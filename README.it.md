# TriReason

**Sistema di ottimizzazione dei prompt basato su agenti multi-iterativi**

TriReason è un sistema avanzato di ottimizzazione dei prompt che utilizza un approccio multi-agente per generare, valutare e raffinare iterativamente i prompt AI fino a raggiungere risultati ottimali rispetto a un obiettivo definito.

## 📋 Indice

- [Panoramica](#panoramica)
- [Architettura](#architettura)
- [Funzionamento](#funzionamento)
- [Requisiti](#requisiti)
- [Installazione](#installazione)
- [Configurazione](#configurazione)
- [Avvio della Soluzione](#avvio-della-soluzione)
- [Utilizzo](#utilizzo)
- [API Endpoints](#api-endpoints)
- [Struttura del Progetto](#struttura-del-progetto)
- [Tecnologie Utilizzate](#tecnologie-utilizzate)
- [Risoluzione Problemi](#risoluzione-problemi)

## 🎯 Panoramica

TriReason implementa un workflow iterativo basato su tre agenti specializzati che collaborano per ottimizzare i prompt AI:

1. **Generator**: Crea prompt candidati e simula output AI
2. **Critic**: Valuta la qualità dell'output rispetto all'obiettivo
3. **Refiner**: Migliora il prompt basandosi sul feedback del Critic

Il sistema continua a iterare fino a quando:
- Il punteggio raggiunge la soglia definita (default: 85/100)
- Si raggiunge il numero massimo di iterazioni (default: 5)
- Non si registrano miglioramenti per 3 iterazioni consecutive

## 🏗️ Architettura

```mermaid
graph TB
    User[Utente] -->|Invia richiesta| API[FastAPI Backend]
    API -->|Inizializza| WF[LangGraph Workflow]
    
    WF -->|1| Gen[Generator Agent]
    Gen -->|Prompt + Output| Crit[Critic Agent]
    Crit -->|Valutazione| Decision{Score OK?}
    
    Decision -->|No| Ref[Refiner Agent]
    Ref -->|Prompt Migliorato| Gen
    Decision -->|Sì| End[Fine]
    
    API -->|Salva| DB[(PostgreSQL)]
    API -->|Cache| Redis[(Redis)]
    
    Frontend[React Frontend] -->|HTTP/SSE| API
    
    style Gen fill:#a8e6cf
    style Crit fill:#ffd3b6
    style Ref fill:#ffaaa5
    style DB fill:#dcedc1
    style Redis fill:#ffd3b6
```

### Componenti Principali

- **Backend (FastAPI)**: API REST con supporto SSE per streaming in tempo reale
- **Workflow Engine (LangGraph)**: Gestisce il flusso di lavoro multi-agente
- **Database (PostgreSQL)**: Persistenza delle esecuzioni e iterazioni
- **Cache (Redis)**: Caching dei risultati per ottimizzare le performance
- **Frontend (React + TypeScript)**: Interfaccia utente interattiva con visualizzazione grafica del workflow

## ⚙️ Funzionamento

### Ciclo di Ottimizzazione

```mermaid
stateDiagram-v2
    [*] --> Generate
    Generate --> Critique
    Critique --> CheckScore
    CheckScore --> Refine: Score < Threshold
    CheckScore --> [*]: Score >= Threshold
    Refine --> Generate
    
    note right of Generate
        Crea prompt candidato
        e simula output
    end note
    
    note right of Critique
        Valuta output con
        5 criteri pesati
    end note
    
    note right of Refine
        Migliora prompt
        basandosi su feedback
    end note
```

### Criteri di Valutazione

Il **Critic Agent** valuta l'output su 5 categorie ponderate:

| Categoria | Peso | Descrizione |
|-----------|------|-------------|
| Objective Fulfillment | 40% | Quanto l'output soddisfa l'obiettivo |
| Correctness & Faithfulness | 25% | Correttezza e fedeltà ai dati forniti |
| Completeness | 15% | Completezza della risposta |
| Format Compliance | 10% | Conformità al formato richiesto |
| Clarity & Usability | 10% | Chiarezza e usabilità dell'output |

**Punteggio totale**: 0-100 (media ponderata)

## 📦 Requisiti

### Software Necessario

- **Docker** e **Docker Compose** (consigliato)
  
  OPPURE
  
- **Python** 3.11+
- **Node.js** 18+
- **PostgreSQL** 16+
- **Redis** 7+

### Chiave API

- **OpenAI API Key** (per utilizzare GPT-4 o altri modelli)

## 🚀 Installazione

### Opzione 1: Docker (Consigliato)

1. **Clona il repository**
   ```bash
   git clone <repository-url>
   cd TriReason
   ```

2. **Configura le variabili d'ambiente**
   ```bash
   cp .env.example .env
   ```
   
   Modifica il file `.env` e inserisci la tua chiave API OpenAI:
   ```env
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

3. **Avvia tutti i servizi con Docker Compose**
   ```bash
   docker-compose up --build
   ```

### Opzione 2: Installazione Locale

1. **Clona il repository**
   ```bash
   git clone <repository-url>
   cd TriReason
   ```

2. **Crea e attiva un ambiente virtuale Python** (CONSIGLIATO)

   L'utilizzo di un ambiente virtuale è fortemente consigliato per isolare le dipendenze del progetto ed evitare conflitti con altri progetti Python.

   **Usando venv (integrato in Python, consigliato):**
   ```bash
   # Crea l'ambiente virtuale
   python -m venv venv
   
   # Attiva su Windows (cmd.exe)
   venv\Scripts\activate.bat
   
   # Attiva su Windows (PowerShell)
   venv\Scripts\Activate.ps1
   
   # Attiva su Linux/macOS
   source venv/bin/activate
   ```

   **Usando virtualenv (alternativa):**
   ```bash
   # Installa virtualenv se non già installato
   pip install virtualenv
   
   # Crea l'ambiente virtuale
   virtualenv venv
   
   # L'attivazione è la stessa di venv sopra
   ```

   **Usando conda (per utenti Anaconda):**
   ```bash
   # Crea l'ambiente conda
   conda create -n trireason python=3.11
   
   # Attiva l'ambiente conda
   conda activate trireason
   ```

   > **Nota**: Dopo l'attivazione, il prompt del terminale dovrebbe mostrare il nome dell'ambiente (es. `(venv)` o `(trireason)`). Tutti i successivi comandi `pip` installeranno i pacchetti solo in questo ambiente isolato.

3. **Installa il backend Python**
   ```bash
   pip install -e .
   ```

4. **Installa il frontend**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Avvia PostgreSQL e Redis**
   ```bash
   # Usando Docker per i servizi di supporto
   docker run -d -p 5432:5432 -e POSTGRES_USER=trireason -e POSTGRES_PASSWORD=trireason -e POSTGRES_DB=trireason postgres:16-alpine
   docker run -d -p 6379:6379 redis:7-alpine
   ```

6. **Configura le variabili d'ambiente**
   ```bash
   cp .env.example .env
   # Modifica .env con la tua chiave API
   ```

7. **Esegui le migrazioni del database**
   ```bash
   alembic upgrade head
   ```

### Disattivare l'Ambiente Virtuale

Quando hai finito di lavorare al progetto, puoi disattivare l'ambiente virtuale:

```bash
# Per venv e virtualenv
deactivate

# Per conda
conda deactivate
```

## 🔧 Configurazione

Il file `.env` contiene tutte le configurazioni necessarie:

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

### Parametri Configurabili

- `OPENAI_MODEL`: Modello da utilizzare (default: `gpt-4o`)
- `DEFAULT_MAX_ITERATIONS`: Numero massimo di iterazioni (default: 5)
- `DEFAULT_SCORE_THRESHOLD`: Soglia di punteggio per considerare l'ottimizzazione completata (default: 85)

## 🎬 Avvio della Soluzione

### Con Docker Compose

```bash
# Avvia tutti i servizi
docker-compose up

# Oppure in background
docker-compose up -d

# Visualizza i log
docker-compose logs -f

# Ferma i servizi
docker-compose down
```

I servizi saranno disponibili su:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Avvio Manuale

**Terminal 1 - Backend:**
```bash
# Dalla root del progetto
python -m trireason
# oppure
uvicorn trireason.app:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## 💻 Utilizzo

### Interfaccia Web

1. Apri il browser su http://localhost:5173
2. Inserisci i tuoi dati nel form:
   - **Data**: I dati di input da processare
   - **Objective**: L'obiettivo che vuoi raggiungere
   - **Max Iterations**: Numero massimo di iterazioni (opzionale)
   - **Score Threshold**: Soglia di punteggio (opzionale)
3. Clicca su "Start Optimization"
4. Osserva il progresso in tempo reale con:
   - Grafico del workflow
   - Punteggi per iterazione
   - Dettagli di ogni iterazione

### API REST

#### Ottimizzazione Sincrona

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

#### Ottimizzazione con Streaming (SSE)

```bash
curl -N http://localhost:8000/api/v1/optimize/stream \
  -H "Content-Type: application/json" \
  -d '{
    "data": "Customer feedback: The product is great but shipping was slow",
    "objective": "Extract sentiment and key issues from customer feedback"
  }'
```

#### Recupera Risultati di un'Esecuzione

```bash
curl http://localhost:8000/api/v1/runs/{run_id}
```

### Esempio di Risposta

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

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| POST | `/api/v1/optimize` | Esegue ottimizzazione sincrona |
| POST | `/api/v1/optimize/stream` | Esegue ottimizzazione con streaming SSE |
| GET | `/api/v1/runs/{run_id}` | Recupera risultati di un'esecuzione |
| GET | `/api/v1/runs/{run_id}/status` | Verifica lo stato di un'esecuzione |
| GET | `/api/v1/health` | Health check del servizio |

Documentazione interattiva disponibile su: http://localhost:8000/docs

## 📁 Struttura del Progetto

```
TriReason/
├── src/trireason/           # Backend Python
│   ├── agents/              # Agenti AI (Generator, Critic, Refiner)
│   ├── api/                 # Route FastAPI
│   ├── cache/               # Gestione cache Redis
│   ├── db/                  # Modelli e repository database
│   ├── schemas/             # Schemi Pydantic
│   ├── utils/               # Utility (hashing, etc.)
│   ├── workflow/            # LangGraph workflow
│   ├── app.py               # Applicazione FastAPI
│   └── config.py            # Configurazione
├── frontend/                # Frontend React + TypeScript
│   ├── src/
│   │   ├── components/      # Componenti React
│   │   ├── hooks/           # Custom hooks
│   │   └── types/           # Definizioni TypeScript
│   └── public/
├── alembic/                 # Migrazioni database
├── tests/                   # Test unitari e di integrazione
├── docker-compose.yml       # Configurazione Docker Compose
├── Dockerfile               # Dockerfile backend
├── pyproject.toml           # Configurazione Python
└── .env.example             # Template variabili d'ambiente
```

## 🛠️ Tecnologie Utilizzate

### Backend
- **FastAPI**: Framework web moderno e performante
- **LangGraph**: Orchestrazione workflow multi-agente
- **LangChain**: Integrazione con LLM
- **SQLAlchemy**: ORM per PostgreSQL
- **Alembic**: Gestione migrazioni database
- **Redis**: Caching e ottimizzazione performance
- **Pydantic**: Validazione dati e configurazione
- **SSE-Starlette**: Server-Sent Events per streaming

### Frontend
- **React 19**: Libreria UI
- **TypeScript**: Type safety
- **Vite**: Build tool e dev server
- **TailwindCSS**: Styling
- **XYFlow**: Visualizzazione grafica del workflow

### Infrastructure
- **Docker & Docker Compose**: Containerizzazione
- **PostgreSQL 16**: Database relazionale
- **Redis 7**: Cache in-memory
- **Nginx**: Reverse proxy per frontend

## 🔍 Caratteristiche Avanzate

### Caching Intelligente
- Cache dei risultati per coppie data+objective identiche
- Cache delle esecuzioni per recupero rapido
- Invalidazione automatica

### Persistenza Completa
- Salvataggio di ogni iterazione nel database
- Tracciamento completo dello storico
- Possibilità di analisi retrospettiva

### Streaming in Tempo Reale
- Aggiornamenti live tramite Server-Sent Events
- Visualizzazione progressiva delle iterazioni
- Feedback immediato all'utente

### Ottimizzazione Automatica
- Stop automatico al raggiungimento della soglia
- Rilevamento di plateau (nessun miglioramento)
- Limite massimo di iterazioni configurabile

## 🔧 Risoluzione Problemi

### Errori di Conflitto Porte

#### Problema: "Bind for 0.0.0.0:5432 failed: port is already allocated"

Questo errore si verifica quando la porta 5432 di PostgreSQL è già in uso.

**Soluzione 1: Usa PostgreSQL Esistente (Consigliato)**

Se hai già PostgreSQL installato:

```bash
# Crea database e utente
psql -U postgres
```

Nel prompt psql:
```sql
CREATE USER trireason WITH PASSWORD 'trireason';
CREATE DATABASE trireason OWNER trireason;
GRANT ALL PRIVILEGES ON DATABASE trireason TO trireason;
\q
```

Salta il comando Docker per PostgreSQL e procedi solo con Redis.

**Soluzione 2: Usa una Porta Diversa**

```bash
# Mappa sulla porta 5433 invece di 5432
docker run -d -p 5433:5432 -e POSTGRES_USER=trireason -e POSTGRES_PASSWORD=trireason -e POSTGRES_DB=trireason postgres:16-alpine
```

Aggiorna `.env`:
```env
DATABASE_URL=postgresql+asyncpg://trireason:trireason@localhost:5433/trireason
```

**Soluzione 3: Ferma il Servizio Esistente**

Windows (PowerShell come Amministratore):
```powershell
Stop-Service postgresql-x64-16
```

Linux/macOS:
```bash
sudo systemctl stop postgresql
```

### Problemi con l'Ambiente Virtuale

#### Problema: Impossibile attivare su Windows PowerShell

**Errore:** "running scripts is disabled on this system"

**Soluzione:**
```powershell
# Esegui come Amministratore
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Problema: "python: command not found"

**Soluzione:**
- Windows: Usa `py -m venv venv`
- Linux/macOS: Usa `python3 -m venv venv`

### Problemi di Connessione al Database

#### Problema: Impossibile connettersi durante la migrazione

**Soluzioni:**
1. Verifica che PostgreSQL sia in esecuzione
2. Controlla che DATABASE_URL in `.env` sia corretto
3. Testa la connessione:
   ```bash
   # Verifica se la porta è in ascolto
   # Windows
   netstat -ano | findstr :5432
   
   # Linux/macOS
   lsof -i :5432
   ```

### Problemi con Docker

#### Problema: "docker: command not found"

**Soluzione:** Installa Docker Desktop da https://www.docker.com/products/docker-desktop

#### Problema: Docker daemon non in esecuzione

**Soluzione:**
- Windows/macOS: Avvia l'applicazione Docker Desktop
- Linux: `sudo systemctl start docker`

### Suggerimenti Generali

- Attiva sempre l'ambiente virtuale prima di eseguire comandi Python
- Usa Docker Compose (Opzione 1) per una configurazione più semplice
- Controlla i log per errori dettagliati: `docker logs <container-id>`

## 📝 Note

- Il sistema richiede una connessione internet attiva per comunicare con l'API OpenAI
- I costi API dipendono dal modello utilizzato e dal numero di iterazioni
- Il caching riduce significativamente i costi per richieste ripetute
- Per ambienti di produzione, configurare adeguatamente le variabili d'ambiente e i segreti

## 🤝 Contributi

Per contribuire al progetto:
1. Fork del repository
2. Crea un branch per la tua feature
3. Commit delle modifiche
4. Push al branch
5. Apri una Pull Request

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT.

---

**Sviluppato con ❤️ utilizzando FastAPI, LangGraph e React**
