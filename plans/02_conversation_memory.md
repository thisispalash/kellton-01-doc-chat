# Conversation Memory Implementation Plan

**Created**: November 14, 2025  
**Status**: Planned

## Overview

Enable "memory" feature by storing message embeddings in `user_{user_id}_conversations` collection and searching past conversations for relevant context. This allows the AI to recall and reference previous discussions automatically.

## Current State

**Infrastructure Ready:**
- `user_{user_id}_conversations` collection structure defined
- `add_message_to_conversation_collection()` function implemented
- Metadata structure: `message_id`, `conversation_id`, `type` (user_message/assistant_message)
- Embedding generation available via `generate_embedding()`

**Not Active:**
- Messages not being stored in conversation collection
- No search function for conversation memory
- Memory context not integrated into RAG pipeline

## Target State

**Core Functionality:**
- Every message (user + assistant) stored with embeddings in conversation collection
- Semantic search across past conversations
- Relevant memory context automatically included in LLM prompts
- Configurable memory retrieval (number of results, recency bias)

**User Experience:**
- AI remembers previous discussions across all conversations
- Can reference past context naturally ("as we discussed before...")
- Users can opt in/out per conversation via a simple "Include memory" checkbox (default on)
- Transparent: users can see what memory is being used (optional UI enhancement)

## Implementation Steps

### 1. Enable Message Embedding Storage

**File**: `backend/src/backend/api/websocket.py`

