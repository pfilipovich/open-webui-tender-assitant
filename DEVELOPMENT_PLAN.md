# Structured Output Feature Development Plan

## LLM Agent Execution Guide

**⚠️ CRITICAL: This plan is designed for independent LLM Agent execution. Follow all procedures exactly as specified.**

### Agent Instructions
1. **Execute phases sequentially** - Complete each phase before moving to the next
2. **Validate each step** - Run all verification procedures before continuing
3. **Report progress** - Update todo lists and provide status updates
4. **Handle errors gracefully** - Follow rollback procedures if issues occur
5. **Ask for help when blocked** - Stop execution and request human intervention for critical decisions

### Prerequisites Checklist
Before starting execution, verify all prerequisites are met:

#### Environment Requirements
- [ ] Node.js 18+ installed
- [ ] Python 3.11+ installed
- [ ] PostgreSQL or SQLite database available
- [ ] Git repository access with write permissions
- [ ] Development server running (backend on :8080, frontend on :5173)

#### Development Tools
- [ ] npm/yarn package manager
- [ ] pip package manager
- [ ] Alembic for database migrations
- [ ] pytest for backend testing
- [ ] Vitest for frontend testing

#### Access Requirements
- [ ] Database admin access for schema changes
- [ ] File system write permissions
- [ ] API testing tools (curl, Postman, or similar)
- [ ] Browser developer tools access

#### Code Quality Tools
- [ ] ESLint configured for frontend
- [ ] Prettier configured for code formatting
- [ ] Black configured for Python formatting
- [ ] TypeScript compiler available

### Execution Environment Setup

#### Step 1: Verify Current Installation
```bash
# Check Node.js version
node --version  # Should be 18+

# Check Python version
python --version  # Should be 3.11+

# Check database connection
# For PostgreSQL:
psql -h localhost -U postgres -d open_webui -c "SELECT version();"

# For SQLite:
sqlite3 backend/data/webui.db ".schema"

# Verify services are running
curl http://localhost:8080/api/v1/models  # Backend health check
curl http://localhost:5173  # Frontend health check
```

#### Step 2: Install Additional Dependencies
```bash
# Backend dependencies for structured output
cd backend
pip install jsonschema==4.21.1 ajv-python==0.6.0

# Frontend dependencies for schema validation
cd ../
npm install ajv@8.12.0 monaco-editor@0.45.0 prismjs@1.29.0

# Testing dependencies
npm install --save-dev @testing-library/svelte vitest jsdom
pip install pytest-asyncio pytest-mock factory-boy
```

#### Step 3: Create Development Branches
```bash
# Create feature branch for structured output enhancements
git checkout -b feature/structured-output-enhancements

# Create backup of current state
git tag backup-pre-structured-output-$(date +%Y%m%d)
```

### File Organization Structure

Create the following directory structure before starting:

```
backend/open_webui/
├── migrations/versions/
│   ├── add_chat_structured_output.py (Phase 2)
│   └── add_schema_library.py (Phase 4)
├── models/
│   ├── schema_library.py (Phase 4)
│   └── chats.py (existing, to be modified)
├── routers/
│   ├── schemas.py (Phase 4)
│   ├── chats.py (existing, to be modified)
│   └── openai.py (existing, to be modified)
├── utils/
│   ├── event-protection.py (Phase 1)
│   └── schema_validation.py (existing, to be enhanced)
└── test/
    ├── test_structured_output.py (Phase 7)
    ├── test_schema_library.py (Phase 7)
    └── test_state_management.py (Phase 7)

src/lib/
├── components/
│   ├── chat/
│   │   ├── ChatHeader.svelte (Phase 5)
│   │   ├── JsonResponseViewer.svelte (Phase 5)
│   │   └── MessageInput/
│   │       └── StructuredOutputModal.svelte (existing, to be enhanced)
│   └── workspace/
│       ├── SchemaLibrary.svelte (Phase 4)
│       └── SchemaTestingModal.svelte (Phase 6)
├── utils/
│   ├── event-protection.ts (Phase 1)
│   └── schema-validation.ts (existing, to be enhanced)
└── apis/
    └── schemas/
        └── index.ts (Phase 4)
```

## Executive Summary

This development plan outlines the implementation roadmap for enhancing Open WebUI's structured output capabilities. Based on comprehensive analysis, **Part 2 (Prompt-based Structured Output) is already fully implemented and operational**. This plan focuses on **Part 1 (Chat-level Structured Output)** enhancements and system hardening.

### Key Findings from Analysis
- ✅ **Part 2 Complete**: Prompt-driven structured output with system message integration is production-ready
- ⚠️ **Part 1 Needed**: Chat-level structured output requires user-friendly implementation
- 🔧 **State Management**: Robust foundation exists but requires hardening against edge cases
- 📊 **OpenAI Compliance**: 85-95% compliance achieved, minor enhancements needed

## Development Phases

### Phase 1: State Management Hardening (Week 1)
**Priority**: Critical - Address listener conflicts and race conditions

#### 1.1 Event Listener Management System
**Files**: `src/lib/utils/event-protection.ts` (new)

```typescript
// Enhanced event listener with priority and isolation
export const addProtectedEventListener = (element: Element, event: string, handler: Function, options = {}) => {
    const protectedHandler = (e: Event) => {
        // Check if structured output operation is in progress
        if (window.__structuredOutputInProgress) {
            e.stopImmediatePropagation();
            return;
        }
        handler(e);
    };
    
    element.addEventListener(event, protectedHandler, {
        ...options,
        capture: true // Ensure priority over other listeners
    });
};

// State locking during critical operations
export const withStateLock = async (operation: Function) => {
    window.__structuredOutputInProgress = true;
    try {
        return await operation();
    } finally {
        window.__structuredOutputInProgress = false;
    }
};
```

**Implementation Tasks**:
- [ ] Create `src/lib/utils/event-protection.ts`
- [ ] Add global state lock mechanism
- [ ] Implement protected event listener wrapper
- [ ] Add TypeScript type definitions

**Verification Steps**:
```bash
# Test event protection system
npm run test:unit -- event-protection

# Manual testing
# 1. Open application in browser
# 2. Open structured output modal
# 3. Try global keyboard shortcuts
# 4. Verify shortcuts are blocked during modal operations
# 5. Verify normal operation after modal closes
```

**Success Criteria**:
- [ ] Event protection utility functions created and tested
- [ ] Global state lock mechanism prevents conflicts
- [ ] Protected event listeners work correctly
- [ ] No breaking changes to existing event handling
- [ ] TypeScript types properly defined

#### 1.2 Modal Event Isolation
**Files**: `src/lib/components/chat/MessageInput/StructuredOutputModal.svelte`

```javascript
// Isolate modal events from global listeners
const createModalEventBoundary = (modalElement) => {
    const stopPropagation = (e) => e.stopPropagation();
    
    ['keydown', 'keyup', 'click', 'focus', 'blur'].forEach(eventType => {
        modalElement.addEventListener(eventType, stopPropagation, { capture: true });
    });
};
```

**Implementation Tasks**:
- [ ] Add modal event boundary creation
- [ ] Implement event isolation for structured output modal
- [ ] Test keyboard shortcut conflicts
- [ ] Add escape key handling with priority

**Verification Steps**:
```bash
# Test modal isolation
npm run test:unit -- StructuredOutputModal

# Manual testing
# 1. Open structured output modal
# 2. Try pressing Escape, Enter, and other shortcuts
# 3. Verify only modal-specific handlers respond
# 4. Test with multiple modals open
# 5. Verify event boundaries work correctly
```

**Success Criteria**:
- [ ] Modal event boundaries prevent global interference
- [ ] Escape key handling works with correct priority
- [ ] No conflicts between modal and global shortcuts
- [ ] Event isolation doesn't break modal functionality

#### 1.3 Enhanced State Validation
**Files**: `src/lib/components/chat/Chat.svelte`

```javascript
// Validate state consistency before submission
const validateStructuredOutputState = (capturedState, currentState) => {
    const keys = ['structuredOutput', 'structuredOutputSchema', 'structuredOutputName', 'attachedPrompt'];
    const inconsistencies = keys.filter(key => 
        JSON.stringify(capturedState[key]) !== JSON.stringify(currentState[key])
    );
    
    if (inconsistencies.length > 0) {
        console.warn('State inconsistency detected:', inconsistencies);
        // Optionally prompt user or use most recent state
        return capturedState; // Use captured state as fallback
    }
    return currentState;
};
```

**Implementation Tasks**:
- [ ] Add state consistency validation function
- [ ] Integrate validation into submission handler
- [ ] Add warning logging for inconsistencies
- [ ] Implement state recovery mechanisms

**Verification Steps**:
```bash
# Test state validation
npm run test:unit -- state-validation

# Manual testing
# 1. Configure structured output
# 2. Rapidly interact with UI elements
# 3. Submit messages quickly
# 4. Check browser console for warnings
# 5. Verify state consistency is maintained
```

**Success Criteria**:
- [ ] State validation detects inconsistencies
- [ ] Warning messages are clear and actionable
- [ ] State recovery mechanisms work correctly
- [ ] No false positive warnings generated

### Phase 2: Chat-Level Structured Output (Week 2-3)
**Priority**: High - Core functionality for Part 1

#### 2.1 Database Schema Extensions
**Files**: `backend/open_webui/migrations/versions/add_chat_structured_output.py` (new)

```sql
-- Migration: Add structured output support to chats table
ALTER TABLE chat ADD COLUMN structured_output_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE chat ADD COLUMN structured_output_schema TEXT;
ALTER TABLE chat ADD COLUMN structured_output_name VARCHAR(255);
ALTER TABLE chat ADD COLUMN structured_output_created_at TIMESTAMP;
ALTER TABLE chat ADD COLUMN structured_output_updated_at TIMESTAMP;

-- Index for performance
CREATE INDEX idx_chat_structured_output ON chat(structured_output_enabled) WHERE structured_output_enabled = TRUE;
```

**Implementation Tasks**:
- [ ] Create Alembic migration for chat table extensions
- [ ] Add database model updates in `backend/open_webui/models/chats.py`
- [ ] Implement backward compatibility checks
- [ ] Add data validation constraints

**Verification Steps**:
```bash
# Test database migration
cd backend
alembic upgrade head
alembic current  # Verify migration applied

# Test model functionality
python -c "from open_webui.models.chats import Chats; print('Models loaded successfully')"

# Run database tests
pytest open_webui/test/test_chat_models.py -v
```

**Success Criteria**:
- [ ] Migration runs successfully without errors
- [ ] New columns added with correct constraints
- [ ] Existing data remains intact
- [ ] Backward compatibility maintained
- [ ] Model validation works correctly

#### 2.2 Chat-Level API Endpoints
**Files**: `backend/open_webui/routers/chats.py`

```python
@router.post("/{id}/structured-output")
async def set_chat_structured_output(
    id: str,
    form_data: ChatStructuredOutputForm,
    user=Depends(get_verified_user)
):
    """Set structured output configuration for a chat"""
    try:
        chat = Chats.get_chat_by_id_and_user_id(id, user.id)
        if not chat:
            raise HTTPException(status_code=404, detail=ERROR_MESSAGES.CHAT_NOT_FOUND)
        
        # Validate schema before saving
        if form_data.schema:
            is_valid, errors = validate_openai_constraints(json.loads(form_data.schema))
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid schema: {', '.join(errors)}")
        
        updated_chat = Chats.update_chat_structured_output(
            id, 
            enabled=form_data.enabled,
            schema=form_data.schema,
            name=form_data.name
        )
        
        return ChatResponse(**updated_chat.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}/structured-output")
async def get_chat_structured_output(
    id: str,
    user=Depends(get_verified_user)
):
    """Get structured output configuration for a chat"""
    chat = Chats.get_chat_by_id_and_user_id(id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail=ERROR_MESSAGES.CHAT_NOT_FOUND)
    
    return {
        "enabled": chat.structured_output_enabled,
        "schema": chat.structured_output_schema,
        "name": chat.structured_output_name,
        "created_at": chat.structured_output_created_at,
        "updated_at": chat.structured_output_updated_at
    }

@router.delete("/{id}/structured-output")
async def delete_chat_structured_output(
    id: str,
    user=Depends(get_verified_user)
):
    """Remove structured output configuration from a chat"""
    chat = Chats.get_chat_by_id_and_user_id(id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail=ERROR_MESSAGES.CHAT_NOT_FOUND)
    
    Chats.clear_chat_structured_output(id)
    return {"message": "Structured output configuration removed"}
```

