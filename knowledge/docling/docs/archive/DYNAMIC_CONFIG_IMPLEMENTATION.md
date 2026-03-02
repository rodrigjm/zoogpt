# Dynamic Config Implementation - Workstream 3

## Overview

Implemented hot-reload configuration system that enables the admin portal to dynamically update Zoocari's behavior without restarting the API service.

## Implementation Summary

### Files Created

1. `/data/admin_config.json` - Default configuration file
   - Contains system prompt, model settings, and TTS configuration
   - Shared between admin-api (writes) and main-api (reads)
   - Pre-populated with current hardcoded values from codebase

2. `/apps/api/tests/test_dynamic_config.py` - Test suite
   - Tests default loading, file loading, hot-reload, invalid JSON handling
   - 5 tests, all passing

3. `/verify_dynamic_config.py` - Verification script
   - Simple CLI tool to verify config loading and view current values
   - Useful for debugging and verification

### Files Modified

1. `/apps/api/app/config.py`
   - Added `DynamicConfig` class with file-watching capability
   - Uses mtime polling (checks every 5 seconds by default)
   - Thread-safe config access with RLock
   - Graceful fallback to defaults if file missing or invalid
   - Path resolution searches up from module location to find project root
   - Exported `dynamic_config` global instance

2. `/apps/api/app/services/rag.py`
   - Removed hardcoded `ZUCARI_SYSTEM_PROMPT` constant
   - Updated `generate_response()` to use `dynamic_config.system_prompt`
   - Updated `generate_response_stream()` to use `dynamic_config.system_prompt`
   - Both methods now use `dynamic_config.model_name`, `.model_temperature`, `.model_max_tokens`
   - Import changed: `from ..config import settings, dynamic_config`

3. `/apps/api/app/services/tts.py`
   - Removed hardcoded `DEFAULT_VOICE` constant
   - All references updated to use `dynamic_config.tts_default_voice`
   - Import changed: `from ..config import dynamic_config`

## Technical Details

### DynamicConfig Class Features

- **Polling-based reload**: Checks file mtime every N seconds (default 5s)
- **Thread-safe**: Uses RLock for concurrent access
- **Graceful degradation**: Falls back to defaults if file missing/invalid
- **Smart path resolution**: Searches up directory tree to find config file
- **Lazy loading**: Only checks file when config values are accessed
- **No dependencies**: Uses stdlib only (json, threading, pathlib)

### Configuration Structure

```json
{
  "version": "1.0",
  "prompts": {
    "system_prompt": "...",
    "fallback_response": "...",
    "followup_questions": [...]
  },
  "model": {
    "name": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 500
  },
  "tts": {
    "provider": "kokoro",
    "default_voice": "af_heart",
    "speed": 1.0,
    "fallback_provider": "openai",
    "available_voices": {...}
  }
}
```

### Hot-Reload Behavior

1. Admin updates config via admin-api (writes to `admin_config.json`)
2. File mtime changes
3. Within 5 seconds, main-api's next request triggers reload check
4. Config is reloaded atomically
5. New values immediately used for subsequent requests
6. Log message printed: `[DynamicConfig] Reloaded config from ... at ...`

## Verification

### Run Tests
```bash
cd apps/api
python -m pytest tests/test_dynamic_config.py -v
```

### Verify Config Loading
```bash
python verify_dynamic_config.py
```

### Manual Hot-Reload Test
```bash
# Terminal 1: Watch logs
cd apps/api
uvicorn app.main:app --reload

# Terminal 2: Edit config
vim data/admin_config.json
# Change model.name to "gpt-4o"
# Save file

# Terminal 3: Make request
curl http://localhost:8000/chat -X POST -H "Content-Type: application/json" -d '{"message": "Hello"}'

# Check Terminal 1 logs for:
# [DynamicConfig] Reloaded config from ...
# [RAG] OpenAI API call starting (gpt-4o)
```

### Check Current Values
```python
from apps.api.app.config import dynamic_config

print(f"Model: {dynamic_config.model_name}")
print(f"Temperature: {dynamic_config.model_temperature}")
print(f"TTS Voice: {dynamic_config.tts_default_voice}")
print(f"System Prompt Length: {len(dynamic_config.system_prompt)}")
```

## Integration Points

### Admin API
- Reads/writes `data/admin_config.json` via `/config` endpoints
- Uses same path resolution as main API
- Should call save after any config update

### Main API
- Imports `dynamic_config` from `app.config`
- Accesses config via properties (e.g., `dynamic_config.model_name`)
- No manual reload needed - happens automatically on access

### Docker Considerations
- Config path: `/app/data/admin_config.json` in container
- Volume mount: `-v $(pwd)/data:/app/data`
- Both admin and main containers share same volume

## Testing Strategy

1. **Unit tests**: Test DynamicConfig class in isolation
2. **Integration tests**: Test services use correct config values
3. **Manual tests**: Verify hot-reload works end-to-end

## Performance

- Minimal overhead: mtime check only every 5 seconds
- No file watching libraries needed
- Thread-safe for concurrent requests
- Config cached between checks

## Error Handling

1. **File missing**: Uses default config, no error
2. **Invalid JSON**: Logs error, keeps previous valid config
3. **Missing keys**: Falls back to default values for that key
4. **Concurrent access**: Thread-safe with RLock

## Future Enhancements

Potential improvements if needed:
1. Add config validation schema
2. Support environment-based overrides
3. Add reload endpoint to force immediate reload
4. Emit events when config changes
5. Add config version checking/migration

## Status

- Implementation: Complete
- Tests: 5/5 passing
- Documentation: Complete
- Verification: Confirmed working