**Changes:**
- After saving user message: generate embedding and store in conversation collection
- After saving assistant message: generate embedding and store in conversation collection
- Handle errors gracefully (don't fail chat if memory storage fails)

**Implementation:**
```python
# After line 113 (user message saved)
try:
    user_embedding = generate_embedding(user_message)
    add_message_to_conversation_collection(
        user_id, user_msg.id, conversation_id, 
        user_message, user_embedding, 'user_message'
    )
except Exception as e:
    print(f"Warning: Failed to store user message embedding: {e}")
    # Continue anyway - memory storage is non-critical

# After line 210 (assistant message saved)
try:
    assistant_embedding = generate_embedding(full_response)
    add_message_to_conversation_collection(
        user_id, assistant_msg.id, conversation_id,
        full_response, assistant_embedding, 'assistant_message'
    )
except Exception as e:
    print(f"Warning: Failed to store assistant message embedding: {e}")
```

### 2. Create Conversation Memory Search Function

**File**: `backend/src/backend/store/search.py`

**New Function:**
```python
def search_conversation_memory(
    user_id, 
    query_text, 
    exclude_conversation_id=None,
    n_results=5,
    message_types=None
):
    """Search user's conversation history for relevant context.
    
    Enables semantic "memory" by finding relevant past discussions.
    
    Args:
        user_id: User ID
        query_text: Query text to search for
        exclude_conversation_id: Optional conversation ID to exclude (current convo)
        n_results: Number of results to return (default: 5)
        message_types: Optional list of types to filter 
                      ['user_message', 'assistant_message']
        
    Returns:
        List of result dicts with 'text', 'metadata', 'distance'
    """
```

**Implementation Details:**
- Get `user_{user_id}_conversations` collection
- Generate query embedding
- Build where clause to exclude current conversation
- Optionally filter by message type
- Return formatted results with conversation context

### 3. Add Memory Context Formatting Helper

**File**: `backend/src/backend/store/search.py`

**New Function:**
```python
def format_memory_context(memory_results, max_items=3):
    """Format memory search results for LLM context.
    
    Args:
        memory_results: Results from search_conversation_memory
        max_items: Maximum memory items to include (default: 3)
        
    Returns:
        Formatted memory context string
    """
```

**Format:**
```
[Memory from past conversation {conv_id}]
{message_text}
```

### 4. Integrate Memory into RAG Pipeline

**File**: `backend/src/backend/api/websocket.py`

**Location**: After document search (line 135), before building LLM messages (line 137)

**Implementation:**
```python
# Search conversation memory
memory_context = ""
try:
    memory_results = search_conversation_memory(
        user_id,
        user_message,
        exclude_conversation_id=conversation_id,
        n_results=3
    )
    if memory_results:
        memory_context = format_memory_context(memory_results)
except Exception as e:
    print(f"Warning: Memory search failed: {e}")
    # Continue without memory - non-critical

# Combine contexts
combined_context = ""
if context:  # Document context
    combined_context += f"Document Context:\n{context}"
if memory_context:
    if combined_context:
        combined_context += "\n\n"
    combined_context += f"Relevant Past Discussions:\n{memory_context}"
```

**Update System Message:**
```python
if combined_context:
    system_message = (
        "You are a helpful assistant. Use the following information to provide "
        "contextual and informed responses:\n\n"
        f"{combined_context}\n\n"
        "If the context contains relevant information, reference it naturally. "
        "If not, use your general knowledge."
    )
```

### 5. Add Configuration

**File**: `backend/src/backend/config.py`

**New Settings:**
```python
# Memory settings
MEMORY_ENABLED = os.getenv('MEMORY_ENABLED', 'true').lower() == 'true'
MEMORY_MAX_RESULTS = int(os.getenv('MEMORY_MAX_RESULTS', '3'))
MEMORY_SEARCH_BOTH_TYPES = os.getenv('MEMORY_SEARCH_BOTH_TYPES', 'true').lower() == 'true'
```

### 6. Update Store Exports

**File**: `backend/src/backend/store/__init__.py`

**Add:**
```python
from .search import (
    search_user_documents,
    search_conversation_memory,
    format_memory_context,
    get_context_from_results
)

__all__ = [
    # ... existing exports ...
    'search_conversation_memory',
    'format_memory_context',
]
```

### 7. Optional: Memory Management API

**File**: `backend/src/backend/api/memory.py` (new file)

**Optional Endpoints:**
- `GET /api/memory/search?q={query}` - Test memory search
- `GET /api/memory/stats` - Show memory statistics (total messages stored)
- `DELETE /api/memory/clear` - Clear all conversation memory (privacy feature)

**Note:** This is optional - memory works without these endpoints.

### 8. Update Documentation

**Files**: 
- `backend/README.md` - Document memory feature
- `PROJECT_SUMMARY.md` - Update RAG flow with memory
- Comments in code

**Document:**
- How memory works
- What gets stored
- Privacy considerations
- Configuration options
- How to disable if desired

### 9. Add UI Toggle for Memory

**Files**: `interface/src/components/ChatArea.tsx`, `interface/src/context/ChatContext.tsx`, `interface/src/util/api.ts`

**Goals:**
- Add a checkbox near the chat input labeled "Include memory"
- Store preference per conversation in chat context (default true)
- Persist setting in local state so it remains when switching conversations
- Include `memory_enabled` flag in WebSocket payloads / API calls
- Update backend handler to respect per-request flag (skip memory search if disabled)

**Details:**
- In `ChatContext`, extend conversation state to track `memoryEnabled` per conversation
- In `ChatArea`, render checkbox tied to current conversation's preference
- When sending `chat_message`, include `memory_enabled` property
- Backend: read flag (`data.get('memory_enabled', True)`) to bypass memory search/storage if false
- UI should show tooltip noting potential 0.5s latency savings when disabled

## Configuration Options

### Environment Variables

```bash
# .env
MEMORY_ENABLED=true              # Enable/disable memory feature
MEMORY_MAX_RESULTS=3             # Max memory items per query
MEMORY_SEARCH_BOTH_TYPES=true    # Search both user and assistant messages
```

### Per-Request Configuration

Future enhancement: Allow frontend to pass memory preferences:
```python
{
  'conversation_id': 123,
  'message': 'What did we discuss about X?',
  'model': 'gpt-4',
  'memory_enabled': true,      # Override default
  'memory_max_results': 5      # Override default
}
```

## Memory Search Strategy

### What to Store
- User messages - capture what user discussed
- Assistant messages - capture AI insights and responses
- Not system messages - not relevant for memory

### What to Search
**Default:** Search both user and assistant messages
- User messages show topics/questions discussed
- Assistant messages show information provided

**Alternative:** Search only user messages
- Focuses on user's interests/topics
- May miss important AI insights

**Recommendation:** Search both types by default

### Filtering Strategy
- Always exclude current conversation (avoid circular reference)
- Optionally exclude very recent messages (< 5 minutes) to avoid redundancy
- Consider recency bias (weight recent memories higher)

## Testing Considerations

1. **Basic Functionality:**
   - Message embeddings stored successfully
   - Memory search returns relevant results
   - Context integrated into LLM prompts

2. **Edge Cases:**
   - First conversation (no memory exists)
   - Empty/short messages
   - Very long conversations
   - Memory search failure (should not break chat)

3. **Performance:**
   - Embedding generation time (< 100ms per message)
   - Memory search time (< 200ms)
   - Total overhead acceptable (< 500ms)

4. **Privacy:**
   - Messages only searchable by owning user
   - No cross-user memory leakage
   - Clear data on user deletion

## Future Enhancements

### Smart Memory Retrieval
- Recency bias: weight recent conversations higher
- Importance scoring: prioritize messages with high engagement
- Topic clustering: group related memories
- Conversation summaries: store condensed memory per conversation

### User Controls
- Toggle memory on/off per conversation
- View what memories are being used
- Edit/delete specific memories
- Export conversation memory

### Advanced Features
- Memory consolidation: merge similar memories
- Proactive memory: "You might want to know..."
- Cross-user memories: shared project context (with permission)
- Time-based filtering: "Discussions from last week"

## Privacy & Performance Notes

**Privacy:**
- All memory stored locally in user's ChromaDB collection
- No cloud storage or external services
- User-scoped: cannot access other users' memories
- Can be cleared/deleted anytime

**Performance:**
- Embedding generation: ~50-100ms per message
- Memory search: ~100-200ms per query
- Total overhead: ~300-500ms per message
- Acceptable for real-time chat experience

**Storage:**
- Each message = ~768 floats (embedding) + text + metadata
- 1000 messages ≈ 3-5MB in ChromaDB
- Scales well for typical usage (thousands of messages)

## Rollout Strategy

### Phase 1: Core Implementation (This Plan)
- Enable message storage
- Add memory search function
- Integrate into RAG pipeline
- Basic configuration

### Phase 2: Polish (Optional)
- Memory management API endpoints
- UI indicators for memory usage
- Performance optimization
- Advanced filtering

### Phase 3: Advanced Features (Future)
- Smart retrieval with scoring
- User controls and preferences
- Memory analytics
- Cross-conversation insights

## Todo List

- [ ] Enable embedding storage for user and assistant messages in websocket handler
- [ ] Create search_conversation_memory function with conversation exclusion
- [ ] Add format_memory_context helper function
- [ ] Integrate memory search into RAG pipeline in websocket handler
- [ ] Add memory configuration options to config.py
- [ ] Export new memory functions in store/__init__.py
- [ ] Document memory feature in README and PROJECT_SUMMARY
- [ ] Add UI checkbox + backend flag to let users include/exclude memory per conversation

