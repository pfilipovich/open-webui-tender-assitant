# AGENT_DEVELOPMENT_PLAN.md

## Checklist Feature Implementation Plan

### Overview
This document outlines the implementation plan for adding a **Checklist** feature to Open WebUI. The Checklist feature will allow users to create collections of prompts that can be executed sequentially in chat conversations using the `%` symbol, similar to how individual prompts are accessed with `/`.

### Feature Requirements

#### Core Functionality
1. **Checklist Management**: Users can create, edit, and delete checklists
2. **Prompt Collection**: Each checklist contains multiple prompts in a specific order
3. **Sequential Execution**: When a checklist is selected via `%`, prompts execute one by one
4. **Context Preservation**: Each prompt in the sequence has access to previous responses
5. **Answer Aggregation**: All responses are collected and presented as a structured list

#### User Interface
- **Workspace Integration**: Checklists appear alongside Prompts in the workspace
- **Chat Integration**: `%` symbol triggers checklist auto-completion in chat
- **Answer Display**: Sequential responses are formatted clearly in the chat

### Technical Architecture

#### Database Schema
Following the existing Prompts pattern, create a new table structure:

```sql
-- Main checklists table
CREATE TABLE checklist (
    id VARCHAR PRIMARY KEY,           -- Unique checklist identifier
    user_id VARCHAR NOT NULL,         -- Creator of the checklist
    title TEXT NOT NULL,              -- Human-readable checklist name
    description TEXT,                 -- Optional checklist description
    command VARCHAR UNIQUE NOT NULL,  -- Unique command (e.g., "meeting-prep")
    timestamp BIGINT NOT NULL,        -- Creation/modification time
    access_control JSON,              -- Permission controls (same as prompts)
    INDEX idx_user_id (user_id),
    INDEX idx_command (command)
);

-- Checklist items table (many-to-many with prompts)
CREATE TABLE checklist_item (
    id VARCHAR PRIMARY KEY,
    checklist_id VARCHAR NOT NULL,
    prompt_command VARCHAR NOT NULL,  -- Reference to existing prompt
    order_index INTEGER NOT NULL,    -- Execution order within checklist
    FOREIGN KEY (checklist_id) REFERENCES checklist(id) ON DELETE CASCADE,
    FOREIGN KEY (prompt_command) REFERENCES prompt(command) ON DELETE CASCADE,
    INDEX idx_checklist_id (checklist_id),
    INDEX idx_order (checklist_id, order_index)
);
```

### Implementation Plan

#### Phase 1: Backend Infrastructure

**1.1 Database Models** (`backend/open_webui/models/checklists.py`)
- `Checklist` - SQLAlchemy model for checklists table
- `ChecklistItem` - SQLAlchemy model for checklist_item table  
- `ChecklistModel` - Pydantic model for API responses
- `ChecklistForm` - Pydantic model for create/update operations
- `ChecklistUserResponse` - Extended model with user information
- `ChecklistsTable` - Database operations class

**1.2 API Endpoints** (`backend/open_webui/routers/checklists.py`)
```python
# Core CRUD operations
GET /api/v1/checklists/                    # Get all checklists
GET /api/v1/checklists/list               # Get checklists with user info
POST /api/v1/checklists/create            # Create new checklist
GET /api/v1/checklists/command/{command}  # Get checklist by command
PUT /api/v1/checklists/command/{command}  # Update checklist
DELETE /api/v1/checklists/command/{command} # Delete checklist

# Checklist execution
POST /api/v1/checklists/command/{command}/execute # Execute checklist
GET /api/v1/checklists/command/{command}/prompts  # Get checklist prompts
```

**1.3 Database Migration** (`backend/open_webui/migrations/`)
- Create Alembic migration for new tables
- Add appropriate indexes for performance

#### Phase 2: Frontend API Integration

**2.1 API Client** (`src/lib/apis/checklists/index.ts`)
```typescript
// API client functions
export const createNewChecklist = async (token: string, checklist: ChecklistForm)
export const getChecklists = async (token: string) 
export const getChecklistList = async (token: string)
export const getChecklistByCommand = async (token: string, command: string)
export const updateChecklistByCommand = async (token: string, command: string, checklist: ChecklistForm)
export const deleteChecklistByCommand = async (token: string, command: string)
export const executeChecklist = async (token: string, command: string, context: string)
```

**2.2 Store Management** (`src/lib/stores/index.ts`)
```typescript
// Add checklist store
export const checklists = writable([]);
```

