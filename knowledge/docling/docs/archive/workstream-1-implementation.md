# Workstream 1: Vector Index Rebuilder Implementation

## Summary

Replaced the placeholder `run_index_rebuild()` function in `apps/admin-api/routers/kb.py` with a complete LanceDB indexing implementation.

## Changes Made

### Files Modified

1. **apps/admin-api/routers/kb.py** (lines 504-547)
   - Added import for `IndexerService`
   - Replaced placeholder implementation with actual indexing logic
   - Function now calls `IndexerService.rebuild_index()` and updates job status with real metrics

2. **apps/admin-api/requirements.txt**
   - Added `pytest>=7.4.0` for testing

### Files Created

1. **apps/admin-api/services/indexer.py**
   - Complete `IndexerService` class with the following methods:
     - `get_all_sources()` - Queries kb_sources with animal names from SQLite
     - `chunk_content()` - Simple overlapping chunking (500 chars, 100 char overlap)
     - `prepare_chunks_for_db()` - Prepares chunks with metadata for LanceDB
     - `write_to_lancedb()` - Creates LanceDB table with OpenAI embeddings
     - `update_source_chunk_counts()` - Updates SQLite with chunk counts
     - `rebuild_index()` - Orchestrates the full rebuild process

2. **apps/admin-api/tests/test_indexer.py**
   - Unit tests for all IndexerService methods
   - Tests use mock database and LanceDB connections

3. **apps/admin-api/tests/__init__.py**
   - Test package initialization

## Implementation Details

### LanceDB Integration
- Uses `text-embedding-3-large` model (matching `zoo_build_knowledge.py`)
- Schema matches existing pattern: `text`, `vector`, `metadata` (animal_name, filename, title, url)
- Uses `mode="overwrite"` to handle concurrent access
- Batches embeddings in groups of 50 to avoid rate limits

### Chunking Strategy
- Simple overlapping chunks: 500 characters with 100 character overlap
- This approach works for pre-extracted text content from SQLite
- Does not require `HybridChunker` or `DocumentConverter` dependencies

### Database Updates
- Updates `kb_index_history` table with:
  - `status` (completed/failed)
  - `completed_at` timestamp
  - `total_documents` count
  - `total_chunks` count
  - `error_message` (on failure)
- Updates `kb_sources` table with:
  - `chunk_count` per source
  - `last_indexed` timestamp

## Verification Steps

### 1. Syntax Validation
```bash
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin-api
python3 -m py_compile services/indexer.py
python3 -m py_compile routers/kb.py
```

### 2. Run Unit Tests
```bash
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin-api
pip install -r requirements.txt
pytest tests/test_indexer.py -v
```

### 3. Start Admin API
```bash
cd /Users/jesus/Documents/gits/ai-cookbook/knowledge/docling/apps/admin-api
export OPENAI_API_KEY="your-key-here"
export SESSION_DB_PATH="/path/to/session.db"
export LANCEDB_PATH="/path/to/zoo_lancedb"
uvicorn main:app --reload --port 8000
```

### 4. Test Index Rebuild Endpoint
```bash
# Get auth token
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your-password"

# Trigger index rebuild
curl -X POST "http://localhost:8000/kb/index/rebuild" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check status
curl -X GET "http://localhost:8000/kb/index/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Notes

- The implementation follows the pattern from `zoo_build_knowledge.py` (lines 157-195)
- Error handling is in place with try-catch blocks
- Background task execution prevents API blocking
- Environment variable `LANCEDB_PATH` can override default location
