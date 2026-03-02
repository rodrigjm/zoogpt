# Chat Streaming Endpoint Tests

## Overview

The POST /chat/stream endpoint implements Server-Sent Events (SSE) for streaming chat responses.

## Test Coverage

### Unit Tests (Always Run)
- `test_stream_session_not_found` - Validates 404 error for non-existent sessions
- `test_stream_empty_message` - Validates 422 error for empty messages

### Integration Tests (Require OpenAI + LanceDB)
These tests are marked with `@pytest.mark.skip` and require:
1. Valid `OPENAI_API_KEY` environment variable
2. Populated LanceDB at `data/zoo_lancedb/`

To run integration tests:
```bash
# Set OPENAI_API_KEY in .env file or export it
export OPENAI_API_KEY="sk-..."

# Run with the skip override
pytest tests/test_chat_endpoints.py::TestChatStreamEndpoint -v -k "stream" --ignore-skip
```

## Manual Testing

Use the verification script for manual testing:
```bash
# Start the API server (if not running)
uvicorn app.main:app --reload

# Run verification script
./verify_chat_stream.sh
```

## SSE Event Format

The endpoint emits these event types:

### Text Chunk
```json
data: {"type": "text", "content": "chunk text", "followup_questions": null, "sources": null}
```

### Done Event
```json
data: {"type": "done", "content": null, "followup_questions": ["Q1?", "Q2?"], "sources": [{"animal": "Lemur", "title": "Diet"}]}
```

### Error Event
```json
data: {"type": "error", "content": "error message", "followup_questions": null, "sources": null}
```

## Implementation Details

### Files Modified
- `/apps/api/app/services/rag.py` - Added `generate_response_stream()` method
- `/apps/api/app/routers/chat.py` - Added POST /chat/stream endpoint
- `/apps/api/app/config.py` - Added path resolution for LanceDB
- `/apps/api/tests/test_chat_endpoints.py` - Added streaming tests

### Key Features
1. **Session Validation**: Returns 404 JSON (not SSE) if session not found
2. **Context Search**: Performed before streaming starts
3. **Text Streaming**: Yields text chunks as they arrive from OpenAI
4. **Follow-up Extraction**: Parses follow-up questions from complete response
5. **Error Handling**: Sends error event if exception occurs

## Dependencies

- `sse-starlette>=1.6.0` - SSE support (already in requirements.txt)
- OpenAI API - For LLM streaming
- LanceDB - For vector search