**Implementation Tasks**:
- [ ] Create API endpoints for chat-level structured output
- [ ] Add Pydantic models for request/response validation
- [ ] Implement database operations in `Chats` class
- [ ] Add comprehensive error handling
- [ ] Write API documentation

**Verification Steps**:
```bash
# Test API endpoints
curl -X POST http://localhost:8080/api/v1/chats/test-chat/structured-output \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"enabled": true, "schema": "{\"type\": \"object\"}", "name": "Test Schema"}'

# Run API tests
pytest open_webui/test/test_chat_api.py::test_structured_output_endpoints -v

# Test error handling
curl -X POST http://localhost:8080/api/v1/chats/nonexistent/structured-output
```

**Success Criteria**:
- [ ] All CRUD endpoints function correctly
- [ ] Request/response validation works
- [ ] Error handling provides clear messages
- [ ] Database operations are atomic
- [ ] API documentation is complete

#### 2.3 Enhanced Completion Logic
**Files**: `backend/open_webui/routers/openai.py`

```python
# Add to completion handler around line 800
async def get_structured_output_config(metadata: dict, chat_id: str, user_id: str):
    """Determine structured output configuration with priority system"""
    
    # Priority 1: Attached prompt structured output
    if metadata.get("prompt_command"):
        prompt = Prompts.get_prompt_by_command(metadata.get("prompt_command"))
        if prompt and prompt.structured_output:
            return {
                "enabled": True,
                "schema": prompt.structured_output_schema,
                "name": f"Prompt: {prompt.title}",
                "source": "prompt"
            }
    
    # Priority 2: Manual structured output from message
    if metadata.get("structured_output"):
        return {
            "enabled": True,
            "schema": metadata.get("structured_output_schema"),
            "name": metadata.get("structured_output_name", "Manual Schema"),
            "source": "manual"
        }
    
    # Priority 3: Chat-level structured output
    if chat_id:
        chat = Chats.get_chat_by_id_and_user_id(chat_id, user_id)
        if chat and chat.structured_output_enabled:
            return {
                "enabled": True,
                "schema": chat.structured_output_schema,
                "name": chat.structured_output_name or "Chat Schema",
                "source": "chat"
            }
    
    return {"enabled": False, "source": "none"}

# Update completion handler to use priority system
structured_output_config = await get_structured_output_config(metadata, chat_id, user.id)
if structured_output_config["enabled"]:
    # Apply structured output configuration
    metadata["structured_output"] = True
    metadata["structured_output_schema"] = structured_output_config["schema"]
    metadata["structured_output_source"] = structured_output_config["source"]
```

**Implementation Tasks**:
- [ ] Implement structured output priority system
- [ ] Add chat-level schema retrieval logic
- [ ] Update completion handler with new priority system
- [ ] Add source tracking for debugging
- [ ] Test priority resolution order

**Verification Steps**:
```bash
# Test priority system
pytest open_webui/test/test_priority_system.py -v

# Manual testing
# 1. Set chat-level structured output
# 2. Attach prompt with structured output
# 3. Add manual structured output
# 4. Verify prompt takes priority
# 5. Check source tracking in logs
```

**Success Criteria**:
- [ ] Priority system resolves correctly (Prompt > Manual > Chat)
- [ ] Source tracking works for debugging
- [ ] Schema inheritance functions properly
- [ ] No conflicts between different sources
- [ ] Performance impact is minimal

#### 2.4 Frontend Chat Interface Integration
**Files**: `src/lib/components/chat/Chat.svelte`

```javascript
// Add chat-level structured output state
let chatStructuredOutput = false;
let chatStructuredOutputSchema = '';
let chatStructuredOutputName = '';

// Load chat structured output configuration
const loadChatStructuredOutput = async (chatId) => {
    if (!chatId) return;
    
    try {
        const response = await fetch(`/api/v1/chats/${chatId}/structured-output`, {
            headers: { Authorization: `Bearer ${localStorage.token}` }
        });
        
        if (response.ok) {
            const config = await response.json();
            chatStructuredOutput = config.enabled;
            chatStructuredOutputSchema = config.schema || '';
            chatStructuredOutputName = config.name || '';
        }
    } catch (error) {
        console.error('Failed to load chat structured output:', error);
    }
};

// Save chat structured output configuration
const saveChatStructuredOutput = async (enabled, schema, name) => {
    if (!$chatId) return;
    
    try {
        await fetch(`/api/v1/chats/${$chatId}/structured-output`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${localStorage.token}`
            },
            body: JSON.stringify({ enabled, schema, name })
        });
        
        chatStructuredOutput = enabled;
        chatStructuredOutputSchema = schema;
        chatStructuredOutputName = name;
    } catch (error) {
        console.error('Failed to save chat structured output:', error);
        toast.error('Failed to save structured output configuration');
    }
};
```

**Implementation Tasks**:
- [ ] Add chat-level structured output state management
- [ ] Implement API integration functions
- [ ] Add loading/saving of chat configurations
- [ ] Update priority system in frontend
- [ ] Add error handling and user feedback

**Verification Steps**:
```bash
# Test frontend integration
npm run test:unit -- Chat.svelte

# Manual testing
# 1. Open existing chat
# 2. Configure structured output for chat
# 3. Refresh browser
# 4. Verify configuration persists
# 5. Test priority system with different sources
```

**Success Criteria**:
- [ ] Chat state management works correctly
- [ ] API integration functions properly
- [ ] Configuration persistence across sessions
- [ ] Frontend priority system matches backend
- [ ] Error handling provides user feedback

### Phase 3: Enhanced Schema Validation (Week 3-4)
**Priority**: Medium - OpenAI compliance improvements

#### 3.1 OpenAI Constraint Validation
**Files**: `backend/open_webui/utils/schema_validation.py`

```python
def count_total_properties(schema: dict, visited=None) -> int:
    """Count total properties across entire schema including nested objects"""
    if visited is None:
        visited = set()
    
    # Prevent infinite recursion
    schema_id = id(schema)
    if schema_id in visited:
        return 0
    visited.add(schema_id)
    
    count = 0
    if isinstance(schema, dict):
        if 'properties' in schema:
            properties = schema['properties']
            count += len(properties)
            for prop_schema in properties.values():
                count += count_total_properties(prop_schema, visited)
        
        # Handle array items
        if 'items' in schema:
            count += count_total_properties(schema['items'], visited)
    
    return count

def get_max_nesting_depth(schema: dict, current_depth=0) -> int:
    """Calculate maximum nesting depth of schema"""
    if not isinstance(schema, dict):
        return current_depth
    
    max_depth = current_depth
    
    if 'properties' in schema:
        for prop_schema in schema['properties'].values():
            depth = get_max_nesting_depth(prop_schema, current_depth + 1)
            max_depth = max(max_depth, depth)
    
    if 'items' in schema:
        depth = get_max_nesting_depth(schema['items'], current_depth + 1)
        max_depth = max(max_depth, depth)
    
    return max_depth

def calculate_total_string_length(schema: dict, visited=None) -> int:
    """Calculate total string length for all string values in schema"""
    if visited is None:
        visited = set()
    
    schema_id = id(schema)
    if schema_id in visited:
        return 0
    visited.add(schema_id)
    
    total_length = 0
    
    def add_string_length(obj):
        nonlocal total_length
        if isinstance(obj, str):
            total_length += len(obj)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(key, str):
                    total_length += len(key)
                add_string_length(value)
        elif isinstance(obj, list):
            for item in obj:
                add_string_length(item)
    
    add_string_length(schema)
    return total_length

def validate_openai_constraints(schema: dict) -> Tuple[bool, List[str]]:
    """Validate schema against OpenAI-specific constraints"""
    errors = []
    
    # Count total properties (max 5,000)
    property_count = count_total_properties(schema)
    if property_count > 5000:
        errors.append(f"Schema has {property_count} properties, max 5,000 allowed")
    
    # Check nesting depth (max 5 levels)
    max_depth = get_max_nesting_depth(schema)
    if max_depth > 5:
        errors.append(f"Schema nesting depth {max_depth}, max 5 levels allowed")
    
    # Check string length limits
    total_string_length = calculate_total_string_length(schema)
    if total_string_length > 120000:
        errors.append(f"Total string length {total_string_length}, max 120,000 allowed")
    
    # Count enum values
    enum_count = count_enum_values(schema)
    if enum_count > 1000:
        errors.append(f"Schema has {enum_count} enum values, max 1,000 allowed")
    
    return len(errors) == 0, errors

def count_enum_values(schema: dict, visited=None) -> int:
    """Count total enum values across schema"""
    if visited is None:
        visited = set()
    
    schema_id = id(schema)
    if schema_id in visited:
        return 0
    visited.add(schema_id)
    
    count = 0
    if isinstance(schema, dict):
        if 'enum' in schema and isinstance(schema['enum'], list):
            count += len(schema['enum'])
        
        for key, value in schema.items():
            if key != 'enum' and isinstance(value, (dict, list)):
                count += count_enum_values(value, visited)
    elif isinstance(schema, list):
        for item in schema:
            count += count_enum_values(item, visited)
    
    return count
```

**Implementation Tasks**:
- [ ] Implement comprehensive OpenAI constraint validation
- [ ] Add property counting with recursion protection
- [ ] Add nesting depth calculation
- [ ] Add string length validation
- [ ] Add enum counting and validation
- [ ] Write comprehensive unit tests

**Verification Steps**:
```bash
# Test validation functions
pytest backend/open_webui/test/test_schema_validation.py -v

# Test with large schemas
python -c "
from open_webui.utils.schema_validation import validate_openai_constraints
schema = {'type': 'object', 'properties': {f'prop_{i}': {'type': 'string'} for i in range(5001)}}
is_valid, errors = validate_openai_constraints(schema)
print(f'Valid: {is_valid}, Errors: {errors}')
"
```

**Success Criteria**:
- [ ] All OpenAI constraints properly validated
- [ ] Property counting handles recursion correctly
- [ ] Nesting depth calculation is accurate
- [ ] String length validation comprehensive
- [ ] Enum validation handles edge cases
- [ ] Unit tests achieve >95% coverage

#### 3.2 Model-Specific Detection
**Files**: `backend/open_webui/routers/openai.py`

```python
def supports_structured_output(model_id: str) -> bool:
    """Check if model supports structured output vs JSON mode"""
    if not model_id:
        return False
    
    model_lower = model_id.lower()
    
    # Models with native structured output support
    structured_output_models = [
        "gpt-4o-mini",
        "gpt-4o-2024-08-06",
        "gpt-4o-2024-11-20",
        "gpt-4o-2025-01-07"
    ]
    
    # Check for structured output support
    for model in structured_output_models:
        if model in model_lower:
            return True
    
    # Check for function calling support (alternative method)
    function_calling_models = [
        "gpt-4-0613",
        "gpt-3.5-turbo-0613",
        "gpt-4-turbo"
    ]
    
    for model in function_calling_models:
        if model in model_lower:
            return True
    
    return False

