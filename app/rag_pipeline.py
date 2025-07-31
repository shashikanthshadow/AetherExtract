# app/rag_pipeline.py
import os
from typing import List, Tuple
from pypdf import PdfReader # For PDF text extraction
from docx import Document # NEW: For DOCX text extraction
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

load_dotenv()

class RAGPipeline:
    def __init__(self):
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set. "
                "Please set it in your .env file in the project root "
                "(e.g., GOOGLE_API_KEY='YOUR_KEY_HERE') or as a system environment variable."
            )

        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=google_api_key)
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7, google_api_key=google_api_key)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        self.vector_store = None

    def reset_knowledge_base(self):
        self.vector_store = None
        print("RAGPipeline: Knowledge base fully reset, ready for a new document.")

    # MODIFIED: Renamed and added file_type parameter for multi-document support
    def get_document_text(self, file_path: str, file_type: str) -> str:
        """
        Extracts text from various document types based on file_type.
        Supports: PDF (.pdf), DOCX (.docx), Text (.txt)
        """
        text = ""
        try:
            if file_type == "pdf":
                pdf_reader = PdfReader(file_path)
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            elif file_type == "docx":
                doc = Document(file_path)
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
            elif file_type == "txt":
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            print(f"Error reading document {file_path} ({file_type}): {e}")
            raise ValueError(f"Failed to extract text from document: {e}")
        return text

    def get_text_chunks(self, text: str) -> List[str]:
        chunks = self.text_splitter.split_text(text)
        return chunks

    def create_vector_store(self, text_chunks: List[str]):
        if not text_chunks:
            print("No text chunks provided for vector store creation. Cannot create vector store.")
            self.vector_store = None
            return

        print(f"Creating a NEW FAISS vector store from {len(text_chunks)} chunks...")
        try:
            self.vector_store = FAISS.from_texts(text_chunks, embedding=self.embeddings)
            print("FAISS vector store created successfully.")
        except Exception as e:
            print(f"Error creating FAISS vector store: {e}")
            self.vector_store = None
            raise ValueError(f"Failed to create vector store: {e}. Check Gemini API key or document content.")

    def get_conversational_chain(self) -> RetrievalQA:
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Please upload and process a document first.")

        prompt_template = """
        You are a highly intelligent and helpful assistant designed to provide accurate, concise, and comprehensive answers based SOLELY on the provided document context.

        **Answer Generation Guidelines:**
        1.  **Concise Default (3-5 Sentences):** For general questions, provide a concise answer, typically within 3 to 5 sentences.
        2.  **Detailed Response:** If the user explicitly asks for 'details', 'more information', 'a comprehensive explanation', 'a full summary', or similar phrases, provide a thorough and elaborate answer, using all relevant information from the context.
        3.  **Accuracy & Grounding:** Carefully analyze ALL relevant information to synthesize a coherent and accurate response. Do not make up information or refer to external knowledge.
        4.  **No Answer:** If the context does not contain sufficient information to answer the question, clearly and politely state: "I cannot find the answer to that question in the provided document." Do not make up an answer.

        Context:
        {context}

        Question:
        {question}

        Answer:
        """
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

        retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})

        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
        return chain

    def query_rag_pipeline(self, question: str) -> Tuple[str, List[str]]:
        try:
            chain = self.get_conversational_chain()
            response = chain.invoke({"query": question})
            
            answer = response["result"]
            
            source_documents = response["source_documents"]
            sources = []
            for doc in source_documents:
                sources.append(doc.page_content.replace('\n', ' ').strip())

            return answer, sources
        except ValueError as e:
            return str(e), []
        except Exception as e:
            print(f"An unexpected error occurred during query_rag_pipeline: {e}")
            return f"An internal error occurred: {e}", []

# Example Usage (for direct testing of this file)
if __name__ == "__main__":
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        dummy_pdf_path = "dummy_test_document.pdf"
        c = canvas.Canvas(dummy_pdf_path, pagesize=letter)
        textobject = c.beginText()
        textobject.setTextOrigin(100, 750)
        textobject.setFont("Helvetica", 12)
        dummy_content = """
        This is the first paragraph about artificial intelligence. AI is transforming industries worldwide.
        The second paragraph discusses machine learning, a key component of modern AI systems. Machine learning enables systems to learn from data without explicit programming.
        The third paragraph talks about natural language processing (NLP). NLP is a field of AI that focuses on enabling computers to understand, interpret, and generate human language.
        Finally, a paragraph about the importance of ethical AI development. Ensuring fairness and transparency in AI is crucial.
        """
        for line in dummy_content.split('\n'):
            textobject.textLine(line.strip())
        c.drawText(textobject)
        c.save()
        print(f"Dummy PDF '{dummy_pdf_path}' created for testing.")

        rag_pipeline = RAGPipeline()
        
        print("\nProcessing dummy PDF for RAG...")
        # Now calls get_document_text
        pdf_text = rag_pipeline.get_document_text(dummy_pdf_path, "pdf")
        chunks = rag_pipeline.get_text_chunks(pdf_text)
        rag_pipeline.create_vector_store(chunks)

        if rag_pipeline.vector_store:
            print("\n--- Testing RAG Pipeline Queries ---")
            
            question1 = "What is machine learning?"
            answer1, sources1 = rag_pipeline.query_rag_pipeline(question1)
            print(f"Question: {question1}")
            print(f"Answer: {answer1}")
            print(f"Sources: {sources1}")

            question2 = "What is NLP?"
            answer2, sources2 = rag_pipeline.query_rag_pipeline(question2)
            print(f"Question: {question2}")
            print(f"Answer: {answer2}")
            print(f"Sources: {sources2}")

            question3 = "Tell me about cars." # Out of context question
            answer3, sources3 = rag_pipeline.query_rag_pipeline(question3)
            print(f"Question: {question3}")
            print(f"Answer: {answer3}")
            print(f"Sources: {sources3}")
        else:
            print("RAG pipeline could not be initialized due to vector store creation issues.")
    except ImportError:
        print("\n'reportlab' not installed. Skipping dummy PDF creation. Install it with 'pip install reportlab' to test directly.")
    except Exception as e:
        print(f"\nAn error occurred during direct testing: {e}")
    finally:
        if 'dummy_pdf_path' in locals() and os.path.exists(dummy_pdf_path):
            os.remove(dummy_pdf_path)
            print(f"Cleaned up dummy PDF: {dummy_pdf_path}")