#### Phase 3: Workspace Management UI

**3.1 Main Checklist Workspace** (`src/routes/(app)/workspace/checklists/+page.svelte`)
- List view of all user checklists
- Search and filter functionality
- Create, edit, delete actions
- Import/export functionality
- Access control management

**3.2 Checklist Editor** (`src/lib/components/workspace/Checklists/ChecklistEditor.svelte`)
- Title and command input with validation
- Description editor
- Prompt selection and ordering interface
- Drag-and-drop for reordering prompts
- Preview functionality
- Access control settings

**3.3 Supporting Components**
- `ChecklistMenu.svelte` - Context menu for checklist actions
- `PromptSelector.svelte` - Interface for adding prompts to checklist
- `ChecklistPreview.svelte` - Preview checklist execution flow

**3.4 Routing**
- `/workspace/checklists` - Main checklists page
- `/workspace/checklists/create` - Create new checklist
- `/workspace/checklists/edit?command={command}` - Edit existing checklist

#### Phase 4: Chat Integration

**4.1 Commands Integration** (`src/lib/components/chat/MessageInput/Commands.svelte`)
```javascript
// Add % symbol support
$: show = ['/', '#', '@', '&', '%'].includes(command?.charAt(0)) ||
        '\\#' === command.slice(0, 2) ||
        '\\&' === command.slice(0, 2) ||
        '\\%' === command.slice(0, 2);

// Add checklist component
{:else if (command?.charAt(0) === '%' && command.startsWith('%') && !command.includes('% ')) || 
          ('\\%' === command.slice(0, 2) && command.startsWith('%') && !command.includes('% '))}
    <Checklists 
        bind:this={commandElement} 
        bind:prompt 
        command={command.includes('\\%') ? command.slice(2) : command}
        on:execute={(e) => executeChecklist(e.detail)} 
    />
```

**4.2 Checklist Component** (`src/lib/components/chat/MessageInput/Commands/Checklists.svelte`)
- Auto-completion interface similar to Prompts
- Checklist selection and execution
- Sequential prompt processing
- Progress indication during execution
- Variable replacement support
- File and knowledge context inheritance

**4.3 Execution Engine**
- Sequential prompt execution with context passing
- Files and knowledge context preservation across prompts
- Response aggregation and formatting
- Error handling and recovery
- User cancellation support
- Integration with existing file upload and knowledge selection systems

#### Phase 5: Workspace Integration

**5.1 Navigation Updates** (`src/routes/(app)/workspace/+layout.svelte`)
- Add "Checklists" tab to workspace navigation
- Conditional display based on user permissions

**5.2 Permission System**
- Add `workspace.checklists` permission
- Integrate with existing access control system
- Admin override capabilities

#### Phase 6: Testing & Quality Assurance

**6.1 Backend Tests** (`backend/open_webui/test/apps/webui/routers/test_checklists.py`)
- CRUD operation tests
- Access control validation
- Execution flow testing
- Error handling verification
- File context preservation tests
- Knowledge base integration tests
- Sequential prompt execution with mixed context

**6.2 Frontend Tests**
- Component unit tests
- Integration tests for chat functionality
- E2E tests for complete workflow
- File upload + checklist execution tests
- Knowledge selection + checklist execution tests
- Multi-modal context preservation tests

### Implementation Details

#### Checklist Execution Flow

1. **Selection**: User types `%checklist-name` in chat
2. **Context Capture**: System captures current chat context:
   - Attached files (documents, images, etc.)
   - Selected knowledge bases and collections
   - Previous conversation history
   - User variables and preferences
3. **Loading**: System loads checklist and associated prompts
4. **Initialization**: First prompt is executed with full context
5. **Iteration**: Each subsequent prompt receives:
   - Original user context
   - All attached files and knowledge sources
   - Previous prompt responses in the checklist
   - Current conversation state
6. **Aggregation**: All responses are collected and formatted
7. **Display**: Results shown as structured list in chat

#### File and Knowledge Integration

**File Context Preservation**:
- All files attached to the conversation remain available throughout checklist execution
- Files can be referenced in checklist prompts using existing file handling mechanisms
- File processing results are maintained across prompt sequences

**Knowledge Base Integration**:
- Knowledge bases selected via `#` remain accessible during checklist execution
- Collections selected via `&` are preserved throughout the sequence
- Knowledge context is automatically included in each prompt execution
- Support for dynamic knowledge base selection within checklists

