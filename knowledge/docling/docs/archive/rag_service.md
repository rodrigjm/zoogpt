# RAG Service Documentation

## Overview
The RAG (Retrieval-Augmented Generation) service provides the core intelligence for Zoocari, combining vector search with LLM generation to deliver accurate, grounded responses about animals.

## Architecture

### Components
1. **LanceDB Integration** - Vector database for semantic search over animal facts
2. **OpenAI Integration** - GPT-4o-mini for response generation
3. **Zoocari Persona** - Kid-friendly elephant character system prompt

### File Location
- Implementation: `apps/api/app/services/rag.py`
- Config: `apps/api/app/config.py`
- Integration: `apps/api/app/routers/chat.py`

## LanceDB Schema Assumptions

The service expects a LanceDB table named `animals` with the following structure:

```
- text: str (primary content field for semantic search)
- metadata: dict
  - animal_name: str (e.g., "Lemur", "Camel")
  - title: str (document/section title)
- _distance: float (computed by LanceDB during search)
```

Database location: `data/zoo_lancedb/`

## RAGService API

### Class: `RAGService`

Singleton-style service with lazy-loaded connections.

#### Methods

##### `search_context(query: str, num_results: int = 5) -> tuple[str, list[dict], float]`

Search LanceDB for relevant context.

**Parameters:**
- `query`: User's question
- `num_results`: Number of results to retrieve (default: 5)

**Returns:**
- `context_string`: Formatted context for LLM
- `sources`: List of source dicts `[{"animal": "Lemur", "title": "Diet"}]`
- `confidence`: Float 0-1 (inverse of average distance)

**Example:**
```python
rag = RAGService()
context, sources, confidence = rag.search_context("What do lemurs eat?")
```

##### `generate_response(messages: list[dict], context: str) -> str`

Generate response using OpenAI with Zoocari persona.

**Parameters:**
- `messages`: Chat history in OpenAI format `[{"role": "user", "content": "..."}]`
- `context`: Retrieved context from LanceDB

**Returns:**
- Generated response string (includes follow-up questions)

**Example:**
```python
messages = [{"role": "user", "content": "Tell me about lemurs"}]
reply = rag.generate_response(messages, context)
```

##### `extract_followup_questions(response: str) -> tuple[str, list[str]]`

Extract follow-up questions from Zoocari's response.

**Parameters:**
- `response`: Full response from LLM

**Returns:**
- `main_response`: Response without follow-up section
- `questions`: List of follow-up questions

**Example:**
```python
main, followups = rag.extract_followup_questions(reply)
# main = "Lemurs are primates..."
# followups = ["What do lemurs eat?", "Where do lemurs live?", ...]
```

## Zoocari Persona

### Character Traits
- Warm, playful, encouraging
- Uses simple language for ages 6-12
- No made-up facts (strictly grounded in context)
- Gentle handling of nature realities
- No emojis in responses

### Response Format
1. Enthusiastic greeting related to question
2. Answer based ONLY on retrieved context
3. Exactly 3 follow-up questions in markdown list

### Safety Rules
1. Only answer from provided context
2. If context insufficient: "Hmm, I don't know about that yet! Maybe ask one of the zookeepers..."
3. Never hallucinate or guess
4. Keep answers short (1-2 paragraphs, under 100 words)
5. Age-appropriate language
6. No graphic details

## Integration with Chat Router

The chat router uses RAGService as follows:

```python
# apps/api/app/routers/chat.py

# 1. Search for context
context, sources, confidence = _rag_service.search_context(body.message)

# 2. Build message history
messages = [{"role": "user", "content": body.message}]

# 3. Generate response
reply = _rag_service.generate_response(messages, context)

# 4. Return per CONTRACT.md
return {
    "session_id": body.session_id,
    "message_id": message_id,
    "reply": reply,
    "sources": sources,
    "created_at": now.isoformat(),
}
```

## Configuration

Settings in `apps/api/app/config.py`:

```python
lancedb_path: str = "data/zoo_lancedb"
embedding_model: str = "text-embedding-3-small"  # (not used yet - LanceDB handles embeddings)
openai_api_key: str  # Required
```

## Future Enhancements

### Not Yet Implemented
1. **Streaming responses** - SSE support for POST /chat/stream
2. **Multi-turn conversation** - Session history integration
3. **Confidence thresholds** - Reject low-confidence queries
4. **Custom embeddings** - Use `embedding_model` setting for custom embeddings

### Potential Improvements
1. **Caching** - Cache frequent queries
2. **Hybrid search** - Combine semantic + keyword search
3. **Reranking** - Post-retrieval reranking for better results
4. **Prompt engineering** - A/B test different personas
5. **Telemetry** - Log retrieval quality metrics

## Testing

### Manual Test
```bash
# 1. Start API
cd apps/api
uvicorn app.main:app --reload

# 2. Create session
curl -X POST http://localhost:8000/session \
  -H "Content-Type: application/json" \
  -d '{"client": "web", "metadata": {}}'

# 3. Send chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<session_id>", "message": "Tell me about lemurs"}'
```

Expected response:
- Reply with Zoocari personality
- Sources list with animal names
- ISO-8601 timestamp

### Verification Steps
1. Response stays grounded in context (no hallucinations)
2. Follow-up questions extracted correctly
3. Sources match retrieved context
4. Confidence score between 0-1

## Troubleshooting

### Common Issues

**LanceDB not found**
```
Error: Table 'animals' not found
```
**Solution:** Build LanceDB first using legacy build script:
```bash
python legacy/zoo_build_knowledge.py
```

**OpenAI API key missing**
```
Error: openai_api_key is required
```
**Solution:** Set in `.env`:
```
OPENAI_API_KEY=sk-...
```

**Low-quality responses**
- Check `num_results` parameter (try 3-10)
- Verify LanceDB has relevant content
- Review context string length

## Performance

Expected latency (approximate):
- LanceDB search: 50-200ms
- OpenAI generation: 500-2000ms (varies by length)
- **Total**: ~1-2 seconds per request

Optimization opportunities:
- Use `gpt-3.5-turbo` for faster responses (slight quality drop)
- Reduce `num_results` for faster retrieval
- Implement response caching