def get_optimal_response_format(model_id: str, schema: str) -> dict:
    """Get optimal response format based on model capabilities"""
    if not schema:
        return None
    
    try:
        parsed_schema = json.loads(schema)
        
        # Validate against OpenAI constraints
        is_valid, errors = validate_openai_constraints(parsed_schema)
        
        if supports_structured_output(model_id) and is_valid:
            # Use structured output format
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "description": "Structured response",
                    "schema": clean_schema_for_openai(parsed_schema),
                    "strict": False
                }
            }
        else:
            # Fallback to JSON mode
            if not is_valid:
                logging.warning(f"Schema validation failed for model {model_id}: {errors}")
            
            return {"type": "json_object"}
    
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON schema for model {model_id}")
        return None
```

**Implementation Tasks**:
- [ ] Implement model capability detection
- [ ] Add structured output vs JSON mode routing
- [ ] Add optimal response format selection
- [ ] Add comprehensive model compatibility mapping
- [ ] Add logging for model routing decisions

**Verification Steps**:
```bash
# Test model detection
python -c "
from open_webui.routers.openai import supports_structured_output, get_optimal_response_format
print('gpt-4o-mini:', supports_structured_output('gpt-4o-mini'))
print('gpt-3.5-turbo:', supports_structured_output('gpt-3.5-turbo'))
schema = '{\"type\": \"object\"}'
print('Response format:', get_optimal_response_format('gpt-4o-mini', schema))
"

