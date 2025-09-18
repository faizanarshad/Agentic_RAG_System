# 🤖 Agentic RAG System

A complete, production-ready Retrieval-Augmented Generation (RAG) system with a modern web interface, built using state-of-the-art technologies.

## ✨ Features

### 🧠 **Core RAG Capabilities**
- **Document Processing**: PDF text extraction and intelligent chunking
- **Vector Search**: Pinecone-powered semantic search
- **AI Responses**: OpenAI GPT-powered contextual answers
- **LangGraph Orchestration**: Advanced workflow management

### 🎨 **Modern Web Interface**
- **React + TypeScript**: Modern, type-safe frontend
- **Real-time Chat**: Interactive conversation interface
- **Drag & Drop Upload**: Easy PDF document management
- **System Monitoring**: Real-time health checks and status
- **Responsive Design**: Works perfectly on all devices

### 🔧 **Backend Architecture**
- **FastAPI**: High-performance Python web framework
- **Pinecone**: Vector database for semantic search
- **OpenAI**: Advanced language models and embeddings
- **LangGraph**: Sophisticated workflow orchestration

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API key
- Pinecone API key

### 1. Clone the Repository
```bash
git clone https://github.com/faizanarshad/Agentic_RAG_System.git
cd Agentic_RAG_System
```

### 2. Backend Setup
```bash
cd rag_app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the `rag_app` directory:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=rag-documents

# Application Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_RETRIEVAL_RESULTS=5
```

### 4. Frontend Setup
```bash
cd rag-frontend
npm install
```

### 5. Run the Application

**Start the Backend:**
```bash
cd rag_app
source venv/bin/activate
python main.py
```

**Start the Frontend:**
```bash
cd rag-frontend
npm run dev
```

### 6. Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📱 Usage

### 1. Upload Documents
- Navigate to the "Upload" tab
- Drag and drop PDF files or click to select
- Monitor upload progress and chunk creation

### 2. Chat with Documents
- Go to the "Chat" tab
- Ask questions about your uploaded documents
- Get contextual answers based on document content

### 3. Monitor System
- Check the "Status" tab for system health
- Monitor vector database and LLM service status
- Refresh status in real-time

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │   FastAPI Backend│    │   External APIs │
│                 │    │                 │    │                 │
│ • Chat Interface│◄──►│ • RAG Service   │◄──►│ • OpenAI API    │
│ • File Upload   │    │ • Vector Search │    │ • Pinecone API  │
│ • Status Monitor│    │ • LangGraph     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development
- **Lucide React** for icons
- **Custom CSS** for styling

### Backend
- **FastAPI** for API framework
- **Python 3.9+** runtime
- **LangGraph** for workflow orchestration
- **Pinecone** for vector database
- **OpenAI** for LLM and embeddings

### Infrastructure
- **Docker** ready for containerization
- **Environment-based** configuration
- **Health monitoring** and logging
- **Error handling** and validation

## 📁 Project Structure

```
Agentic_RAG_System/
├── rag_app/                 # Backend FastAPI application
│   ├── api/                # API routes
│   ├── core/               # Configuration and settings
│   ├── services/           # Business logic services
│   ├── utils/              # Utility functions
│   ├── main.py             # Application entry point
│   └── requirements.txt    # Python dependencies
├── rag-frontend/           # React frontend application
│   ├── src/                # Source code
│   │   ├── components/     # React components
│   │   ├── App.tsx         # Main application
│   │   └── index.css       # Styling
│   ├── package.json        # Node.js dependencies
│   └── vite.config.ts      # Vite configuration
└── README.md               # This file
```

## 🔧 API Endpoints

### Chat
- `POST /chat/` - Send messages to the RAG system

### File Management
- `POST /files/add_file` - Upload PDF documents
- `DELETE /files/delete_file/{file_id}` - Delete documents
- `PUT /files/update_file/{file_id}` - Update documents

### Health
- `GET /health` - System health check
- `GET /files/health` - Component health status

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Manual Deployment
1. Set up environment variables
2. Install dependencies
3. Run backend: `python main.py`
4. Run frontend: `npm run dev`
5. Configure reverse proxy (nginx)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for advanced language models
- Pinecone for vector database services
- LangChain for RAG framework
- FastAPI for the web framework
- React team for the frontend library

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API docs at `/docs`

---

**Built with ❤️ using modern AI technologies**