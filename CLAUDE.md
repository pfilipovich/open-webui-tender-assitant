# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open WebUI is a self-hosted AI platform designed to operate offline with various LLM runners like Ollama and OpenAI-compatible APIs. It features a Python FastAPI backend with a Svelte frontend, supporting RAG, function calling, multi-modal interactions, and extensive customization options.

## Development Commands

### Frontend Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Watch build
npm run build:watch

# Run frontend tests
npm run test:frontend

# Lint and format
npm run lint
npm run format
```

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server
./dev.sh
# or
uvicorn open_webui.main:app --port 8080 --host 0.0.0.0 --reload

# Run backend tests
pytest
```

### Linting and Code Quality
```bash
# Full lint check (frontend + backend + types)
npm run lint

# Individual lint commands
npm run lint:frontend    # ESLint for frontend
npm run lint:types       # TypeScript type checking
npm run lint:backend     # Pylint for backend

# Format code
npm run format           # Frontend formatting
npm run format:backend   # Backend formatting with black
```

### Docker Development
```bash
# Build and run with Docker Compose
make install             # docker-compose up -d
make start              # docker-compose start
make stop               # docker-compose stop
make startAndBuild      # docker-compose up -d --build
make update             # Full update process
```

## Architecture Overview

### Backend Architecture (`backend/open_webui/`)
- **FastAPI Application**: Main application in `main.py` with async/await support
- **Database Layer**: SQLAlchemy ORM with Alembic migrations, supports PostgreSQL, MySQL, SQLite
- **Model Layer**: Pydantic models in `models/` directory (users, chats, messages, etc.)
- **Router Layer**: FastAPI routers in `routers/` directory for API endpoints
- **Utilities**: Helper functions in `utils/` directory (auth, middleware, embeddings, etc.)
- **Configuration**: Environment-based config in `config.py` and `env.py`

### Frontend Architecture (`src/`)
- **SvelteKit**: Full-stack Svelte framework with TypeScript
- **Component Structure**: Reusable components in `lib/components/`
- **API Layer**: API client functions in `lib/apis/`
- **State Management**: Svelte stores in `lib/stores/`
- **Routing**: File-based routing in `routes/`
- **Internationalization**: i18n support in `lib/i18n/`

### Key Integrations
- **WebSocket Communication**: Real-time chat via Socket.IO
- **Vector Databases**: ChromaDB, Qdrant, Milvus, Pinecone for RAG
- **AI Services**: OpenAI, Anthropic, Google, Ollama integration
- **Authentication**: JWT-based auth with OAuth support
- **File Processing**: Document parsing, image processing, audio handling

## Database Architecture

### Migration System
- **Alembic**: Database migrations in `backend/open_webui/migrations/`
- **Internal Migrations**: Legacy migration system in `backend/open_webui/internal/migrations/`
- **Models**: Database models in `backend/open_webui/models/`

### Key Database Tables
- `users`: User authentication and profiles
- `chats`: Chat conversations
- `messages`: Individual chat messages
- `models`: AI model configurations
- `files`: File uploads and metadata
- `knowledge`: RAG knowledge base entries
- `tools`: Custom function definitions

## Development Patterns

### Backend Patterns
- **Dependency Injection**: FastAPI's dependency system for database connections, auth
- **Async Programming**: Extensive use of async/await for I/O operations
- **Middleware**: Custom middleware for CORS, compression, auth, security headers
- **Error Handling**: Structured error responses with proper HTTP status codes
- **Configuration**: Environment variables with fallback defaults

### Frontend Patterns
- **Component Composition**: Reusable Svelte components with props and slots
- **Store Management**: Reactive stores for global state
- **API Integration**: Centralized API client with error handling
- **Form Handling**: Form validation and submission patterns
- **Responsive Design**: Mobile-first CSS with Tailwind

## Testing

### Frontend Testing
```bash
npm run test:frontend    # Vitest unit tests
npm run cy:open         # Cypress e2e tests
```

### Backend Testing
```bash
cd backend
pytest                  # Run all tests
pytest -v               # Verbose output
pytest backend/open_webui/test/apps/webui/routers/test_auths.py  # Specific test file
```

### Test Structure
- **Frontend Tests**: Vitest for unit tests, Cypress for e2e in `cypress/`
- **Backend Tests**: pytest in `backend/open_webui/test/`
- **Integration Tests**: Full stack tests with Docker containers

## Key Configuration Files

- **package.json**: Frontend dependencies and scripts
- **requirements.txt**: Python backend dependencies
- **pyproject.toml**: Python project configuration
- **docker-compose.yaml**: Multi-service Docker setup
- **tailwind.config.js**: Tailwind CSS configuration
- **vite.config.ts**: Vite build configuration
- **tsconfig.json**: TypeScript configuration

## Environment Variables

Key environment variables are defined in `backend/open_webui/env.py`:
- `DATABASE_URL`: Database connection string
- `WEBUI_SECRET_KEY`: JWT secret key
- `OLLAMA_BASE_URL`: Ollama service URL
- `OPENAI_API_KEY`: OpenAI API key
- `DATA_DIR`: Data storage directory
- `REDIS_URL`: Redis connection for caching

## Common Development Tasks

### Adding New API Endpoints
1. Create router in `backend/open_webui/routers/`
2. Add database models in `backend/open_webui/models/`
3. Create migration if needed
4. Add API client function in `src/lib/apis/`
5. Update frontend components to use new API

### Adding New Features
1. Design database schema changes
2. Create Alembic migration
3. Implement backend API endpoints
4. Add frontend components and integration
5. Write tests for both frontend and backend
6. Update documentation

### Working with Vector Databases
- ChromaDB is the default vector database
- Configuration in `backend/open_webui/retrieval/vector/`
- Support for multiple vector databases via factory pattern

## Production Deployment

### Docker Deployment
```bash
# Production build
docker-compose up -d

# With GPU support
docker-compose -f docker-compose.gpu.yaml up -d

# With external Ollama
docker run -p 3000:8080 -e OLLAMA_BASE_URL=https://example.com \
  -v open-webui:/app/backend/data ghcr.io/open-webui/open-webui:main
```

### Python Package Installation
```bash
pip install open-webui
open-webui serve
```

## Important Notes

- **Database Migrations**: Always create migrations for schema changes
- **Authentication**: JWT tokens are used for session management
- **File Uploads**: Stored in `DATA_DIR/uploads/` with UUID filenames
- **RAG Integration**: Documents processed and stored in vector databases
- **WebSocket**: Real-time features use Socket.IO
- **Security**: CORS, security headers, and input validation are implemented
- **Internationalization**: Frontend supports multiple languages via i18n