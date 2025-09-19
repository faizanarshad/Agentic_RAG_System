# 🧪 RAG System Testing Guide

## 📚 Test Datasets Available

### 1. **Sample Documents (Ready to Use)**
I've created sample PDF documents for testing:

- **`rag_app/sample_documents/ai_ml_basics.pdf`** - Comprehensive guide on AI and Machine Learning
- **`rag_app/sample_documents/rag_systems.pdf`** - Detailed information about RAG systems

### 2. **How to Test Your RAG System**

#### Step 1: Start Your System
```bash
# Terminal 1 - Backend
cd rag_app
source venv/bin/activate
python main.py

# Terminal 2 - Frontend  
cd rag-frontend
npm run dev
```

#### Step 2: Upload Test Documents
1. Open http://localhost:5173
2. Go to "Upload" tab
3. Upload the sample PDFs from `rag_app/sample_documents/`
4. Wait for processing to complete

#### Step 3: Test with Questions
Go to "Chat" tab and try these questions:

**About AI/ML:**
- "What is machine learning?"
- "Explain the difference between supervised and unsupervised learning"
- "What are the applications of deep learning?"
- "What are the challenges in AI development?"

**About RAG Systems:**
- "How does RAG work?"
- "What are the benefits of RAG systems?"
- "Explain the components of a RAG system"
- "What are the challenges in RAG systems?"

## 🌐 Where to Get More Test Datasets

### 1. **Academic Sources**
- **ArXiv** (https://arxiv.org/): Research papers in various fields
- **PubMed** (https://pubmed.ncbi.nlm.nih.gov/): Medical research papers
- **Google Scholar** (https://scholar.google.com/): Academic publications
- **ResearchGate** (https://www.researchgate.net/): Scientific papers

### 2. **Documentation & Manuals**
- **Software Documentation**: API docs, user manuals
- **Technical Guides**: Programming tutorials, system documentation
- **Company Reports**: Annual reports, whitepapers
- **Government Documents**: Policy papers, regulations

### 3. **News & Articles**
- **News Websites**: Download articles as PDFs
- **Blog Posts**: Convert to PDF format
- **Magazine Articles**: Industry publications
- **Wikipedia**: Export articles as PDFs

### 4. **Domain-Specific Datasets**

#### Healthcare:
- Medical research papers
- Clinical guidelines
- Drug information sheets
- Patient education materials

#### Legal:
- Case law documents
- Legal statutes
- Court decisions
- Legal briefs

#### Business:
- Financial reports
- Market research
- Business plans
- Industry analysis

#### Technology:
- Technical documentation
- API references
- Code documentation
- System manuals

## 🔧 Creating Your Own Test Documents

### Method 1: Text to PDF Conversion
```bash
cd rag_app
python create_test_pdfs.py
```

### Method 2: Manual PDF Creation
1. Create text files with your content
2. Use online converters or tools like:
   - **Pandoc**: `pandoc input.txt -o output.pdf`
   - **LibreOffice**: Open text file and export as PDF
   - **Google Docs**: Upload text and download as PDF

### Method 3: Web Scraping
```python
# Example: Convert web pages to PDF
import requests
from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas

def web_to_pdf(url, output_file):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text()
    # Convert to PDF using reportlab
```

## 📊 Testing Scenarios

### 1. **Basic Functionality Tests**
- Upload single PDF document
- Ask simple questions
- Verify responses are relevant
- Check source citations

### 2. **Complex Query Tests**
- Multi-part questions
- Questions requiring multiple sources
- Questions with context
- Follow-up questions

### 3. **Edge Case Tests**
- Questions with no relevant information
- Very specific technical questions
- Questions about recent events
- Ambiguous questions

### 4. **Performance Tests**
- Large document uploads
- Multiple concurrent queries
- Long conversation threads
- System stress testing

## 🎯 Sample Test Questions by Domain

### AI/ML Domain:
- "What is the difference between machine learning and deep learning?"
- "Explain how neural networks work"
- "What are the ethical considerations in AI?"
- "How do recommendation systems work?"

### RAG Systems Domain:
- "What are the advantages of RAG over fine-tuning?"
- "How do you improve retrieval quality in RAG systems?"
- "What is the role of embeddings in RAG?"
- "How do you handle context length limitations?"

### General Knowledge:
- "Summarize the main points of this document"
- "What are the key challenges mentioned?"
- "List the applications discussed"
- "What are the future prospects?"

## 🔍 Evaluating RAG Performance

### 1. **Relevance Metrics**
- Are retrieved documents relevant to the question?
- Is the answer based on the retrieved information?
- Are sources properly cited?

### 2. **Accuracy Metrics**
- Is the information factually correct?
- Are there any hallucinations?
- Is the answer complete?

### 3. **Quality Metrics**
- Is the response well-structured?
- Is the language clear and coherent?
- Does it answer the specific question asked?

## 🚀 Advanced Testing

### 1. **Multi-Document Testing**
- Upload multiple related documents
- Ask questions requiring information from multiple sources
- Test cross-document reasoning

### 2. **Temporal Testing**
- Upload documents with different dates
- Ask time-sensitive questions
- Test handling of outdated information

### 3. **Language Testing**
- Test with different question phrasings
- Try questions in different languages
- Test with technical jargon

## 📝 Test Results Documentation

Keep track of:
- Questions asked
- Responses received
- Source citations
- Response quality (1-5 scale)
- Any issues encountered
- System performance metrics

## 🎉 Ready to Test!

Your RAG system is now ready for comprehensive testing. Start with the sample documents and gradually expand to more complex datasets. The system will learn and improve as you add more documents and test different types of queries.

**Happy Testing! 🚀**