**Context Variables**:
```javascript
// Enhanced context object passed to each prompt
{
  files: [...attachedFiles],           // All uploaded/attached files
  knowledge: [...selectedKnowledge],   // Selected knowledge bases
  collections: [...selectedCollections], // Selected collections
  previousResponses: [...responses],   // Previous checklist responses
  userContext: {...userVariables}     // User variables and preferences
}
```

#### Variable Replacement

Checklists support all existing prompt variables plus new context variables:
- `{{CLIPBOARD}}` - Clipboard content
- `{{USER_NAME}}` - Current user name
- `{{CURRENT_DATE}}` - Current date
- `{{USER_LOCATION}}` - User location
- `{{PREVIOUS_RESPONSE}}` - Previous checklist item response (new)
- `{{FILE_NAMES}}` - List of attached file names (new)
- `{{KNOWLEDGE_SOURCES}}` - List of selected knowledge bases (new)
- `{{COLLECTION_NAMES}}` - List of selected collections (new)

#### Integration Scenarios

**Scenario 1: Document Analysis Checklist**
```
User workflow:
1. Uploads PDF document to chat
2. Types %document-analysis
3. Checklist executes:
   - /extract-summary (analyzes the uploaded PDF)
   - /identify-key-points (processes summary + original PDF)  
   - /action-items (creates tasks based on analysis)
   - /follow-up-questions (generates questions for clarification)
```

**Scenario 2: Knowledge Base Research Checklist**
```
User workflow:
1. Selects company knowledge base via #company-docs
2. Selects project collection via &project-alpha
3. Types %research-checklist
4. Checklist executes:
   - /background-research (queries knowledge base)
   - /related-projects (searches collections for similar work)
   - /risk-assessment (analyzes findings for potential issues)
   - /recommendations (provides actionable insights)
```

**Scenario 3: Multi-Modal Analysis Checklist**
```
User workflow:
1. Uploads image + text document
2. Selects relevant knowledge base
3. Types %multi-modal-analysis
4. Checklist executes:
   - /image-description (analyzes uploaded image)
   - /document-summary (processes text document)
   - /knowledge-correlation (relates to knowledge base)
   - /comprehensive-report (combines all analyses)
```

#### Technical Implementation Details

**File Context Management**:
```typescript
// Enhanced checklist execution with file context
interface ChecklistExecutionContext {
  checklistId: string;
  files: AttachedFile[];           // Files attached to conversation
  knowledge: KnowledgeBase[];      // Selected knowledge bases
  collections: Collection[];       // Selected collections
  previousResponses: Response[];   // Previous prompt responses
  userContext: UserContext;        // User preferences and variables
  conversationHistory: Message[]; // Chat history for context
}

// File handling during execution
const executeChecklistWithFiles = async (context: ChecklistExecutionContext) => {
  for (const promptItem of checklist.items) {
    const promptContext = {
      ...context,
      currentFiles: context.files,  // All files remain available
      previousResponses: responses.slice(0, currentIndex)
    };
    
    const response = await executePromptWithContext(promptItem.prompt, promptContext);
    responses.push(response);
  }
};
```

**Knowledge Integration**:
```typescript
// Knowledge base context preservation
interface KnowledgeContext {
  selectedBases: KnowledgeBase[];
  selectedCollections: Collection[];
  queryHistory: string[];
  relevantDocuments: Document[];
}

// Each prompt in checklist maintains access to knowledge
const executePromptWithKnowledge = async (prompt: Prompt, context: ChecklistExecutionContext) => {
  const knowledgeQuery = await processPromptForKnowledge(prompt.content, context.knowledge);
  const relevantDocs = await queryKnowledgeBases(knowledgeQuery, context.knowledge);
  
  return await executePrompt(prompt, {
    ...context,
    knowledgeContext: relevantDocs,
    previousKnowledgeQueries: context.previousResponses.map(r => r.knowledgeQuery)
  });
};
```

#### Enhanced Data Model

```json
{
  "id": "uuid-123",
  "command": "document-analysis",
  "title": "Document Analysis Checklist",
  "description": "Comprehensive analysis of uploaded documents with knowledge base correlation",
  "user_id": "user-456",
  "timestamp": 1699123456,
  "access_control": null,
  "settings": {
    "preserveFileContext": true,        // Keep files available throughout
    "preserveKnowledgeContext": true,   // Maintain knowledge base access
    "aggregateResponses": true,         // Collect all responses
    "allowCancellation": true           // User can stop mid-execution
  },
  "items": [
    {
      "prompt_command": "/extract-summary",
      "order_index": 1,
      "settings": {
        "requiresFiles": true,          // This prompt needs files
        "fileTypes": ["pdf", "doc", "txt"]
      }
    },
    {
      "prompt_command": "/knowledge-correlation",
      "order_index": 2,
      "settings": {
        "requiresKnowledge": true,      // This prompt needs knowledge base
        "knowledgeTypes": ["documents", "collections"]
      }
    }
  ]
}
```