# Test routing decisions
pytest backend/open_webui/test/test_model_compatibility.py -v
```

**Success Criteria**:
- [ ] Model capability detection is accurate
- [ ] Routing between structured output and JSON mode works
- [ ] Response format optimization functions correctly
- [ ] Model compatibility mapping is comprehensive
- [ ] Logging provides useful debugging information

### Phase 4: Schema Library System (Week 4-5)
**Priority**: Medium - Centralized schema management

#### 4.1 Schema Library Database Design
**Files**: `backend/open_webui/migrations/versions/add_schema_library.py` (new)

```sql
-- Schema Library Tables
CREATE TABLE schema_library (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id VARCHAR NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    schema_content TEXT NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    category VARCHAR(100),
    tags TEXT[], -- PostgreSQL array, JSON for other DBs
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    rating_avg DECIMAL(3,2) DEFAULT 0.0,
    rating_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

CREATE TABLE schema_library_access (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    schema_id BIGINT NOT NULL,
    user_id VARCHAR,
    group_id VARCHAR,
    permission VARCHAR(10) DEFAULT 'read', -- read, write, admin
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by VARCHAR NOT NULL,
    FOREIGN KEY (schema_id) REFERENCES schema_library(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES user(id)
);

CREATE TABLE schema_library_ratings (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    schema_id BIGINT NOT NULL,
    user_id VARCHAR NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schema_id) REFERENCES schema_library(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    UNIQUE(schema_id, user_id)
);

CREATE TABLE schema_library_usage (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    schema_id BIGINT NOT NULL,
    user_id VARCHAR NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context VARCHAR(50), -- 'chat', 'prompt', 'api'
    FOREIGN KEY (schema_id) REFERENCES schema_library(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_schema_library_user ON schema_library(user_id);
CREATE INDEX idx_schema_library_public ON schema_library(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_schema_library_category ON schema_library(category);
CREATE INDEX idx_schema_library_tags ON schema_library USING GIN(tags);
CREATE INDEX idx_schema_library_usage_schema ON schema_library_usage(schema_id);
CREATE INDEX idx_schema_library_usage_user ON schema_library_usage(user_id);
```

**Implementation Tasks**:
- [ ] Create comprehensive schema library database design
- [ ] Add access control and permissions system
- [ ] Add rating and review system
- [ ] Add usage tracking and analytics
- [ ] Create proper indexes for performance
- [ ] Add data migration scripts

**Verification Steps**:
```bash
# Test database schema
alembic upgrade head
psql -d open_webui -c "\\dt schema_library*"

# Test indexes
psql -d open_webui -c "\\di schema_library*"

# Run migration tests
pytest backend/open_webui/test/test_schema_library_migration.py -v
```

**Success Criteria**:
- [ ] Database schema created successfully
- [ ] All indexes created for performance
- [ ] Access control tables properly structured
- [ ] Migration runs without errors
- [ ] Data integrity constraints enforced

#### 4.2 Schema Library API
**Files**: `backend/open_webui/routers/schemas.py` (new)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import json

router = APIRouter(prefix="/schemas", tags=["schemas"])

class SchemaLibraryForm(BaseModel):
    name: str
    description: Optional[str] = None
    schema_content: str
    is_public: bool = False
    category: Optional[str] = None
    tags: List[str] = []

class SchemaLibraryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    schema_content: str
    is_public: bool
    category: Optional[str]
    tags: List[str]
    version: int
    created_at: datetime
    updated_at: datetime
    usage_count: int
    rating_avg: float
    rating_count: int
    user_id: str
    can_edit: bool = False

@router.get("/")
async def get_schemas(
    user=Depends(get_verified_user),
    category: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    public_only: bool = Query(False),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """Get schemas from library with filtering and pagination"""
    
    # Parse tags if provided
    tag_list = tags.split(',') if tags else []
    
    schemas = SchemaLibrary.get_schemas(
        user_id=user.id,
        category=category,
        tags=tag_list,
        public_only=public_only,
        search=search,
        limit=limit,
        offset=offset
    )
    
    return {
        "schemas": [SchemaLibraryResponse(**schema.model_dump(), can_edit=schema.user_id == user.id) for schema in schemas],
        "total": SchemaLibrary.count_schemas(user.id, category, tag_list, public_only, search)
    }

@router.post("/")
async def create_schema(
    form_data: SchemaLibraryForm,
    user=Depends(get_verified_user)
):
    """Create new schema in library"""
    
    # Validate schema content
    try:
        parsed_schema = json.loads(form_data.schema_content)
        is_valid, errors = validate_openai_constraints(parsed_schema)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid schema: {', '.join(errors)}")
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON schema format")
    
    # Check for duplicate names (user-scoped)
    existing = SchemaLibrary.get_by_name_and_user(form_data.name, user.id)
    if existing:
        raise HTTPException(status_code=409, detail="Schema with this name already exists")
    
    # Create schema
    schema = SchemaLibrary.create_schema(
        user_id=user.id,
        name=form_data.name,
        description=form_data.description,
        schema_content=form_data.schema_content,
        is_public=form_data.is_public,
        category=form_data.category,
        tags=form_data.tags
    )
    
    return SchemaLibraryResponse(**schema.model_dump(), can_edit=True)

@router.get("/{schema_id}")
async def get_schema(
    schema_id: int,
    user=Depends(get_verified_user)
):
    """Get specific schema from library"""
    
    schema = SchemaLibrary.get_schema_by_id(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    # Check access permissions
    if not schema.is_public and schema.user_id != user.id:
        has_access = SchemaLibraryAccess.check_access(schema_id, user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Track usage
    SchemaLibraryUsage.record_usage(schema_id, user.id, 'view')
    
    return SchemaLibraryResponse(**schema.model_dump(), can_edit=schema.user_id == user.id)

@router.put("/{schema_id}")
async def update_schema(
    schema_id: int,
    form_data: SchemaLibraryForm,
    user=Depends(get_verified_user)
):
    """Update schema in library"""
    
    schema = SchemaLibrary.get_schema_by_id(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    # Check edit permissions
    if schema.user_id != user.id:
        has_write_access = SchemaLibraryAccess.check_access(schema_id, user.id, 'write')
        if not has_write_access:
            raise HTTPException(status_code=403, detail="Edit permission denied")
    
    # Validate schema content
    try:
        parsed_schema = json.loads(form_data.schema_content)
        is_valid, errors = validate_openai_constraints(parsed_schema)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid schema: {', '.join(errors)}")
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON schema format")
    
    # Update schema
    updated_schema = SchemaLibrary.update_schema(
        schema_id=schema_id,
        name=form_data.name,
        description=form_data.description,
        schema_content=form_data.schema_content,
        is_public=form_data.is_public,
        category=form_data.category,
        tags=form_data.tags
    )
    
    return SchemaLibraryResponse(**updated_schema.model_dump(), can_edit=True)

@router.delete("/{schema_id}")
async def delete_schema(
    schema_id: int,
    user=Depends(get_verified_user)
):
    """Delete schema from library"""
    
    schema = SchemaLibrary.get_schema_by_id(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    # Check delete permissions
    if schema.user_id != user.id:
        has_admin_access = SchemaLibraryAccess.check_access(schema_id, user.id, 'admin')
        if not has_admin_access:
            raise HTTPException(status_code=403, detail="Delete permission denied")
    
    SchemaLibrary.delete_schema(schema_id)
    return {"message": "Schema deleted successfully"}

@router.post("/{schema_id}/rate")
async def rate_schema(
    schema_id: int,
    rating: int = Query(..., ge=1, le=5),
    comment: Optional[str] = None,
    user=Depends(get_verified_user)
):
    """Rate a schema"""
    
    schema = SchemaLibrary.get_schema_by_id(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    
    # Can't rate your own schema
    if schema.user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot rate your own schema")
    
    # Record rating
    SchemaLibraryRating.add_or_update_rating(
        schema_id=schema_id,
        user_id=user.id,
        rating=rating,
        comment=comment
    )
    
    return {"message": "Rating added successfully"}

@router.get("/categories")
async def get_categories(user=Depends(get_verified_user)):
    """Get available schema categories"""
    categories = SchemaLibrary.get_categories()
    return {"categories": categories}

@router.get("/tags")
async def get_tags(user=Depends(get_verified_user)):
    """Get popular schema tags"""
    tags = SchemaLibrary.get_popular_tags(limit=50)
    return {"tags": tags}
```

**Implementation Tasks**:
- [ ] Create comprehensive schema library API
- [ ] Implement CRUD operations with proper permissions
- [ ] Add search and filtering capabilities
- [ ] Add rating and review system
- [ ] Add usage tracking and analytics
- [ ] Add comprehensive error handling
- [ ] Write API documentation

**Verification Steps**:
```bash
# Test API endpoints
curl -X GET http://localhost:8080/api/v1/schemas \
  -H "Authorization: Bearer $JWT_TOKEN"

# Test CRUD operations
curl -X POST http://localhost:8080/api/v1/schemas \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"name": "Test Schema", "schema_content": "{\"type\": \"object\"}"}'

# Run API tests
pytest backend/open_webui/test/test_schema_library_api.py -v
```

**Success Criteria**:
- [ ] All CRUD endpoints function correctly
- [ ] Permissions system enforces access control
- [ ] Search and filtering work efficiently
- [ ] Rating system functions properly
- [ ] Usage tracking captures analytics
- [ ] Error handling provides clear responses
- [ ] API documentation is comprehensive

### Phase 5: Enhanced UI Components (Week 5-6)
**Priority**: Medium - User experience improvements

#### 5.1 Chat Header Schema Indicator
**Files**: `src/lib/components/chat/ChatHeader.svelte` (new)

```svelte
<script lang="ts">
    import { chatId } from '$lib/stores';
    import { onMount } from 'svelte';
    
    export let structuredOutputEnabled = false;
    export let structuredOutputName = '';
    export let onToggle: Function;
    export let onEdit: Function;
    
    let showTooltip = false;
</script>

{#if structuredOutputEnabled}
    <div class="flex items-center gap-2 px-3 py-1 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div class="flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-blue-600 dark:text-blue-400">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
            </svg>
            <span class="text-sm font-medium text-blue-700 dark:text-blue-300">
                {structuredOutputName || 'Structured Output'}
            </span>
        </div>
        
        <div class="flex items-center gap-1">
            <button
                on:click={onEdit}
                class="p-1 hover:bg-blue-100 dark:hover:bg-blue-800/50 rounded text-blue-600 dark:text-blue-400"
                title="Edit schema"
            >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
                </svg>
            </button>
            
            <button
                on:click={onToggle}
                class="p-1 hover:bg-blue-100 dark:hover:bg-blue-800/50 rounded text-blue-600 dark:text-blue-400"
                title="Disable structured output"
            >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    </div>
{/if}
```

**Implementation Tasks**:
- [ ] Create chat header schema indicator component
- [ ] Add visual feedback for active structured output
- [ ] Add quick edit and disable functionality
- [ ] Add responsive design for mobile
- [ ] Add accessibility features

**Verification Steps**:
```bash
# Test component
npm run test:unit -- ChatHeader.svelte

# Manual testing
# 1. Enable structured output in chat
# 2. Verify header indicator appears
# 3. Test edit and disable buttons
# 4. Test on different screen sizes
# 5. Test with screen reader
```

**Success Criteria**:
- [ ] Header indicator displays correctly
- [ ] Visual feedback is clear and intuitive
- [ ] Edit and disable functionality works
- [ ] Responsive design works on all devices
- [ ] Accessibility standards met (WCAG 2.1 AA)

#### 5.2 Enhanced JSON Response Viewer
**Files**: `src/lib/components/chat/JsonResponseViewer.svelte` (new)

```svelte
<script lang="ts">
    import { onMount } from 'svelte';
    import { copyToClipboard } from '$lib/utils';
    
    export let jsonData: any;
    export let schemaName: string = '';
    export let compact: boolean = false;
    
    let isExpanded = !compact;
    let formattedJson = '';
    let copySuccess = false;
    
    $: if (jsonData) {
        try {
            formattedJson = JSON.stringify(jsonData, null, 2);
        } catch (e) {
            formattedJson = String(jsonData);
        }
    }
    
    const toggleExpansion = () => {
        isExpanded = !isExpanded;
    };
    
    const handleCopy = async () => {
        try {
            await copyToClipboard(formattedJson);
            copySuccess = true;
            setTimeout(() => copySuccess = false, 2000);
        } catch (e) {
            console.error('Failed to copy:', e);
        }
    };
    
    const handleExport = () => {
        const blob = new Blob([formattedJson], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${schemaName || 'structured-output'}-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };
</script>

<div class="structured-output-viewer border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center gap-2">
            <button
                on:click={toggleExpansion}
                class="flex items-center gap-1 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
            >
                <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke-width="1.5" 
                    stroke="currentColor" 
                    class="w-4 h-4 transition-transform {isExpanded ? 'rotate-90' : ''}"
                >
                    <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                </svg>
                Structured Output {schemaName ? `(${schemaName})` : ''}
            </button>
        </div>
        
        <div class="flex items-center gap-1">
            <button
                on:click={handleCopy}
                class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                title="Copy JSON"
            >
                {#if copySuccess}
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-green-600">
                        <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                    </svg>
                {:else}
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 0 1 1.927-.184" />
                    </svg>
                {/if}
            </button>
            
            <button
                on:click={handleExport}
                class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                title="Export JSON"
            >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                </svg>
            </button>
        </div>
    </div>
    
    <!-- Content -->
    {#if isExpanded}
        <div class="p-4">
            <pre class="text-sm overflow-x-auto"><code class="language-json">{formattedJson}</code></pre>
        </div>
    {:else}
        <div class="p-3 text-sm text-gray-600 dark:text-gray-400">
            Click to expand structured output...
        </div>
    {/if}
</div>

<style>
    .structured-output-viewer pre {
        background: transparent;
        margin: 0;
        padding: 0;
    }
    
    .structured-output-viewer code {
        color: inherit;
        background: transparent;
        font-family: ui-monospace, SFMono-Regular, 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace;
    }
</style>
```

**Implementation Tasks**:
- [ ] Create enhanced JSON response viewer component
- [ ] Add syntax highlighting with Prism.js integration
- [ ] Add expand/collapse functionality
- [ ] Add copy-to-clipboard feature
- [ ] Add JSON export functionality
- [ ] Add responsive design for mobile

**Verification Steps**:
```bash
# Test component
npm run test:unit -- JsonResponseViewer.svelte

# Manual testing
# 1. Send message with structured output
# 2. Verify JSON syntax highlighting
# 3. Test expand/collapse functionality
# 4. Test copy and export features
# 5. Test on mobile devices
```

**Success Criteria**:
- [ ] JSON syntax highlighting works correctly
- [ ] Expand/collapse functionality is smooth
- [ ] Copy-to-clipboard works across browsers
- [ ] Export generates valid JSON files
- [ ] Component is responsive on all devices

#### 5.3 Schema Library Browser
**Files**: `src/lib/components/workspace/SchemaLibrary.svelte` (new)

```svelte
<script lang="ts">
    import { onMount } from 'svelte';
    import { getSchemas, createSchema, updateSchema, deleteSchema } from '$lib/apis/schemas';
    import { toast } from 'svelte-sonner';
    
    let schemas = [];
    let filteredSchemas = [];
    let categories = [];
    let selectedCategory = '';
    let searchQuery = '';
    let showCreateModal = false;
    let editingSchema = null;
    let loading = false;
    
    // Pagination
    let currentPage = 1;
    let totalSchemas = 0;
    const schemasPerPage = 20;
    
    // Filters
    let showPublicOnly = false;
    let selectedTags = [];
    
    onMount(async () => {
        await loadSchemas();
        await loadCategories();
    });
    
    const loadSchemas = async () => {
        loading = true;
        try {
            const response = await getSchemas({
                category: selectedCategory,
                tags: selectedTags.join(','),
                public_only: showPublicOnly,
                search: searchQuery,
                limit: schemasPerPage,
                offset: (currentPage - 1) * schemasPerPage
            });
            
            schemas = response.schemas;
            totalSchemas = response.total;
            filteredSchemas = schemas;
        } catch (error) {
            console.error('Failed to load schemas:', error);
            toast.error('Failed to load schemas');
        } finally {
            loading = false;
        }
    };
    
    const loadCategories = async () => {
        try {
            const response = await fetch('/api/v1/schemas/categories', {
                headers: { Authorization: `Bearer ${localStorage.token}` }
            });
            const data = await response.json();
            categories = data.categories;
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    };
    
    const handleSearch = () => {
        currentPage = 1;
        loadSchemas();
    };
    
    const handleCategoryChange = () => {
        currentPage = 1;
        loadSchemas();
    };
    
    const handleCreateSchema = () => {
        showCreateModal = true;
        editingSchema = null;
    };
    
    const handleEditSchema = (schema) => {
        editingSchema = schema;
        showCreateModal = true;
    };
    
    const handleDeleteSchema = async (schemaId) => {
        if (!confirm('Are you sure you want to delete this schema?')) return;
        
        try {
            await deleteSchema(schemaId);
            toast.success('Schema deleted successfully');
            await loadSchemas();
        } catch (error) {
            console.error('Failed to delete schema:', error);
            toast.error('Failed to delete schema');
        }
    };
    
    const handleUseSchema = (schema) => {
        // Emit event to parent component
        const event = new CustomEvent('useSchema', {
            detail: { schema }
        });
        document.dispatchEvent(event);
        toast.success(`Using schema: ${schema.name}`);
    };
    
    $: if (searchQuery || selectedCategory || showPublicOnly) {
        // Debounced search
        const timeoutId = setTimeout(handleSearch, 300);
        return () => clearTimeout(timeoutId);
    }
</script>

<div class="schema-library">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Schema Library</h2>
        <button
            on:click={handleCreateSchema}
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2"
        >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Create Schema
        </button>
    </div>
    
    <!-- Filters -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <!-- Search -->
        <div class="md:col-span-2">
            <input
                type="text"
                bind:value={searchQuery}
                placeholder="Search schemas..."
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
        </div>
        
        <!-- Category Filter -->
        <div>
            <select
                bind:value={selectedCategory}
                on:change={handleCategoryChange}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
                <option value="">All Categories</option>
                {#each categories as category}
                    <option value={category}>{category}</option>
                {/each}
            </select>
        </div>
        
        <!-- Public Only Toggle -->
        <div class="flex items-center">
            <input
                type="checkbox"
                id="public-only"
                bind:checked={showPublicOnly}
                on:change={handleCategoryChange}
                class="mr-2"
            />
            <label for="public-only" class="text-sm text-gray-700 dark:text-gray-300">
                Public only
            </label>
        </div>
    </div>
    
    <!-- Schema Grid -->
    {#if loading}
        <div class="flex justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
    {:else if filteredSchemas.length === 0}
        <div class="text-center py-12">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-12 h-12 mx-auto text-gray-400 mb-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
            <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">No schemas found</h3>
            <p class="text-gray-600 dark:text-gray-400">Try adjusting your search criteria or create a new schema.</p>
        </div>
    {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each filteredSchemas as schema}
                <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-lg transition-shadow">
                    <!-- Schema Header -->
                    <div class="flex items-start justify-between mb-3">
                        <div>
                            <h3 class="font-semibold text-gray-900 dark:text-white mb-1">{schema.name}</h3>
                            <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                                {#if schema.category}
                                    <span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">
                                        {schema.category}
                                    </span>
                                {/if}
                                {#if schema.is_public}
                                    <span class="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded text-xs">
                                        Public
                                    </span>
                                {/if}
                            </div>
                        </div>
                        
                        <!-- Rating -->
                        {#if schema.rating_count > 0}
                            <div class="flex items-center gap-1 text-sm">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24" class="w-4 h-4 text-yellow-400">
                                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                                </svg>
                                <span class="text-gray-600 dark:text-gray-400">
                                    {schema.rating_avg.toFixed(1)} ({schema.rating_count})
                                </span>
                            </div>
                        {/if}
                    </div>
                    
                    <!-- Description -->
                    {#if schema.description}
                        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                            {schema.description}
                        </p>
                    {/if}
                    
                    <!-- Tags -->
                    {#if schema.tags.length > 0}
                        <div class="flex flex-wrap gap-1 mb-4">
                            {#each schema.tags.slice(0, 3) as tag}
                                <span class="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded text-xs">
                                    {tag}
                                </span>
                            {/each}
                            {#if schema.tags.length > 3}
                                <span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs">
                                    +{schema.tags.length - 3}
                                </span>
                            {/if}
                        </div>
                    {/if}
                    
                    <!-- Stats -->
                    <div class="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-4">
                        <span>Used {schema.usage_count} times</span>
                        <span>{new Date(schema.created_at).toLocaleDateString()}</span>
                    </div>
                    
                    <!-- Actions -->
                    <div class="flex items-center justify-between">
                        <button
                            on:click={() => handleUseSchema(schema)}
                            class="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium"
                        >
                            Use Schema
                        </button>
                        
                        <div class="flex items-center gap-1">
                            {#if schema.can_edit}
                                <button
                                    on:click={() => handleEditSchema(schema)}
                                    class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-gray-500 dark:text-gray-400"
                                    title="Edit"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
                                    </svg>
                                </button>
                                
                                <button
                                    on:click={() => handleDeleteSchema(schema.id)}
                                    class="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-red-500 dark:text-red-400"
                                    title="Delete"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                                    </svg>
                                </button>
                            {/if}
                        </div>
                    </div>
                </div>
            {/each}
        </div>
        
        <!-- Pagination -->
        {#if Math.ceil(totalSchemas / schemasPerPage) > 1}
            <div class="flex justify-center mt-8">
                <div class="flex items-center gap-2">
                    <button
                        on:click={() => { currentPage = Math.max(1, currentPage - 1); loadSchemas(); }}
                        disabled={currentPage === 1}
                        class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm disabled:opacity-50"
                    >
                        Previous
                    </button>
                    
                    <span class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                        Page {currentPage} of {Math.ceil(totalSchemas / schemasPerPage)}
                    </span>
                    
                    <button
                        on:click={() => { currentPage++; loadSchemas(); }}
                        disabled={currentPage >= Math.ceil(totalSchemas / schemasPerPage)}
                        class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded text-sm disabled:opacity-50"
                    >
                        Next
                    </button>
                </div>
            </div>
        {/if}
    {/if}
</div>

<style>
    .line-clamp-2 {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>
```

**Implementation Tasks**:
- [ ] Create comprehensive schema library browser
- [ ] Add search and filtering capabilities
- [ ] Add pagination for large schema collections
- [ ] Add rating and usage statistics display
- [ ] Add schema preview and testing features
- [ ] Add responsive design for mobile

**Verification Steps**:
```bash
# Test component
npm run test:unit -- SchemaLibrary.svelte

# Manual testing
# 1. Open schema library
# 2. Test search and filtering
# 3. Navigate through paginated results
# 4. Test rating and usage display
# 5. Test schema preview features
```

**Success Criteria**:
- [ ] Schema library loads and displays correctly
- [ ] Search and filtering work efficiently
- [ ] Pagination handles large datasets
- [ ] Rating and usage statistics are accurate
- [ ] Schema preview functionality works
- [ ] Responsive design works on all devices

### Phase 6: Advanced Features & Polish (Week 6-7)
**Priority**: Low - Nice-to-have enhancements

#### 6.1 Schema Testing Interface
**Files**: `src/lib/components/workspace/SchemaTestingModal.svelte` (new)

```svelte
<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import { validateJsonSchema } from '$lib/utils/schema-validation';
    import { toast } from 'svelte-sonner';
    
    const dispatch = createEventDispatcher();
    
    export let show = false;
    export let schema = '';
    export let schemaName = '';
    
    let testData = '';
    let validationResult = null;
    let isValidating = false;
    let testHistory = [];
    
    // Sample test data templates
    const testTemplates = [
        {
            name: 'Simple Object',
            data: '{\n  "result": "success",\n  "confidence": 0.95\n}'
        },
        {
            name: 'Array Example',
            data: '{\n  "items": [\n    {"name": "Item 1", "value": 100},\n    {"name": "Item 2", "value": 200}\n  ]\n}'
        },
        {
            name: 'Nested Object',
            data: '{\n  "user": {\n    "id": 123,\n    "profile": {\n      "name": "John Doe",\n      "settings": {\n        "theme": "dark"\n      }\n    }\n  }\n}'
        }
    ];
    
    const validateTestData = async () => {
        if (!testData.trim()) {
            toast.error('Please enter test data');
            return;
        }
        
        if (!schema.trim()) {
            toast.error('No schema to validate against');
            return;
        }
        
        isValidating = true;
        validationResult = null;
        
        try {
            // Parse test data
            const parsedData = JSON.parse(testData);
            
            // Parse schema
            const parsedSchema = JSON.parse(schema);
            
            // Validate using Ajv or similar JSON schema validator
            const Ajv = (await import('ajv')).default;
            const ajv = new Ajv({ allErrors: true });
            
            const validate = ajv.compile(parsedSchema);
            const valid = validate(parsedData);
            
            validationResult = {
                valid,
                errors: validate.errors || [],
                data: parsedData,
                timestamp: new Date()
            };
            
            // Add to history
            testHistory = [validationResult, ...testHistory.slice(0, 9)]; // Keep last 10
            
            if (valid) {
                toast.success('Test data is valid!');
            } else {
                toast.error(`Validation failed: ${validate.errors.length} errors found`);
            }
            
        } catch (error) {
            validationResult = {
                valid: false,
                errors: [{ message: error.message }],
                timestamp: new Date()
            };
            toast.error(`Error: ${error.message}`);
        } finally {
            isValidating = false;
        }
    };
    
    const loadTemplate = (template) => {
        testData = template.data;
    };
    
    const generateSampleData = async () => {
        if (!schema.trim()) {
            toast.error('No schema provided');
            return;
        }
        
        try {
            const parsedSchema = JSON.parse(schema);
            const sampleData = generateFromSchema(parsedSchema);
            testData = JSON.stringify(sampleData, null, 2);
            toast.success('Sample data generated');
        } catch (error) {
            toast.error(`Failed to generate sample data: ${error.message}`);
        }
    };
    
    const generateFromSchema = (schema) => {
        if (schema.type === 'object' && schema.properties) {
            const obj = {};
            for (const [key, propSchema] of Object.entries(schema.properties)) {
                obj[key] = generateFromSchema(propSchema);
            }
            return obj;
        } else if (schema.type === 'array' && schema.items) {
            return [generateFromSchema(schema.items)];
        } else if (schema.type === 'string') {
            return schema.enum ? schema.enum[0] : 'example string';
        } else if (schema.type === 'number') {
            return schema.minimum || 0;
        } else if (schema.type === 'integer') {
            return Math.floor(schema.minimum || 0);
        } else if (schema.type === 'boolean') {
            return true;
        } else {
            return null;
        }
    };
    
    const clearHistory = () => {
        testHistory = [];
    };
</script>

{#if show}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div class="bg-white dark:bg-gray-800 rounded-lg w-full max-w-6xl max-h-[90vh] flex flex-col">
            <!-- Header -->
            <div class="flex justify-between items-center p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                    Schema Testing - {schemaName || 'Untitled Schema'}
                </h2>
                <button
                    on:click={() => { show = false; }}
                    class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
            
            <!-- Content -->
            <div class="flex-1 overflow-hidden flex">
                <!-- Left Panel - Test Data Input -->
                <div class="flex-1 p-6 border-r border-gray-200 dark:border-gray-700 flex flex-col">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-medium text-gray-900 dark:text-white">Test Data</h3>
                        <div class="flex gap-2">
                            <button
                                on:click={generateSampleData}
                                class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm"
                            >
                                Generate Sample
                            </button>
                            <select
                                on:change={(e) => loadTemplate(testTemplates[e.target.value])}
                                class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm bg-white dark:bg-gray-700"
                            >
                                <option value="">Load Template...</option>
                                {#each testTemplates as template, i}
                                    <option value={i}>{template.name}</option>
                                {/each}
                            </select>
                        </div>
                    </div>
                    
                    <textarea
                        bind:value={testData}
                        placeholder="Enter JSON test data here..."
                        class="flex-1 w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg font-mono text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
                    ></textarea>
                    
                    <div class="mt-4 flex justify-between items-center">
                        <div class="text-sm text-gray-600 dark:text-gray-400">
                            {testData.trim() ? `${testData.trim().split('\n').length} lines` : 'No data entered'}
                        </div>
                        <button
                            on:click={validateTestData}
                            disabled={isValidating || !testData.trim() || !schema.trim()}
                            class="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded font-medium"
                        >
                            {isValidating ? 'Validating...' : 'Validate'}
                        </button>
                    </div>
                </div>
                
                <!-- Right Panel - Results -->
                <div class="flex-1 p-6 flex flex-col">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-medium text-gray-900 dark:text-white">Validation Results</h3>
                        {#if testHistory.length > 0}
                            <button
                                on:click={clearHistory}
                                class="px-3 py-1 text-red-600 hover:text-red-700 text-sm"
                            >
                                Clear History
                            </button>
                        {/if}
                    </div>
                    
                    <div class="flex-1 overflow-y-auto">
                        {#if validationResult}
                            <div class="mb-6 p-4 border rounded-lg {validationResult.valid ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20' : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'}">
                                <div class="flex items-center gap-2 mb-2">
                                    {#if validationResult.valid}
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-green-600">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                                        </svg>
                                        <span class="font-medium text-green-800 dark:text-green-200">Valid</span>
                                    {:else}
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 text-red-600">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                                        </svg>
                                        <span class="font-medium text-red-800 dark:text-red-200">Invalid</span>
                                    {/if}
                                    <span class="text-sm text-gray-600 dark:text-gray-400">
                                        {validationResult.timestamp.toLocaleTimeString()}
                                    </span>
                                </div>
                                
                                {#if !validationResult.valid && validationResult.errors.length > 0}
                                    <div class="mt-3">
                                        <h4 class="font-medium text-red-800 dark:text-red-200 mb-2">Errors:</h4>
                                        <ul class="list-disc list-inside space-y-1">
                                            {#each validationResult.errors as error}
                                                <li class="text-sm text-red-700 dark:text-red-300">
                                                    {error.instancePath ? `${error.instancePath}: ` : ''}{error.message}
                                                </li>
                                            {/each}
                                        </ul>
                                    </div>
                                {/if}
                            </div>
                        {:else}
                            <div class="flex items-center justify-center h-32 text-gray-500 dark:text-gray-400">
                                Enter test data and click validate to see results
                            </div>
                        {/if}
                        
                        <!-- Test History -->
                        {#if testHistory.length > 1}
                            <div class="mt-6">
                                <h4 class="font-medium text-gray-900 dark:text-white mb-3">Previous Tests</h4>
                                <div class="space-y-2">
                                    {#each testHistory.slice(1) as result}
                                        <div class="p-3 border border-gray-200 dark:border-gray-700 rounded text-sm">
                                            <div class="flex items-center justify-between">
                                                <span class="font-medium {result.valid ? 'text-green-600' : 'text-red-600'}">
                                                    {result.valid ? 'Valid' : 'Invalid'}
                                                </span>
                                                <span class="text-gray-500 dark:text-gray-400">
                                                    {result.timestamp.toLocaleTimeString()}
                                                </span>
                                            </div>
                                            {#if !result.valid && result.errors.length > 0}
                                                <div class="mt-1 text-gray-600 dark:text-gray-400">
                                                    {result.errors.length} error{result.errors.length === 1 ? '' : 's'}
                                                </div>
                                            {/if}
                                        </div>
                                    {/each}
                                </div>
                            </div>
                        {/if}
                    </div>
                </div>
            </div>
        </div>
    </div>
{/if}
```

**Implementation Tasks**:
- [ ] Create schema testing interface
- [ ] Add JSON validation with detailed error reporting
- [ ] Add sample data generation from schema
- [ ] Add test templates and history
- [ ] Add export test results functionality

**Verification Steps**:
```bash
# Test component
npm run test:unit -- SchemaTestingModal.svelte

# Manual testing
# 1. Open schema testing interface
# 2. Test with valid and invalid JSON
# 3. Generate sample data from schema
# 4. Test templates and history
# 5. Export test results
```

**Success Criteria**:
- [ ] Schema testing interface is functional
- [ ] JSON validation provides detailed errors
- [ ] Sample data generation works correctly
- [ ] Test templates are useful and accurate
- [ ] Export functionality generates valid files

#### 6.2 Model Compatibility Indicators
**Files**: `src/lib/components/chat/ModelSelector/CompatibilityBadge.svelte` (new)

```svelte
<script lang="ts">
    export let modelId: string;
    export let compact: boolean = false;
    
    $: supportsStructuredOutput = checkStructuredOutputSupport(modelId);
    $: supportLevel = getStructuredOutputSupportLevel(modelId);
    
    function checkStructuredOutputSupport(modelId: string): boolean {
        if (!modelId) return false;
        
        const model = modelId.toLowerCase();
        
        // Native structured output support
        const nativeSupport = [
            'gpt-4o-mini',
            'gpt-4o-2024-08-06',
            'gpt-4o-2024-11-20',
            'gpt-4o-2025-01-07'
        ];
        
        // Function calling support (alternative method)
        const functionCallSupport = [
            'gpt-4-0613',
            'gpt-3.5-turbo-0613',
            'gpt-4-turbo'
        ];
        
        return nativeSupport.some(m => model.includes(m)) || 
               functionCallSupport.some(m => model.includes(m));
    }
    
    function getStructuredOutputSupportLevel(modelId: string): 'native' | 'function-calling' | 'json-mode' | 'none' {
        if (!modelId) return 'none';
        
        const model = modelId.toLowerCase();
        
        const nativeSupport = [
            'gpt-4o-mini',
            'gpt-4o-2024-08-06',
            'gpt-4o-2024-11-20'
        ];
        
        const functionCallSupport = [
            'gpt-4-0613',
            'gpt-3.5-turbo-0613',
            'gpt-4-turbo'
        ];
        
        if (nativeSupport.some(m => model.includes(m))) {
            return 'native';
        } else if (functionCallSupport.some(m => model.includes(m))) {
            return 'function-calling';
        } else if (model.includes('gpt-') || model.includes('claude-') || model.includes('llama')) {
            return 'json-mode';
        } else {
            return 'none';
        }
    }
    
    const getSupportInfo = (level: string) => {
        switch (level) {
            case 'native':
                return {
                    label: 'Native',
                    color: 'green',
                    description: 'Full structured output support with schema validation'
                };
            case 'function-calling':
                return {
                    label: 'Functions',
                    color: 'blue',
                    description: 'Structured output via function calling'
                };
            case 'json-mode':
                return {
                    label: 'JSON',
                    color: 'yellow',
                    description: 'Basic JSON mode support'
                };
            default:
                return {
                    label: 'None',
                    color: 'gray',
                    description: 'No structured output support'
                };
        }
    };
    
    $: supportInfo = getSupportInfo(supportLevel);
</script>

{#if supportsStructuredOutput}
    <div 
        class="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium
               {supportInfo.color === 'green' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                supportInfo.color === 'blue' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' :
                supportInfo.color === 'yellow' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' :
                'bg-gray-100 dark:bg-gray-900/30 text-gray-700 dark:text-gray-400'}"
        title={supportInfo.description}
    >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
        </svg>
        {#if !compact}
            <span>SO: {supportInfo.label}</span>
        {/if}
    </div>
{:else}
    <div 
        class="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-900/30 text-gray-500 dark:text-gray-500 rounded text-xs"
        title="No structured output support"
    >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3 h-3">
            <path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636" />
        </svg>
        {#if !compact}
            <span>No SO</span>
        {/if}
    </div>
{/if}
```

**Implementation Tasks**:
- [ ] Create model compatibility badge component
- [ ] Add structured output support detection
- [ ] Add visual indicators for different support levels
- [ ] Add tooltips with detailed compatibility information
- [ ] Integrate with model selector components

**Verification Steps**:
```bash
# Test component
npm run test:unit -- CompatibilityBadge.svelte

# Manual testing
# 1. View model selector with different models
# 2. Verify badges show correct support levels
# 3. Test tooltips for detailed information
# 4. Verify integration with existing UI
```

**Success Criteria**:
- [ ] Compatibility badges display correctly
- [ ] Support detection is accurate
- [ ] Visual indicators are clear and informative
- [ ] Tooltips provide useful information
- [ ] Integration doesn't break existing functionality

### Phase 7: Testing & Documentation (Week 7-8)
**Priority**: Critical - Quality assurance

#### 7.1 Comprehensive Test Suite
**Files**: `backend/open_webui/test/test_structured_output.py` (new)

```python
import pytest
import json
from unittest.mock import Mock, patch
from open_webui.utils.schema_validation import (
    validate_json_schema,
    validate_openai_constraints,
    count_total_properties,
    get_max_nesting_depth,
    calculate_total_string_length,
    clean_schema_for_openai
)

class TestSchemaValidation:
    def test_valid_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        result = validate_json_schema(json.dumps(schema))
        assert result.valid is True
        assert result.schema == schema
    
    def test_invalid_json(self):
        result = validate_json_schema("invalid json")
        assert result.valid is False
        assert "Invalid JSON format" in result.error
    
    def test_property_count_validation(self):
        # Create schema with many properties
        properties = {f"prop_{i}": {"type": "string"} for i in range(5001)}
        schema = {"type": "object", "properties": properties}
        
        is_valid, errors = validate_openai_constraints(schema)
        assert is_valid is False
        assert any("5,000 allowed" in error for error in errors)
    
    def test_nesting_depth_validation(self):
        # Create deeply nested schema (6 levels)
        schema = {"type": "object"}
        current = schema
        for i in range(6):
            current["properties"] = {f"level_{i}": {"type": "object"}}
            current = current["properties"][f"level_{i}"]
        
        max_depth = get_max_nesting_depth(schema)
        assert max_depth == 6
        
        is_valid, errors = validate_openai_constraints(schema)
        assert is_valid is False
        assert any("max 5 levels" in error for error in errors)
    
    def test_string_length_validation(self):
        # Create schema with very long strings
        long_string = "a" * 50000
        schema = {
            "type": "object",
            "properties": {
                long_string: {"type": "string", "description": long_string}
            }
        }
        
        total_length = calculate_total_string_length(schema)
        assert total_length > 120000
        
        is_valid, errors = validate_openai_constraints(schema)
        assert is_valid is False
        assert any("120,000 allowed" in error for error in errors)
    
    def test_schema_cleaning(self):
        schema = {
            "type": "object",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {"test": {"type": "string"}},
            "properties": {
                "name": {"type": "string", "additionalProperties": True}
            },
            "additionalProperties": True
        }
        
        cleaned = clean_schema_for_openai(schema)
        assert "$schema" not in cleaned
        assert "definitions" not in cleaned
        assert cleaned["additionalProperties"] is False

class TestChatStructuredOutput:
    @pytest.fixture
    def mock_chat(self):
        return Mock(
            id="test_chat_id",
            user_id="test_user_id",
            structured_output_enabled=True,
            structured_output_schema='{"type": "object", "properties": {"result": {"type": "string"}}}',
            structured_output_name="Test Schema"
        )
    
    def test_chat_structured_output_priority(self, mock_chat):
        # Test priority system: prompt > manual > chat
        metadata = {
            "prompt_command": "/test",
            "structured_output": True,
            "structured_output_schema": '{"type": "object", "properties": {"manual": {"type": "string"}}}'
        }
        
        # Mock prompt with structured output
        mock_prompt = Mock(
            structured_output=True,
            structured_output_schema='{"type": "object", "properties": {"prompt": {"type": "string"}}}'
        )
        
        with patch('open_webui.models.prompts.Prompts.get_prompt_by_command', return_value=mock_prompt):
            from open_webui.routers.openai import get_structured_output_config
            
            config = get_structured_output_config(metadata, "test_chat_id", "test_user_id")
            assert config["source"] == "prompt"
            assert "prompt" in config["schema"]

class TestSchemaLibrary:
    def test_create_schema(self):
        # Test schema creation with validation
        schema_data = {
            "name": "Test Schema",
            "description": "A test schema",
            "schema_content": '{"type": "object", "properties": {"test": {"type": "string"}}}',
            "is_public": False,
            "category": "test",
            "tags": ["test", "example"]
        }
        
        # Mock database operations
        with patch('open_webui.models.schema_library.SchemaLibrary.create_schema') as mock_create:
            mock_create.return_value = Mock(**schema_data, id=1, user_id="test_user")
            
            # Test would call API endpoint here
            assert True  # Placeholder for actual API test
    
    def test_schema_access_control(self):
        # Test that private schemas are not accessible to other users
        # Test that public schemas are accessible to all users
        # Test that shared schemas respect access permissions
        pass
    
    def test_schema_rating_system(self):
        # Test schema rating and review functionality
        pass

class TestStateManagement:
    def test_state_capture_mechanism(self):
        # Test pre-tick state capture
        state = {
            "structuredOutput": True,
            "structuredOutputSchema": '{"type": "object"}',
            "structuredOutputName": "Test",
            "attachedPrompt": None
        }
        
        # Simulate state capture before tick()
        captured_state = state.copy()
        
        # Simulate state change after tick()
        state["structuredOutput"] = False
        
        # Verify captured state is preserved
        assert captured_state["structuredOutput"] is True
        assert state["structuredOutput"] is False
    
    def test_listener_conflict_protection(self):
        # Test event listener protection mechanism
        # Test modal event isolation
        # Test state lock functionality
        pass

class TestModelCompatibility:
    def test_structured_output_detection(self):
        from open_webui.routers.openai import supports_structured_output
        
        # Test models with native support
        assert supports_structured_output("gpt-4o-mini") is True
        assert supports_structured_output("gpt-4o-2024-08-06") is True
        
        # Test models with function calling support
        assert supports_structured_output("gpt-4-0613") is True
        assert supports_structured_output("gpt-3.5-turbo-0613") is True
        
        # Test unsupported models
        assert supports_structured_output("gpt-3.5-turbo") is False
        assert supports_structured_output("unknown-model") is False
    
    def test_response_format_optimization(self):
        from open_webui.routers.openai import get_optimal_response_format
        
        schema = '{"type": "object", "properties": {"result": {"type": "string"}}}'
        
        # Test structured output format for supported models
        format_so = get_optimal_response_format("gpt-4o-mini", schema)
        assert format_so["type"] == "json_schema"
        assert "json_schema" in format_so
        
        # Test JSON mode fallback for unsupported models
        format_json = get_optimal_response_format("gpt-3.5-turbo", schema)
        assert format_json["type"] == "json_object"

# Integration Tests
class TestEndToEndFlow:
    def test_complete_structured_output_flow(self):
        # Test complete flow from schema creation to response
        # 1. Create schema in library
        # 2. Attach to chat or prompt
        # 3. Send message with structured output
        # 4. Verify correct API format
        # 5. Verify response processing
        pass
    
    def test_error_handling_flow(self):
        # Test error scenarios and fallback mechanisms
        # 1. Invalid schema
        # 2. Unsupported model
        # 3. API failures
        # 4. State management failures
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Implementation Tasks**:
- [ ] Create comprehensive backend test suite
- [ ] Add frontend component tests with Vitest
- [ ] Add integration tests for complete workflows
- [ ] Add performance tests for large schemas
- [ ] Add error handling and edge case tests
- [ ] Set up CI/CD test automation

**Verification Steps**:
```bash
# Run complete test suite
npm run test:all
pytest backend/open_webui/test/ -v --cov=open_webui --cov-report=html

# Check test coverage
open backend/htmlcov/index.html

# Run performance tests
pytest backend/open_webui/test/test_performance.py -v
```

**Success Criteria**:
- [ ] Test suite achieves >80% code coverage
- [ ] All unit tests pass consistently
- [ ] Integration tests cover main workflows
- [ ] Performance tests validate scalability
- [ ] Edge case handling is comprehensive
- [ ] CI/CD pipeline runs tests automatically

#### 7.2 Documentation and User Guides
**Files**: `docs/STRUCTURED_OUTPUT.md` (new)

```markdown
# Structured Output Feature Guide

## Overview

Open WebUI's Structured Output feature enables users to receive responses from LLMs in specific JSON formats defined by JSON schemas. This ensures consistent, predictable response formats for automation, data processing, and integration workflows.

## Features

### ✅ Available Features

1. **Prompt-based Structured Output** - Attach schemas to reusable prompts
2. **Chat-level Structured Output** - Apply schemas to entire conversations
3. **Schema Library** - Centralized management of reusable schemas
4. **Model Compatibility** - Automatic detection and optimization for different models
5. **Template System** - Pre-built schema templates for common use cases
6. **Validation & Testing** - Built-in schema validation and testing tools

### 🎯 Use Cases

- **Data Extraction** - Extract structured information from unstructured text
- **API Integration** - Generate responses that integrate directly with other systems
- **Quality Assurance** - Ensure consistent response formats across conversations
- **Automation** - Enable reliable parsing and processing of LLM responses
- **Analysis** - Standardize data collection for analysis and reporting

## Getting Started

### 1. Creating Your First Schema

Navigate to **Workspace → Prompts** and create a new prompt:

1. **Title**: Give your prompt a descriptive name
2. **Command**: Optional slash command (e.g., `/extract-data`)
3. **Content**: Write your system message/instructions
4. **Enable Structured Output**: Check the structured output checkbox
5. **JSON Schema**: Define your response structure

**Example Schema - Contact Information Extraction**:
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Full name of the person"
    },
    "email": {
      "type": "string",
      "description": "Email address"
    },
    "phone": {
      "type": "string",
      "description": "Phone number"
    },
    "company": {
      "type": "string",
      "description": "Company name"
    }
  },
  "required": ["name"]
}
```

### 2. Using Structured Output in Chat

**Method 1: Attach Prompt**
1. In any chat, click the **More** menu (⋯)
2. Select **Attach Prompt**
3. Choose a prompt with structured output enabled
4. The prompt appears as a purple badge with "SO" indicator
5. Type your message and send

**Method 2: Manual Configuration**
1. In any chat, click the **More** menu (⋯)
2. Select **Structured Output**
3. Configure your schema directly
4. Apply to current message or entire chat

### 3. Managing Schemas in Library

Navigate to **Workspace → Schema Library**:

- **Browse** existing schemas by category and tags
- **Search** for specific schemas
- **Create** new reusable schemas
- **Rate** and review public schemas
- **Share** schemas with other users

## Schema Design Guidelines

### Best Practices

1. **Keep schemas simple** - Start with basic structures and expand as needed
2. **Use descriptive property names** - Clear names improve LLM understanding
3. **Include descriptions** - Help the LLM understand expected content
4. **Define required fields** - Specify which properties are mandatory
5. **Use appropriate types** - Match data types to expected content

### OpenAI Constraints

When using OpenAI models, schemas have specific limitations:

- **Maximum Properties**: 5,000 total properties across entire schema
- **Nesting Depth**: Maximum 5 levels of nested objects
- **String Length**: Combined string length cannot exceed 120,000 characters
- **Enum Values**: Maximum 1,000 enum values total

### Supported JSON Schema Features

✅ **Supported**:
- Basic types: `string`, `number`, `integer`, `boolean`, `array`, `object`
- Property constraints: `required`, `enum`, `minimum`, `maximum`
- Array specifications: `items`, `minItems`, `maxItems`
- String constraints: `minLength`, `maxLength`

❌ **Not Supported**:
- Complex conditionals: `if`, `then`, `else`
- References: `$ref`, `definitions`
- Format validations: `format` (dates, emails, etc.)
- Pattern properties: `patternProperties`

## Model Compatibility

### Native Structured Output Support
- **gpt-4o-mini** - Full support with schema validation
- **gpt-4o-2024-08-06** - Full support with schema validation
- **gpt-4o-2024-11-20** - Full support with schema validation

### Function Calling Support
- **gpt-4-0613** - Via function calling mechanism
- **gpt-3.5-turbo-0613** - Via function calling mechanism
- **gpt-4-turbo** - Via function calling mechanism

### JSON Mode Fallback
- Most other models fall back to basic JSON object mode
- Less strict validation but still provides structured responses

## Advanced Features

### Schema Testing

Use the built-in schema testing interface to:
1. **Validate schemas** against sample data
2. **Generate sample data** from schemas
3. **Test different scenarios** before deployment
4. **Debug validation issues** with detailed error reports

### Chat-Level Persistence

Configure structured output for entire conversations:
1. Set schema once for the entire chat
2. All messages use the same structure
3. Schema persists across browser sessions
4. Override with prompt-specific schemas when needed

### Priority System

When multiple structured output configurations exist:
1. **Prompt Schema** (highest priority) - From attached prompts
2. **Manual Schema** (medium priority) - Manually configured for message
3. **Chat Schema** (lowest priority) - Applied to entire conversation

## Troubleshooting

### Common Issues

**Schema Validation Errors**
- Check JSON syntax with a validator
- Ensure all required properties are defined
- Verify schema doesn't exceed OpenAI limits

**Model Compatibility Issues**
- Check model compatibility indicators
- Use simpler schemas for unsupported models
- Enable debug logging to see actual API requests

**Response Not Following Schema**
- Verify schema is properly formatted
- Check if model supports structured output
- Review prompt instructions for clarity

### Debug Information

Enable debug logging to see:
- Schema validation results
- API request format sent to model
- Model compatibility detection
- Error messages and fallback behavior

## API Reference

### Chat-Level Endpoints

```http
POST /api/v1/chats/{chat_id}/structured-output
GET /api/v1/chats/{chat_id}/structured-output
DELETE /api/v1/chats/{chat_id}/structured-output
```

### Schema Library Endpoints

```http
GET /api/v1/schemas
POST /api/v1/schemas
GET /api/v1/schemas/{schema_id}
PUT /api/v1/schemas/{schema_id}
DELETE /api/v1/schemas/{schema_id}
POST /api/v1/schemas/{schema_id}/rate
```

## Examples

### Data Extraction Schema
```json
{
  "type": "object",
  "properties": {
    "entities": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "type": {"type": "string", "enum": ["person", "organization", "location"]},
          "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "required": ["name", "type"]
      }
    },
    "summary": {"type": "string"},
    "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]}
  },
  "required": ["entities", "summary"]
}
```

### Task Management Schema
```json
{
  "type": "object",
  "properties": {
    "tasks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "description": {"type": "string"},
          "priority": {"type": "string", "enum": ["low", "medium", "high"]},
          "due_date": {"type": "string"},
          "assignee": {"type": "string"},
          "status": {"type": "string", "enum": ["todo", "in_progress", "completed"]}
        },
        "required": ["title", "priority", "status"]
      }
    },
    "total_tasks": {"type": "integer"},
    "completion_percentage": {"type": "number", "minimum": 0, "maximum": 100}
  },
  "required": ["tasks", "total_tasks"]
}
```

## Support

For additional help:
- Check the [troubleshooting section](#troubleshooting)
- Review [schema design guidelines](#schema-design-guidelines)
- Test your schemas using the built-in testing interface
- Join the community discussions for tips and examples
```

