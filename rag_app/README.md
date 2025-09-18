# Agentic RAG System

A Retrieval-Augmented Generation (RAG) system built with LangGraph, Pinecone, and OpenAI. This system supports PDF document processing and provides intelligent question-answering capabilities through a FastAPI service.

## Features

- **PDF Document Processing**: Extract text from PDF files and create embeddings
- **Vector Search**: Use Pinecone for efficient similarity search
- **Intelligent Responses**: Generate answers using OpenAI's GPT models
- **LangGraph Orchestration**: Manage the RAG pipeline with LangGraph
- **RESTful API**: Complete FastAPI service with all CRUD operations
- **Error Handling**: Comprehensive error handling and logging

## Architecture

```
rag_app/
├── main.py                     # FastAPI entrypoint
├── api/                        # API routes
│   ├── routes_chat.py         # /chat endpoint
│   └── routes_files.py        # add, delete, update file endpoints
├── core/                      # Core configurations
│   └── config.py              # Environment variables
├── services/                  # Business logic
│   ├── data_injestion_service.py  # PDF text extraction and chunking
│   ├── embeddings_service.py      # OpenAI embeddings
│   ├── vectordb_service.py        # Pinecone operations
│   ├── llm_service.py            # OpenAI LLM
│   └── rag_service.py            # Main RAG orchestration
├── utils/                     # Utility functions
│   └── logger.py              # Centralized logging
├── requirements.txt           # Dependencies
├── env.example               # Environment variables template
└── README.md                 # This file
```

## Prerequisites

- Python 3.8+
- OpenAI API key
- Pinecone account and API key

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Agentic_RAG_System/rag_app
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` file with your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_ENVIRONMENT=your_pinecone_environment_here
   ```

## Configuration

The system uses the following environment variables:

### Required Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_ENVIRONMENT`: Your Pinecone environment

### Optional Variables
- `OPENAI_MODEL`: OpenAI model (default: gpt-3.5-turbo)
- `OPENAI_EMBEDDING_MODEL`: Embedding model (default: text-embedding-ada-002)
- `PINECONE_INDEX_NAME`: Pinecone index name (default: rag-documents)
- `CHUNK_SIZE`: Text chunk size (default: 1000)
- `CHUNK_OVERLAP`: Chunk overlap (default: 200)
- `MAX_RETRIEVAL_RESULTS`: Max results for retrieval (default: 5)
- `API_HOST`: API host (default: 0.0.0.0)
- `API_PORT`: API port (default: 8000)
- `DEBUG`: Debug mode (default: False)

## Running the Application

1. **Start the FastAPI server**:
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access the API**:
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

## API Endpoints

### Chat Endpoints

#### POST /chat/
Process a chat query and get an AI-generated response.

**Request**:
```json
{
  "query": "What does the document say about machine learning?"
}
```

**Response**:
```json
{
  "answer": "Based on the document, machine learning is...",
  "query": "What does the document say about machine learning?",
  "context_count": 3,
  "context_documents": [...]
}
```

#### GET /chat/health
Check the health status of the chat service.

### File Management Endpoints

#### POST /files/add_file
Upload a PDF file and add it to the system.

**Request**: Multipart form data with PDF file

**Response**:
```json
{
  "file_id": "uuid-string",
  "message": "Document successfully added to the system",
  "total_chunks": 15,
  "text_length": 5000
}
```

#### DELETE /files/delete_file/{file_id}
Delete a document from the system.

**Response**:
```json
{
  "file_id": "uuid-string",
  "message": "Document successfully deleted from the system"
}
```

#### PUT /files/update_file/{file_id}
Update an existing document with a new PDF file.

**Request**: Multipart form data with new PDF file

**Response**:
```json
{
  "file_id": "uuid-string",
  "message": "Document successfully updated in the system",
  "total_chunks": 12,
  "text_length": 4500
}
```

#### GET /files/health
Check the health status of the file service.

### System Endpoints

#### GET /
Get basic API information.

#### GET /health
Get overall system health status.

## Example Usage

### Using curl

1. **Add a document**:
   ```bash
   curl -X POST "http://localhost:8000/files/add_file" \
        -H "accept: application/json" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@document.pdf"
   ```

2. **Ask a question**:
   ```bash
   curl -X POST "http://localhost:8000/chat/" \
        -H "accept: application/json" \
        -H "Content-Type: application/json" \
        -d '{"query": "What is the main topic of the document?"}'
   ```

3. **Delete a document**:
   ```bash
   curl -X DELETE "http://localhost:8000/files/delete_file/uuid-string"
   ```

### Using Python requests

```python
import requests

# Add a document
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/files/add_file',
        files={'file': f}
    )
    file_data = response.json()
    file_id = file_data['file_id']

# Ask a question
response = requests.post(
    'http://localhost:8000/chat/',
    json={'query': 'What is this document about?'}
)
answer = response.json()['answer']

# Delete the document
requests.delete(f'http://localhost:8000/files/delete_file/{file_id}')
```

## Development

### Code Structure

The codebase follows a clean architecture pattern:

- **API Layer**: FastAPI routes and request/response models
- **Service Layer**: Business logic and orchestration
- **Core Layer**: Configuration and settings
- **Utils Layer**: Shared utilities and logging

### Adding New Features

1. **New API endpoints**: Add routes in the `api/` directory
2. **New services**: Add service classes in the `services/` directory
3. **New configurations**: Add settings in `core/config.py`
4. **New utilities**: Add utility functions in `utils/` directory

### Testing

Run the application and test the endpoints using the interactive docs at http://localhost:8000/docs.

## Troubleshooting

### Common Issues

1. **Missing API keys**: Ensure all required environment variables are set
2. **Pinecone connection issues**: Check your Pinecone API key and environment
3. **OpenAI API errors**: Verify your OpenAI API key and account status
4. **PDF processing errors**: Ensure the PDF file is valid and not corrupted

### Logs

The application uses structured logging. Check the console output for detailed error messages and debugging information.

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions, please create an issue in the repository or contact the development team.
