# CSV Upload Fix - Quick Guide

## What Was Fixed

The CSV file upload functionality was working on the backend but had frontend timeout and user experience issues. The following improvements were made:

### 1. **Extended Timeout for CSV Files**
- CSV files now have a 2-minute timeout (vs 1 minute for PDFs)
- CSV processing takes 30-60 seconds due to data transformation

### 2. **Progress Indicator**
- Added visual progress bar for CSV uploads (0-95% during processing)
- Shows "Processing CSV data... X%" message
- Updates every 500ms to show activity

### 3. **Better Error Handling**
- Specific timeout error messages
- Clear distinction between upload and processing failures
- Proper cleanup of progress intervals

### 4. **User Feedback**
- Info message in upload area explaining CSV processing time
- Status text changes from "Uploading..." to "Processing CSV data..."
- Shows number of documents created (not just chunks)

### 5. **Theme Support**
- Added CSS variables for info messages (--info-bg, --info-text)
- Works in both light and dark themes

## How CSV Processing Works

1. **File Upload** → CSV file sent to backend
2. **Validation** → Checks file format and encoding
3. **Medical Detection** → Analyzes columns and content for medical terms
4. **Anonymization** → Removes PHI (Personal Health Information)
5. **Document Creation** → Converts rows/batches into searchable documents
6. **Embedding Generation** → Creates vector embeddings (1 document at a time)
7. **Vector Storage** → Stores in Pinecone for RAG queries

## Testing CSV Upload

### Test Files Available
- `backend/sample_documents/medical_conditions.csv` (2.6KB, 15 conditions)
- `backend/sample_documents/lab_results.csv` (1.5KB, lab data)

### Test Steps

1. **Open the application**: http://localhost:5173
2. **Navigate to Upload tab**
3. **Upload a CSV file** (drag & drop or click to select)
4. **Wait for processing** (~30-60 seconds)
   - Watch progress indicator (0-95%)
   - Status shows "Processing CSV data... X%"
5. **Verify success**
   - Status changes to "Uploaded (X documents)"
   - Green checkmark appears

### Expected Results

For `medical_conditions.csv`:
- **16 documents** created
- **4,645 characters** of medical content
- Processing time: ~30 seconds

For `lab_results.csv`:
- Similar document count based on rows
- Medical content detected automatically

## Command Line Test

Test backend directly:
```bash
cd /Users/MuhammadUsman/Documents/GitHub/Agentic_RAG_System/backend/sample_documents
curl -X POST -F "file=@medical_conditions.csv" http://localhost:8000/files/add_file
```

Expected response:
```json
{
  "file_id": "uuid-here",
  "message": "Successfully processed CSV file with 16 documents",
  "total_chunks": 16,
  "text_length": 4645
}
```

## Querying CSV Data

After upload, you can query the medical data:

### Example Questions:
- "What are the symptoms of hypertension?"
- "What medications are used for Type 2 Diabetes?"
- "What is the treatment for pneumonia?"
- "What are the risk factors for atrial fibrillation?"

The RAG system will retrieve relevant information from the uploaded CSV data.

## Troubleshooting

### Issue: "Upload timeout - file processing took too long"
- **Cause**: File is very large or backend is slow
- **Solution**: Check backend logs, increase timeout if needed
- **Workaround**: Split CSV into smaller files

### Issue: CSV file not recognized
- **Cause**: File extension or format issue
- **Solution**: Ensure file has `.csv` extension and proper format
- **Check**: File should be comma-separated with header row

### Issue: No medical content detected
- **Note**: Non-medical CSVs are still processed but organized differently
- **Expected**: General data documents instead of medical records

### Issue: Progress stuck at 0%
- **Cause**: Backend not responding or network issue
- **Check**: Backend logs at `/backend` directory
- **Verify**: http://localhost:8000/health should return "healthy"

## Backend Logs

Monitor backend processing:
```bash
# Logs show CSV processing steps
tail -f /path/to/backend/logs
```

Look for:
- "Successfully read CSV with X encoding"
- "Medical content detection: ..."
- "Created X documents from CSV file"
- "Processing document X of Y"

## Architecture

```
Frontend (React)
    ↓ [CSV File]
Backend API (FastAPI)
    ↓ [validate & parse]
CSV Processor Service
    ↓ [detect medical content]
    ↓ [anonymize PHI]
    ↓ [create documents]
Embeddings Service (OpenAI)
    ↓ [generate vectors]
Vector DB Service (Pinecone)
    ↓ [store for retrieval]
RAG System
    ↓ [ready for queries]
```

## Server Status

✅ **Backend**: http://localhost:8000
✅ **Frontend**: http://localhost:5173
✅ **API Docs**: http://localhost:8000/docs

## Next Steps

1. Upload sample CSV files
2. Test querying the medical data
3. Try uploading your own medical CSV files
4. Monitor processing times and adjust timeouts if needed

---

**Note**: CSV files are automatically anonymized to remove potential PHI (names, IDs, etc.) before processing.

