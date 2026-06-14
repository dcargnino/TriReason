# TriReason

**Multi-iterative agent-based prompt optimization system**

TriReason is an advanced prompt optimization system that uses a multi-agent approach to iteratively generate, evaluate, and refine AI prompts until achieving optimal results against a defined objective.

> 🇮🇹 [Versione Italiana](README.it.md)

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Starting the Solution](#starting-the-solution)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

TriReason implements an iterative workflow based on three specialized agents that collaborate to optimize AI prompts:

1. **Generator**: Creates candidate prompts and simulates AI outputs
2. **Critic**: Evaluates output quality against the objective
3. **Refiner**: Improves the prompt based on Critic feedback

The system continues iterating until:
- The score reaches the defined threshold (default: 85/100)
- The maximum number of iterations is reached (default: 5)
- No improvements are registered for 3 consecutive iterations

## 🏗️ Architecture

```mermaid
graph TB
    User[User] -->|Sends request| API[FastAPI Backend]
    API -->|Initializes| WF[LangGraph Workflow]
    
    WF -->|1| Gen[Generator Agent]
    Gen -->|Prompt + Output| Crit[Critic Agent]
    Crit -->|Evaluation| Decision{Score OK?}
    
    Decision -->|No| Ref[Refiner Agent]
    Ref -->|Improved Prompt| Gen
    Decision -->|Yes| End[End]
    
    API -->|Saves| DB[(PostgreSQL)]
    API -->|Cache| Redis[(Redis)]
    
    Frontend[React Frontend] -->|HTTP/SSE| API
    
    style Gen fill:#a8e6cf
    style Crit fill:#ffd3b6
    style Ref fill:#ffaaa5
    style DB fill:#dcedc1
    style Redis fill:#ffd3b6
```

### Main Components

- **Backend (FastAPI)**: REST API with SSE support for real-time streaming
- **Workflow Engine (LangGraph)**: Manages multi-agent workflow
- **Database (PostgreSQL)**: Persistence of executions and iterations
- **Cache (Redis)**: Result caching to optimize performance
- **Frontend (React + TypeScript)**: Interactive user interface with graphical workflow visualization

## ⚙️ How It Works

### Optimization Cycle

```mermaid
stateDiagram-v2
    [*] --> Generate
    Generate --> Critique
    Critique --> CheckScore
    CheckScore --> Refine: Score < Threshold
    CheckScore --> [*]: Score >= Threshold
    Refine --> Generate
    
    note right of Generate
        Creates candidate prompt
        and simulates output
    end note
    
    note right of Critique
        Evaluates output with
        5 weighted criteria
    end note
    
    note right of Refine
        Improves prompt
        based on feedback
    end note
```

### Evaluation Criteria

The **Critic Agent** evaluates output on 5 weighted categories:

| Category | Weight | Description |
|----------|--------|-------------|
| Objective Fulfillment | 40% | How well the output satisfies the objective |
| Correctness & Faithfulness | 25% | Correctness and faithfulness to provided data |
| Completeness | 15% | Completeness of the response |
| Format Compliance | 10% | Compliance with requested format |
| Clarity & Usability | 10% | Clarity and usability of output |

**Total score**: 0-100 (weighted average)

## 📦 Requirements

### Required Software

- **Docker** and **Docker Compose** (recommended)
  
  OR
  
- **Python** 3.11+
- **Node.js** 18+
- **PostgreSQL** 16+
- **Redis** 7+

### API Key

- **OpenAI API Key** (to use GPT-4 or other models)

## 🚀 Installation

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TriReason
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file and insert your OpenAI API key:
   ```env
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

3. **Start all services with Docker Compose**
   ```bash
   docker-compose up --build
   ```

### Option 2: Local Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TriReason
   ```

2. **Create and activate a Python virtual environment** (RECOMMENDED)

   Using a virtual environment is strongly recommended to isolate project dependencies and avoid conflicts with other Python projects.

   **Using venv (Python built-in, recommended):**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate on Windows (cmd.exe)
   venv\Scripts\activate.bat
   
   # Activate on Windows (PowerShell)
   venv\Scripts\Activate.ps1
   
   # Activate on Linux/macOS
   source venv/bin/activate
   ```

   **Using virtualenv (alternative):**
   ```bash
   # Install virtualenv if not already installed
   pip install virtualenv
   
   # Create virtual environment
   virtualenv venv
   
   # Activation is the same as venv above
   ```

   **Using conda (for Anaconda users):**
   ```bash
   # Create conda environment
   conda create -n trireason python=3.11
   
   # Activate conda environment
   conda activate trireason
   ```

   > **Note**: After activation, your terminal prompt should show the environment name (e.g., `(venv)` or `(trireason)`). All subsequent `pip` commands will install packages only in this isolated environment.

3. **Install Python backend**
   ```bash
   pip install -e .
   ```

4. **Install frontend**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Start PostgreSQL and Redis**
   ```bash
   # Using Docker for support services
   docker run -d -p 5432:5432 -e POSTGRES_USER=trireason -e POSTGRES_PASSWORD=trireason -e POSTGRES_DB=trireason postgres:16-alpine
   docker run -d -p 6379:6379 redis:7-alpine
   ```

6. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API key
   ```

7. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

### Deactivating the Virtual Environment

When you're done working on the project, you can deactivate the virtual environment:

```bash
# For venv and virtualenv
deactivate

# For conda
conda deactivate
```

## 🔧 Configuration

The `.env` file contains all necessary configurations:

```env
# OpenAI / LLM Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o

# Database
DATABASE_URL=postgresql+asyncpg://trireason:trireason@localhost:5432/trireason

# Redis
REDIS_URL=redis://localhost:6379/0

# App
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=info

# TriReason defaults
DEFAULT_MAX_ITERATIONS=5
DEFAULT_SCORE_THRESHOLD=85
```

### Configurable Parameters

- `OPENAI_MODEL`: Model to use (default: `gpt-4o`)
- `DEFAULT_MAX_ITERATIONS`: Maximum number of iterations (default: 5)
- `DEFAULT_SCORE_THRESHOLD`: Score threshold to consider optimization complete (default: 85)

## 🎬 Starting the Solution

### With Docker Compose

```bash
# Start all services
docker-compose up

# Or in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Manual Start

**Terminal 1 - Backend:**
```bash
# From project root
python -m trireason
# or
uvicorn trireason.app:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## 💻 Usage

### Web Interface

1. Open browser at http://localhost:5173
2. Enter your data in the form:
   - **Data**: Input data to process
   - **Objective**: The objective you want to achieve
   - **Max Iterations**: Maximum number of iterations (optional)
   - **Score Threshold**: Score threshold (optional)
3. Click "Start Optimization"
4. Observe real-time progress with:
   - Workflow graph
   - Scores per iteration
   - Details of each iteration

### REST API

#### Synchronous Optimization

```bash
curl -X POST http://localhost:8000/api/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "data": "Customer feedback: The product is great but shipping was slow",
    "objective": "Extract sentiment and key issues from customer feedback",
    "max_iterations": 5,
    "score_threshold": 85
  }'
```

#### Streaming Optimization (SSE)

```bash
curl -N http://localhost:8000/api/v1/optimize/stream \
  -H "Content-Type: application/json" \
  -d '{
    "data": "Customer feedback: The product is great but shipping was slow",
    "objective": "Extract sentiment and key issues from customer feedback"
  }'
```

#### Retrieve Execution Results

```bash
curl http://localhost:8000/api/v1/runs/{run_id}
```

### Response Example

```json
{
  "run_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "total_iterations": 3,
  "best_score": 92.5,
  "best_prompt": "You are a customer feedback analyzer...",
  "stop_reason": "threshold_reached",
  "iterations": [
    {
      "iteration_number": 1,
      "candidate_prompt": "...",
      "candidate_output": "...",
      "score_total": 75.0,
      "score_breakdown": {
        "objective_fulfillment": 70,
        "correctness_faithfulness": 80,
        "completeness": 75,
        "format_compliance": 85,
        "clarity_usability": 65
      },
      "passed": false,
      "issues": ["Output lacks specific sentiment classification"],
      "recommendations": ["Add explicit sentiment labels"],
      "is_best_so_far": true
    }
  ]
}
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/optimize` | Executes synchronous optimization |
| POST | `/api/v1/optimize/stream` | Executes optimization with SSE streaming |
| GET | `/api/v1/runs/{run_id}` | Retrieves execution results |
| GET | `/api/v1/runs/{run_id}/status` | Checks execution status |
| GET | `/api/v1/health` | Service health check |

Interactive documentation available at: http://localhost:8000/docs

## 📁 Project Structure

```
TriReason/
├── src/trireason/           # Python Backend
│   ├── agents/              # AI Agents (Generator, Critic, Refiner)
│   ├── api/                 # FastAPI Routes
│   ├── cache/               # Redis cache management
│   ├── db/                  # Database models and repository
│   ├── schemas/             # Pydantic schemas
│   ├── utils/               # Utilities (hashing, etc.)
│   ├── workflow/            # LangGraph workflow
│   ├── app.py               # FastAPI application
│   └── config.py            # Configuration
├── frontend/                # React + TypeScript Frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   └── types/           # TypeScript definitions
│   └── public/
├── alembic/                 # Database migrations
├── tests/                   # Unit and integration tests
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile               # Backend Dockerfile
├── pyproject.toml           # Python configuration
└── .env.example             # Environment variables template
```

## 🛠️ Technologies Used

### Backend
- **FastAPI**: Modern and performant web framework
- **LangGraph**: Multi-agent workflow orchestration
- **LangChain**: LLM integration
- **SQLAlchemy**: ORM for PostgreSQL
- **Alembic**: Database migration management
- **Redis**: Caching and performance optimization
- **Pydantic**: Data validation and configuration
- **SSE-Starlette**: Server-Sent Events for streaming

### Frontend
- **React 19**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **TailwindCSS**: Styling
- **XYFlow**: Graphical workflow visualization

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **PostgreSQL 16**: Relational database
- **Redis 7**: In-memory cache
- **Nginx**: Reverse proxy for frontend

## 🔍 Advanced Features

### Intelligent Caching
- Result caching for identical data+objective pairs
- Execution caching for fast retrieval
- Automatic invalidation

### Complete Persistence
- Saving of every iteration in the database
- Complete history tracking
- Retrospective analysis capability

### Real-time Streaming
- Live updates via Server-Sent Events
- Progressive iteration visualization
- Immediate user feedback

### Automatic Optimization
- Automatic stop when threshold is reached
- Plateau detection (no improvement)
- Configurable maximum iteration limit

## 🔧 Troubleshooting

### Port Conflict Errors

#### Problem: "Bind for 0.0.0.0:5432 failed: port is already allocated"

This error occurs when PostgreSQL port 5432 is already in use.

**Solution 1: Use Existing PostgreSQL (Recommended)**

If you already have PostgreSQL installed:

```bash
# Create database and user
psql -U postgres
```

In psql prompt:
```sql
CREATE USER trireason WITH PASSWORD 'trireason';
CREATE DATABASE trireason OWNER trireason;
GRANT ALL PRIVILEGES ON DATABASE trireason TO trireason;
\q
```

Skip the Docker PostgreSQL command and proceed with Redis only.

**Solution 2: Use Different Port**

```bash
# Map to port 5433 instead
docker run -d -p 5433:5432 -e POSTGRES_USER=trireason -e POSTGRES_PASSWORD=trireason -e POSTGRES_DB=trireason postgres:16-alpine
```

Update `.env`:
```env
DATABASE_URL=postgresql+asyncpg://trireason:trireason@localhost:5433/trireason
```

**Solution 3: Stop Existing Service**

Windows (PowerShell as Administrator):
```powershell
Stop-Service postgresql-x64-16
```

Linux/macOS:
```bash
sudo systemctl stop postgresql
```

### Virtual Environment Issues

#### Problem: Cannot activate on Windows PowerShell

**Error:** "running scripts is disabled on this system"

**Solution:**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Problem: "python: command not found"

**Solution:**
- Windows: Use `py -m venv venv`
- Linux/macOS: Use `python3 -m venv venv`

### Database Connection Issues

#### Problem: Cannot connect during migration

**Solutions:**
1. Verify PostgreSQL is running
2. Check `.env` DATABASE_URL is correct
3. Test connection:
   ```bash
   # Check if port is listening
   # Windows
   netstat -ano | findstr :5432
   
   # Linux/macOS
   lsof -i :5432
   ```

### Docker Issues

#### Problem: "docker: command not found"

**Solution:** Install Docker Desktop from https://www.docker.com/products/docker-desktop

#### Problem: Docker daemon not running

**Solution:**
- Windows/macOS: Start Docker Desktop application
- Linux: `sudo systemctl start docker`

### General Tips

- Always activate virtual environment before running Python commands
- Use Docker Compose (Option 1) for easier setup
- Check logs for detailed errors: `docker logs <container-id>`

## 📝 Notes

- The system requires an active internet connection to communicate with the OpenAI API
- API costs depend on the model used and number of iterations
- Caching significantly reduces costs for repeated requests
- For production environments, properly configure environment variables and secrets

## 🤝 Contributing

To contribute to the project:
1. Fork the repository
2. Create a branch for your feature
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is distributed under the MIT license.

---

**Developed with ❤️ using FastAPI, LangGraph and React**