#### Access Control

Checklists inherit the same access control system as Prompts:
- **Public**: Available to all users
- **Private**: Creator only
- **Group-based**: Specific users/groups with read/write permissions

#### Data Model Example

```json
{
  "id": "uuid-123",
  "command": "meeting-prep",
  "title": "Meeting Preparation Checklist",
  "description": "Complete preparation checklist for important meetings",
  "user_id": "user-456", 
  "timestamp": 1699123456,
  "access_control": null,
  "items": [
    {
      "prompt_command": "/agenda-review",
      "order_index": 1
    },
    {
      "prompt_command": "/stakeholder-analysis", 
      "order_index": 2
    },
    {
      "prompt_command": "/action-items",
      "order_index": 3
    }
  ]
}
```

### Development Timeline

#### Week 1-2: Backend Infrastructure
- Database models and migrations
- Core API endpoints
- Basic CRUD operations

#### Week 3-4: Frontend API & Workspace
- API client implementation
- Workspace UI components
- Checklist editor interface

#### Week 5-6: Chat Integration
- Commands integration
- Checklist selection component
- Execution engine

#### Week 7-8: Testing & Polish
- Comprehensive testing
- Bug fixes and optimization
- Documentation updates

### Dependencies

#### Technical Dependencies
- **Frontend**: Existing Svelte/SvelteKit setup, Tailwind CSS
- **Backend**: FastAPI, SQLAlchemy, Alembic
- **Database**: Compatible with existing PostgreSQL/MySQL/SQLite setup

#### Feature Dependencies
- **Prompts System**: Checklists reference existing prompts
- **Access Control**: Reuse existing permission system
- **Workspace**: Integrate with existing workspace infrastructure
- **File Upload System**: Integration with existing file handling mechanisms
- **Knowledge Base System**: Integration with existing knowledge and collection selection
- **Chat Context**: Preservation of conversation state and file attachments

### Success Criteria

1. **Functionality**: Users can create, manage, and execute checklists
2. **Performance**: Checklist execution completes within reasonable time
3. **Usability**: Intuitive interface following existing design patterns
4. **Reliability**: Robust error handling and recovery mechanisms
5. **Compatibility**: Works seamlessly with existing features
6. **File Integration**: Files uploaded to conversation remain accessible throughout checklist execution
7. **Knowledge Integration**: Selected knowledge bases and collections are preserved across all prompts
8. **Context Preservation**: Previous responses and file/knowledge context flow correctly between prompts

### Future Enhancements

#### Phase 2 Features
- **Conditional Logic**: Skip prompts based on previous responses
- **Branching**: Different execution paths based on conditions
- **Templates**: Pre-built checklist templates for common use cases
- **Analytics**: Usage statistics and execution metrics
- **Collaboration**: Share and collaborate on checklists
- **Scheduling**: Automated checklist execution
- **Integration**: Export results to external systems

#### Advanced Features
- **AI-Assisted Creation**: Generate checklists from descriptions
- **Dynamic Prompts**: Modify prompts based on context
- **Result Processing**: Automated analysis of checklist outputs
- **Workflow Integration**: Trigger external actions based on results

### Risk Mitigation

#### Technical Risks
- **Performance**: Large checklists may impact chat responsiveness
  - *Mitigation*: Implement streaming/progressive execution
- **Database Complexity**: Many-to-many relationships may complicate queries
  - *Mitigation*: Proper indexing and query optimization

#### User Experience Risks  
- **Confusion**: New % symbol may not be discoverable
  - *Mitigation*: Clear documentation and in-app guidance
- **Complexity**: Checklist management may overwhelm users
  - *Mitigation*: Progressive disclosure and intuitive defaults

### Conclusion

The Checklist feature will significantly enhance Open WebUI's productivity capabilities by allowing users to create and execute structured prompt sequences. By following the existing Prompts architecture and patterns, we can ensure consistency, maintainability, and user familiarity while adding powerful new functionality.

The phased implementation approach minimizes risk while delivering incremental value, and the comprehensive testing strategy ensures reliability and quality.