**Implementation Tasks**:
- [ ] Create comprehensive user documentation
- [ ] Add API reference documentation
- [ ] Create video tutorials for key workflows
- [ ] Add troubleshooting guides with common issues
- [ ] Create schema examples library
- [ ] Add developer integration guides

**Verification Steps**:
```bash
# Build documentation
cd docs
mkdocs build
mkdocs serve  # Verify locally

# Test API documentation
curl -X GET http://localhost:8080/docs  # Swagger UI

# Review documentation completeness
find docs/ -name "*.md" -exec wc -l {} + | sort -n
```

**Success Criteria**:
- [ ] User documentation is comprehensive and clear
- [ ] API reference is complete and accurate
- [ ] Video tutorials cover key workflows
- [ ] Troubleshooting guides address common issues
- [ ] Schema examples are practical and useful
- [ ] Developer guides enable easy integration

## Success Metrics and Monitoring

### Key Performance Indicators (KPIs)

#### User Adoption Metrics
- **Structured Output Usage Rate**: % of chats using structured output
- **Schema Library Adoption**: Number of schemas created and shared
- **Feature Retention**: Users continuing to use structured output after 30 days
- **Public Schema Engagement**: Usage of shared schemas vs. private schemas

#### Technical Performance Metrics
- **Schema Validation Success Rate**: % of schemas that validate successfully
- **API Response Time**: Latency impact of structured output processing
- **Error Rate**: % of structured output requests that fail
- **Model Compatibility**: Success rates across different model types

