# CSV Upload Timeout Issue - FIXED

## Problem

User was getting "Upload timeout - file processing took too long" when uploading CSV files. Investigation revealed the file had **1,643 documents** taking **30-50 minutes** to process!

### Root Causes
1. **Very Large File**: CSV file created 1,643 documents (typical is 10-100)
2. **Short Timeout**: Frontend had 2-minute timeout, way too short for large files
3. **Token Limit Errors**: Some documents exceeded OpenAI's 8,191 token limit
4. **No Preview**: Users couldn't see file size before uploading
5. **Slow Processing**: Each document takes ~1.5 seconds (embed + store)

## Solutions Implemented

### 1. ✅ CSV Preview with Warnings

**Backend** (`routes_files.py`):
- Enhanced `/files/csv_info` endpoint
- Calculates estimated document count
- Estimates processing time (1.5s per document)
- Returns warnings for large files (>100 docs) and very large files (>500 docs)

**Frontend** (`App.tsx`):
- Added `previewCSV()` function that calls info endpoint before upload
- Shows confirmation dialog with:
  - File name
  - Estimated document count
  - Estimated processing time in minutes
  - Warning message if large/very large
- User must confirm before proceeding with large files

**Example Warning**:
```
⚠️ Very large file! Will create ~1643 documents. 
Processing may take 41.1 minutes. Consider splitting the file.

File: huge_dataset.csv
Estimated Documents: 1643
Estimated Time: 41.1 minutes

Do you want to continue?
```

### 2. ✅ Token Limit Handling

**CSV Processor** (`csv_processor.py`):
- Added constants: `MAX_EMBEDDING_TOKENS = 8000`, `CHARS_PER_TOKEN = 4`
- New method: `truncate_text(text, max_chars)` 
- Applied truncation to ALL document types:
  - Row-based documents
  - Batch documents
  - Summary documents
  - Column documents
- Documents exceeding ~32,000 characters are truncated with message

**Embeddings Service** (`embeddings_service.py`):
- Pre-checks text length before API call
- Estimates tokens (length / 4)
- Auto-truncates if >8000 tokens estimated
- Better error messages for token limit errors
- Graceful handling instead of crashing

### 3. ✅ Dynamic Timeouts

**Frontend** (`App.tsx`):
- Removed fixed 2-minute timeout
- Implemented dynamic timeout based on file size:
  - **PDF files**: 1 minute (60,000 ms)
  - **CSV files**: 2 minutes base + 1 minute per MB
  - **Maximum**: 30 minutes (1,800,000 ms)
- Logs timeout setting in console

**Examples**:
- 0.5 MB CSV → 2.5 minutes timeout
- 2 MB CSV → 4 minutes timeout  
- 10 MB CSV → 12 minutes timeout
- 50 MB CSV → 30 minutes timeout (capped)

### 4. ✅ Better User Feedback

**Upload Area**:
- Info message: "CSV files may take 30-60 seconds to process as they're converted into medical documents"
- Blue info box with icon

**Progress Indicator**:
- Shows "Processing CSV data... X%" during upload
- Updates every 500ms (0-95%)
- Changes to "Uploaded (X documents)" on success

**Error Messages**:
- Specific timeout error: "Upload timeout - file processing took too long"
- Token limit error: "Text exceeds token limit - please split into smaller chunks"

## How It Works Now

### Upload Flow for CSV Files

```
1. User selects CSV file
   ↓
2. Frontend calls /files/csv_info (preview)
   ↓
3. Backend analyzes CSV:
   - Counts rows
   - Detects medical content
   - Estimates document count
   - Calculates processing time
   ↓
4. Frontend shows confirmation dialog if large
   ↓
5. User confirms or cancels
   ↓
6. Upload starts with dynamic timeout
   ↓
7. Backend processes CSV:
   - Validates and reads file
   - Anonymizes PHI
   - Creates documents with truncation
   - Generates embeddings (with token check)
   - Stores in Pinecone
   ↓
8. Frontend shows success with document count
```

