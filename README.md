# AetherExtract

Unleash the knowledge from your documents with AetherExtract -- an intelligent chatbot powered by Google Gemini and advanced Retrieval Augmented Generation (RAG).

![AetherExtract UI Preview](assets/AetherExtract_UI_Preview.png)

## Key Features

- **Multi-Document Support**: Upload and query PDF (.pdf), Word (.docx, .doc), and Text (.txt) files.
- **Intelligent Q&A**: Get accurate, contextual answers directly from your uploaded documents.
- **Gemini-Powered**: Leverages Google's powerful Gemini 2.0 Flash model for natural language understanding and generation.
- **Retrieval-Augmented Generation (RAG)**: Efficiently retrieves relevant information from your documents using FAISS vector store.
- **Dynamic Response Length**: Ask general questions for concise answers (3-5 sentences) or explicitly request "details" for comprehensive explanations.
- **Source Transparency**: Always shows the top relevant source paragraph for transparency.
- **Aurora-Themed UI**: A sleek, dark, and aesthetically pleasing interface inspired by the night sky.
- **Reset Functionality**: Easily clear the current document and chat history to start fresh.

## Tech Stack

### Backend
- **FastAPI**: High-performance web framework for the API.
- **LangChain**: Framework for building LLM applications (integrates Gemini, FAISS, and text processing).
- **Google Gemini API**: Large Language Model (LLM) for answering questions and generating embeddings.
- **FAISS**: (Facebook AI Similarity Search) For efficient similarity search in vector stores.
- **pypdf**: For text extraction from PDF files.
- **python-docx**: For text extraction from .docx (Word) files.
- **docx2txt**: For text extraction from older .doc (Word) files.
- **python-dotenv**: For secure management of API keys.
- **Uvicorn**: ASGI server to run the FastAPI application.

### Frontend
- **HTML5**: Structure of the web interface.
- **CSS3**: Styling for the unique aurora theme and responsive layout.
- **JavaScript (ES6+)**: Handles user interaction, API calls to the backend, and dynamic content updates.

## Setup Instructions

Follow these steps to get your AetherExtract chatbot up and running on your local machine.

### 1. Prerequisites
- **Python 3.8+**: Make sure you have a compatible Python version installed.
- **Google Gemini API Key**: Obtain an API key from Google AI Studio or your Google Cloud Console.
- **Antiword (for .doc files)**: If you plan to process .doc files, you might need to install antiword on your system.
  - On Debian/Ubuntu: `sudo apt-get install antiword`
  - On macOS (with Homebrew): `brew install antiword`
  - On Windows: Download and install `antiword.exe` and add it to your system's PATH.

### 2. Clone the Repository
```bash
git clone YOUR_GITHUB_REPO_URL_HERE
cd mini_rag_chatbot
```


### 3. Create and Activate Virtual Environment
```bash
python -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```
### 5. Set up your Gemini API Key
Create a .env file in the root directory:

```env
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY_HERE
```
Ensure there are no spaces around the = sign.
 
## ▶️ How to Run
### 1. Start the Backend Server

```bash
uvicorn app.main:app --reload
```
Leave this terminal open; the server will keep running.

2. Open the Frontend in Your Browser
Go to:

```cpp

http://127.0.0.1:8000/
```
You should now see the AetherExtract chatbot interface.