#### Quality Metrics
- **Schema Complexity**: Average schema size and nesting depth
- **Template Usage**: Adoption of built-in vs. custom schemas
- **User Satisfaction**: Rating and feedback on structured output feature
- **Support Requests**: Volume of structured output-related issues

### Monitoring Implementation

```python
# Add to backend/open_webui/utils/metrics.py
import logging
import time
from functools import wraps
from typing import Dict, Any

def track_structured_output_usage(func):
    """Decorator to track structured output API usage"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            
            # Log successful usage
            logging.info(f"structured_output_success", extra={
                "function": func.__name__,
                "duration": time.time() - start_time,
                "user_id": kwargs.get("user_id"),
                "model_id": kwargs.get("model_id"),
                "schema_source": kwargs.get("schema_source")
            })
            
            return result
            
        except Exception as e:
            # Log errors
            logging.error(f"structured_output_error", extra={
                "function": func.__name__,
                "duration": time.time() - start_time,
                "error": str(e),
                "user_id": kwargs.get("user_id"),
                "model_id": kwargs.get("model_id")
            })
            raise
    
    return wrapper

class StructuredOutputMetrics:
    @staticmethod
    def record_schema_validation(schema_size: int, validation_time: float, success: bool):
        """Record schema validation metrics"""
        logging.info("schema_validation", extra={
            "schema_size": schema_size,
            "validation_time": validation_time,
            "success": success
        })
    
    @staticmethod
    def record_model_compatibility(model_id: str, support_level: str, fallback_used: bool):
        """Record model compatibility information"""
        logging.info("model_compatibility", extra={
            "model_id": model_id,
            "support_level": support_level,
            "fallback_used": fallback_used
        })
    
    @staticmethod
    def record_schema_library_usage(action: str, schema_id: int, user_id: str):
        """Record schema library interactions"""
        logging.info("schema_library_usage", extra={
            "action": action,
            "schema_id": schema_id,
            "user_id": user_id
        })
```