### Processing Times

| CSV Size | Documents | Time Estimate | Timeout |
|----------|-----------|---------------|---------|
| Small (<100 rows) | 10-50 | 15-75 sec | 2.5 min |
| Medium (100-500) | 50-250 | 1-6 min | 4-8 min |
| Large (500-1000) | 250-500 | 6-12 min | 10-15 min |
| Very Large (>1000) | 500+ | 12+ min | 15-30 min |

## Testing

### Test with Sample Files

```bash
cd backend/sample_documents

# Small file (15 conditions → 16 documents)
# Should take ~30 seconds
curl -X POST -F "file=@medical_conditions.csv" http://localhost:8000/files/add_file

# Preview first
curl -X POST -F "file=@medical_conditions.csv" http://localhost:8000/files/csv_info
```

### Expected Results

**Small CSV** (`medical_conditions.csv`):
- ✅ No warning (15 rows)
- ✅ Uploads directly
- ✅ ~30 seconds processing
- ✅ 16 documents created

**Large CSV** (1000+ rows):
- ⚠️ Warning dialog shown
- ⚠️ Estimates 20+ minutes
- ✅ User can confirm or cancel
- ✅ Progress indicator updates
- ✅ Extended timeout applied

## Recommendations for Users

### For Small to Medium CSVs (<500 rows)
✅ Upload directly - will process in a few minutes

### For Large CSVs (500-1000 rows)
⚠️ Expect 10-15 minute wait
- Preview will warn you
- Consider splitting if >1000 rows

### For Very Large CSVs (>1000 rows)
❌ **Split into smaller files** recommended
- Processing takes 20-50+ minutes
- Risk of timeouts or errors
- Better to upload 2-3 smaller files

### How to Split Large CSV Files

**Option 1: Using Python**
```python
import pandas as pd

# Read large CSV
df = pd.read_csv('large_file.csv')

# Split into chunks of 500 rows
chunk_size = 500
for i, chunk_start in enumerate(range(0, len(df), chunk_size)):
    chunk = df[chunk_start:chunk_start + chunk_size]
    chunk.to_csv(f'large_file_part{i+1}.csv', index=False)
```

**Option 2: Using Excel**
1. Open CSV in Excel
2. Select first 500 rows
3. Copy to new workbook
4. Save as CSV
5. Repeat for remaining rows

## What's Still Needed?

### Possible Future Improvements

1. **Async Background Processing** 
   - Process uploads in background job queue
   - Return immediately with job ID
   - Poll for status updates
   - Would allow unlimited processing time

2. **Batch Embedding Generation**
   - Send multiple texts to OpenAI at once
   - Could speed up by 2-3x
   - Need to handle batch token limits

3. **Progress Websockets**
   - Real-time progress updates from backend
   - Show "Processing document 220 of 1643"
   - Better user experience

4. **Resume Failed Uploads**
   - Save progress in database
   - Allow retry from last successful document
   - Handle partial failures better

## Files Modified

### Backend
- `backend/api/routes_files.py` - Enhanced CSV info endpoint
- `backend/services/csv_processor.py` - Added token limit truncation
- `backend/services/embeddings_service.py` - Better error handling

### Frontend  
- `frontend/src/App.tsx` - Preview, dynamic timeouts, better UI
- `frontend/src/index.css` - Info message styles

### Documentation
- `CSV_UPLOAD_GUIDE.md` - Original guide
- `CSV_TIMEOUT_FIX.md` - This file

## Summary

✅ **FIXED**: Token limit errors with automatic truncation
✅ **FIXED**: Timeout errors with dynamic timeouts (up to 30 min)
✅ **ADDED**: CSV preview with file size warnings
✅ **IMPROVED**: User feedback and progress indicators
✅ **RECOMMENDED**: Split files >1000 rows for best experience

Your CSV uploads should now work reliably for small to medium files, with clear warnings for large files! 🎉

