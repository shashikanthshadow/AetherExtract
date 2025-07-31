# app/main.py
import os
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.rag_pipeline import RAGPipeline

# Initialize FastAPI app
app = FastAPI(
    title="Mini RAG Chatbot API",
    description="API for uploading documents and querying them using Google Gemini and FAISS.",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instance of the RAGPipeline.
rag_pipeline = RAGPipeline()
current_doc_filename = None # RENAMED: now tracks the name of the *currently loaded* document

# Serve static files from the 'frontend' directory under the /frontend path.
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


# Root endpoint to serve the index.html file directly.
@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serves the main frontend HTML page from the frontend directory."""
    return os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")

# --- API Endpoints ---

# MODIFIED: Renamed from upload_pdf to upload_document
@app.post("/upload-document/")
async def upload_document(file: UploadFile = File(...)):
    global current_doc_filename # RENAMED
    
    # Explicitly clear the previous knowledge base when a new document is uploaded
    if rag_pipeline.vector_store is not None:
        print(f"New document '{file.filename}' uploaded. Clearing previous knowledge base.")
        rag_pipeline.reset_knowledge_base()
        current_doc_filename = None # Reset the tracker too

    # Get file extension to determine type
    file_extension = file.filename.split(".")[-1].lower()
    
    # Validate supported file types (you can expand this list)
    supported_types = ["pdf", "docx", "txt"]
    if file_extension not in supported_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{file_extension}. Only .pdf, .docx, and .txt are supported.")

    current_doc_filename = file.filename # Set the name of the *new* document being processed

    # Save the uploaded file temporarily
    # Using tempfile ensures proper cleanup
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
        for chunk in iter(lambda: file.file.read(4096), b''):
            tmp_file.write(chunk)
        temp_doc_path = tmp_file.name

    try:
        # MODIFIED: Call get_document_text with file_extension
        doc_text = rag_pipeline.get_document_text(temp_doc_path, file_extension)
        if not doc_text:
            raise HTTPException(status_code=500, detail="Could not extract text from the document. It might be an image-only, encrypted, corrupted, or contain no selectable text.")

        text_chunks = rag_pipeline.get_text_chunks(doc_text)
        if not text_chunks:
            raise HTTPException(status_code=500, detail="No valid text chunks could be generated from the document content. Document might be empty or its content is unparseable after chunking.")

        rag_pipeline.create_vector_store(text_chunks)
        
        if rag_pipeline.vector_store is None:
             raise HTTPException(status_code=500, detail="Failed to initialize the knowledge base. This might be due to Gemini API key issues or content.")

        return JSONResponse(
            content={"message": f"Document '{file.filename}' processed successfully. It has replaced any previous document. Ready to answer questions!"},
            status_code=200
        )
    except ValueError as ve:
        print(f"Processing error (ValueError) for {file.filename}: {ve}")
        if current_doc_filename == file.filename:
            current_doc_filename = None
        raise HTTPException(status_code=500, detail=f"Processing error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred during document processing for {file.filename}: {e}")
        if current_doc_filename == file.filename:
            current_doc_filename = None
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred while processing document: {e}. Please try again.")
    finally:
        if os.path.exists(temp_doc_path):
            os.remove(temp_doc_path)

@app.post("/chat/")
async def chat_with_pdf(request_body: dict):
    """
    Answers a question based on the currently loaded document's knowledge base.
    """
    user_question = request_body.get("query")
    if not user_question:
        raise HTTPException(status_code=400, detail="No query (question) was provided in the request.")

    if rag_pipeline.vector_store is None:
        raise HTTPException(status_code=400, detail="No document has been uploaded and processed yet. Please upload a document first to enable chat functionality.")
    
    current_doc_info = f" from '{current_doc_filename}'" if current_doc_filename else ""
    print(f"Chat query received{current_doc_info}: {user_question}")


    try:
        answer, sources = rag_pipeline.query_rag_pipeline(user_question)
        return JSONResponse(
            content={
                "answer": answer,
                "sources": sources
            },
            status_code=200
        )
    except ValueError as ve:
        print(f"Chat query error (ValueError): {ve}")
        raise HTTPException(status_code=500, detail=f"Chat error: {ve}")
    except Exception as e:
        print(f"An unexpected error occurred during chat query: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred during chat: {e}. Please try again.")

@app.post("/reset-chatbot/")
async def reset_chatbot():
    """
    Resets the chatbot by clearing the loaded document's knowledge base from memory.
    """
    global current_doc_filename # RENAMED
    if rag_pipeline.vector_store is not None:
        rag_pipeline.reset_knowledge_base()
        print("Backend: Chatbot knowledge base has been reset.")
    current_doc_filename = None # Ensure filename tracker is also cleared
    return JSONResponse(
        content={"message": "Chatbot reset successfully. Please upload a new document."},
        status_code=200
    )