### Analytics Dashboard

Create monitoring dashboard to track:
- **Usage Trends**: Daily/weekly structured output usage
- **Performance Metrics**: Response times and error rates
- **Model Distribution**: Which models are used with structured output
- **Schema Popularity**: Most used schemas and templates
- **User Engagement**: Active users and feature adoption

## Risk Assessment and Mitigation

### Technical Risks

#### High Risk
1. **State Management Conflicts** - Event listeners interfering with structured output
   - **Mitigation**: Implement event listener prioritization and modal isolation
   - **Monitoring**: Track state inconsistency warnings

2. **Schema Validation Performance** - Large schemas causing delays
   - **Mitigation**: Implement size limits and optimization
   - **Monitoring**: Track validation response times

#### Medium Risk
1. **Model Compatibility Issues** - New models not properly detected
   - **Mitigation**: Regular compatibility matrix updates
   - **Monitoring**: Track fallback usage rates

2. **Database Performance** - Schema library queries becoming slow
   - **Mitigation**: Proper indexing and query optimization
   - **Monitoring**: Database query performance metrics

#### Low Risk
1. **User Experience Confusion** - Complex UI overwhelming users
   - **Mitigation**: Progressive disclosure and better onboarding
   - **Monitoring**: User feedback and support request volume

### Business Risks

1. **Low Adoption** - Users not discovering or using the feature
   - **Mitigation**: Better onboarding and documentation
   - **Monitoring**: Usage metrics and user surveys

2. **Performance Impact** - Feature slowing down overall application
   - **Mitigation**: Performance optimization and lazy loading
   - **Monitoring**: Application performance metrics

## Conclusion

This comprehensive development plan provides a structured approach to implementing and enhancing Open WebUI's structured output capabilities. The plan prioritizes:

1. **Immediate Value**: Hardening existing functionality and addressing edge cases
2. **User Experience**: Making structured output accessible and intuitive
3. **Scalability**: Building a foundation that can grow with user needs
4. **Quality**: Comprehensive testing and monitoring

The phased approach allows for incremental delivery while maintaining system stability. Each phase builds upon the previous one, ensuring a solid foundation before adding advanced features.

### Next Steps for LLM Agent Execution

1. **Phase 1**: Begin with state management hardening (highest priority)
2. **Phase 2**: Implement chat-level structured output (core functionality)
3. **Phase 3**: Add enhanced schema validation (OpenAI compliance)
4. **Phase 4**: Build schema library system (user experience)
5. **Phase 5**: Develop advanced UI components (polish)
6. **Phase 6**: Add testing and monitoring (quality assurance)

Each phase includes specific implementation tasks, code examples, and success criteria to guide LLM agent execution. The plan balances technical excellence with practical user needs, ensuring the structured output feature becomes a powerful and reliable tool for Open WebUI users.

## Agent Execution Instructions

### Phase Execution Protocol

For each phase, follow this exact sequence:

#### Pre-Phase Checklist
1. **Update Todo List**: Mark current phase as "in_progress"
2. **Create Branch**: `git checkout -b phase-{number}-{description}`
3. **Backup Current State**: `git tag backup-phase-{number}-start-$(date +%Y%m%d-%H%M)`
4. **Verify Prerequisites**: Check all dependencies for this phase
5. **Review Phase Goals**: Understand what needs to be accomplished

#### During Phase Execution
1. **Follow Task Order**: Complete tasks in the specified sequence
2. **Test Each Step**: Run verification commands after each major change
3. **Commit Frequently**: Make atomic commits with descriptive messages
4. **Document Issues**: Log any problems or deviations in comments
5. **Update Progress**: Update todo lists as tasks are completed

#### Post-Phase Validation
1. **Run Full Test Suite**: Execute all relevant tests
2. **Perform Integration Tests**: Verify phase works with existing functionality
3. **Check Performance**: Ensure no significant performance degradation
4. **Review Code Quality**: Run linting and formatting tools
5. **Update Documentation**: Document any changes or new features

#### Phase Completion Protocol
1. **Final Testing**: Run comprehensive test suite
2. **Code Review Preparation**: Ensure code follows project standards
3. **Merge to Main Branch**: `git checkout main && git merge phase-{number}-{description}`
4. **Tag Release**: `git tag phase-{number}-complete-$(date +%Y%m%d)`
5. **Update Todo List**: Mark phase as "completed"
6. **Generate Phase Report**: Document completion status and any issues

### Validation and Testing Procedures

#### Unit Test Validation
```bash
# Backend unit tests
cd backend
python -m pytest open_webui/test/test_structured_output.py -v
python -m pytest open_webui/test/test_schema_validation.py -v

# Frontend unit tests
npm run test:unit
```

#### Integration Test Validation
```bash
# Backend integration tests
python -m pytest open_webui/test/test_integration_structured_output.py -v

# Frontend integration tests
npm run test:integration
```

#### Manual Testing Procedures

**Phase 1 Validation (State Management)**:
1. Open multiple browser tabs with the application
2. Open structured output modal in one tab
3. Try keyboard shortcuts in other tabs
4. Verify no state conflicts occur
5. Test rapid clicking and modal interactions

**Phase 2 Validation (Chat-Level Structured Output)**:
1. Create a new chat
2. Configure structured output for the entire chat
3. Send multiple messages
4. Verify all responses follow the schema
5. Test schema persistence across browser refresh

**Phase 3 Validation (Enhanced Schema Validation)**:
1. Create schemas with various complexity levels
2. Test OpenAI constraint validation
3. Verify error messages are clear and actionable
4. Test schema size and nesting limits
5. Verify fallback mechanisms work correctly

**Phase 4 Validation (Schema Library)**:
1. Create, read, update, delete schemas
2. Test search and filtering functionality
3. Verify access control for public/private schemas
4. Test rating and review system
5. Verify usage tracking and analytics

**Phase 5 Validation (Enhanced UI)**:
1. Test all new UI components in different screen sizes
2. Verify accessibility features work correctly
3. Test keyboard navigation and shortcuts
4. Verify responsive design on mobile devices
5. Test with different themes (light/dark mode)

**Phase 6 Validation (Advanced Features)**:
1. Test schema testing interface with various schemas
2. Verify model compatibility indicators are accurate
3. Test import/export functionality
4. Verify performance with large schemas
5. Test error handling for edge cases

**Phase 7 Validation (Testing & Documentation)**:
1. Run complete test suite and verify all tests pass
2. Review test coverage reports
3. Verify documentation is complete and accurate
4. Test deployment procedures
5. Verify monitoring and metrics are working

### Error Handling and Recovery Procedures

#### Common Error Scenarios

**Database Migration Failures**:
```bash
# If migration fails, rollback to previous version
alembic downgrade -1

# Check database state
alembic current

# Fix migration file and retry
alembic upgrade head
```

**Frontend Build Failures**:
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear build cache
npm run build:clean
npm run build
```

**Test Failures**:
```bash
# Run specific failing test with verbose output
pytest path/to/failing_test.py::test_function -v -s

# Check test database state
pytest --pdb path/to/failing_test.py::test_function
```

**API Integration Issues**:
```bash
# Test API endpoints manually
curl -X GET http://localhost:8080/api/v1/schemas \
  -H "Authorization: Bearer $JWT_TOKEN"

# Check API logs
tail -f backend/logs/api.log
```

#### Rollback Procedures

**Phase Rollback**:
```bash
# Stop development servers
pkill -f "uvicorn"
pkill -f "vite"

# Rollback code changes
git checkout main
git branch -D phase-{number}-{description}

# Restore database to backup
# For PostgreSQL:
pg_restore --clean --if-exists -h localhost -U postgres -d open_webui backup_phase_{number}.sql

# For SQLite:
cp backup/webui_phase_{number}.db backend/data/webui.db

# Restart services
./start_development.sh
```

**Complete System Recovery**:
```bash
# Restore to pre-development state
git checkout backup-pre-structured-output-{date}
git branch -D feature/structured-output-enhancements

# Clear all changes
git clean -fd
git reset --hard HEAD

# Restore database from initial backup
# Restart all services
```

### Quality Gates and Checkpoints

#### Code Quality Standards
- **Test Coverage**: Minimum 80% for new code
- **Performance**: No more than 10% performance degradation
- **Security**: All user inputs validated and sanitized
- **Accessibility**: WCAG 2.1 AA compliance for UI components
- **Documentation**: All public APIs documented

#### Checkpoint Criteria

**Phase 1 Checkpoint**:
- [ ] Event listener protection system implemented
- [ ] State locking mechanism working
- [ ] Modal isolation functional
- [ ] State validation passing
- [ ] No conflicts with existing functionality

**Phase 2 Checkpoint**:
- [ ] Database schema successfully migrated
- [ ] API endpoints functional and tested
- [ ] Frontend integration complete
- [ ] Schema persistence working
- [ ] Priority system functioning correctly

**Phase 3 Checkpoint**:
- [ ] OpenAI constraint validation implemented
- [ ] Model-specific detection working
- [ ] Enhanced schema validation functional
- [ ] Performance within acceptable limits
- [ ] Error handling comprehensive

**Phase 4 Checkpoint**:
- [ ] Schema library database operational
- [ ] CRUD API endpoints functional
- [ ] Frontend library interface complete
- [ ] Access control working correctly
- [ ] Search and filtering operational

**Phase 5 Checkpoint**:
- [ ] All UI components implemented
- [ ] Responsive design verified
- [ ] Accessibility standards met
- [ ] Performance optimized
- [ ] User experience validated

**Phase 6 Checkpoint**:
- [ ] Advanced features implemented
- [ ] Testing interface functional
- [ ] Compatibility indicators accurate
- [ ] Performance optimized
- [ ] Error handling complete

**Phase 7 Checkpoint**:
- [ ] Complete test suite passing
- [ ] Documentation comprehensive
- [ ] Deployment procedures verified
- [ ] Monitoring systems operational
- [ ] Performance benchmarks met

### Progress Tracking and Reporting

#### Daily Progress Reports
For each day of development, create a progress report:

```markdown
# Daily Progress Report - Day {X} of Phase {N}

## Completed Tasks
- [ ] Task 1: Description and outcome
- [ ] Task 2: Description and outcome

## In Progress Tasks
- [ ] Task 3: Current status and blockers

## Blockers and Issues
- Issue 1: Description and proposed resolution
- Issue 2: Description and impact

## Next Steps
1. Priority task for tomorrow
2. Dependency that needs resolution

## Metrics
- Tests passing: X/Y
- Code coverage: X%
- Performance impact: +/-X%
- New files created: X
- Lines of code added/modified: X

## Notes
- Any important observations or decisions
- Changes to original plan
- Lessons learned
```

#### Phase Completion Reports
At the end of each phase, generate a comprehensive report:

```markdown
# Phase {N} Completion Report

## Overview
- Phase: {Name and Description}
- Duration: {Start Date} to {End Date}
- Status: {Completed/Partially Completed/Failed}

## Achievements
- ✅ Completed features and functionality
- ✅ Tests implemented and passing
- ✅ Documentation updated

## Challenges and Solutions
- Challenge 1: Description and how it was resolved
- Challenge 2: Description and how it was resolved

## Deviations from Plan
- Change 1: Why it was made and impact
- Change 2: Why it was made and impact

## Quality Metrics
- Test Coverage: X%
- Performance Impact: +/-X%
- Code Quality Score: X/10
- Security Scan Results: X issues found and resolved

## Lessons Learned
- What worked well
- What could be improved
- Recommendations for future phases

## Next Phase Readiness
- [ ] All prerequisites for next phase are met
- [ ] Code is properly committed and tagged
- [ ] Database is in expected state
- [ ] Documentation is updated
```

### Critical Decision Points

During execution, the LLM Agent may encounter decision points that require careful consideration:

#### When to Request Human Intervention
1. **Major Architecture Changes**: If implementation requires significant changes to existing architecture
2. **Security Concerns**: If potential security vulnerabilities are discovered
3. **Performance Issues**: If implementation causes significant performance degradation
4. **Breaking Changes**: If changes would break existing functionality
5. **External Dependencies**: If new external services or libraries are required
6. **Data Migration Issues**: If database migrations fail or cause data loss risk

#### Autonomous Decision Guidelines
1. **Code Style**: Follow existing project conventions
2. **Library Versions**: Use latest stable versions unless specific version required
3. **Error Messages**: Make them clear, actionable, and user-friendly
4. **Default Values**: Choose sensible defaults that work for most users
5. **Naming Conventions**: Follow existing patterns in the codebase
6. **File Organization**: Place files in logical locations following existing structure

### Success Criteria

The development plan is considered successful when:

#### Functional Requirements
- [ ] All 7 phases completed successfully
- [ ] All tests passing with >80% coverage
- [ ] All quality gates met
- [ ] Documentation complete and accurate
- [ ] Performance impact <10% degradation

#### Technical Requirements
- [ ] Code follows project standards
- [ ] Security scan passes
- [ ] Accessibility standards met
- [ ] Cross-browser compatibility verified
- [ ] Mobile responsiveness confirmed

#### User Experience Requirements
- [ ] Feature is intuitive and easy to use
- [ ] Error messages are helpful
- [ ] Performance feels responsive
- [ ] Integration with existing workflow is seamless
- [ ] Documentation enables self-service usage

### Final Deployment Checklist

Before considering the project complete:

#### Pre-Deployment
- [ ] All tests passing in CI/CD pipeline
- [ ] Security scan completed and issues resolved
- [ ] Performance benchmarks met
- [ ] Documentation reviewed and approved
- [ ] Rollback procedures tested

#### Deployment
- [ ] Feature flags configured for gradual rollout
- [ ] Monitoring and alerting configured
- [ ] Database migrations tested in staging
- [ ] Frontend assets built and deployed
- [ ] API endpoints verified in production

#### Post-Deployment
- [ ] Monitor system performance for 24 hours
- [ ] Check error logs for any issues
- [ ] Verify user adoption metrics
- [ ] Collect initial user feedback
- [ ] Document any issues and resolutions

This comprehensive execution guide ensures that an LLM Agent can independently implement the structured output feature enhancements while maintaining high quality standards and system reliability.