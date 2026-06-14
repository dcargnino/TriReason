# Analisi Errore Alembic: InvalidPasswordError

## Descrizione dell'Errore

```
asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "trireason"
```

L'errore si verifica quando Alembic tenta di connettersi al database PostgreSQL durante l'esecuzione di `alembic upgrade head`.

## Causa Principale

Il database PostgreSQL **non è in esecuzione** oppure le credenziali di autenticazione sono errate. Alembic sta cercando di connettersi a PostgreSQL usando le credenziali configurate in [`alembic.ini`](alembic.ini:3), ma la connessione fallisce.

## Configurazione del Database

Il file [`alembic.ini`](alembic.ini:3) contiene la stringa di connessione al database:

```ini
sqlalchemy.url = postgresql+asyncpg://trireason:trireason@localhost:5432/trireason
```

Questa configurazione indica:
- **Driver**: `postgresql+asyncpg` (PostgreSQL con driver asyncpg)
- **Username**: `trireason`
- **Password**: `trireason`
- **Host**: `localhost`
- **Porta**: `5432`
- **Database**: `trireason`

Il progetto usa Docker Compose per gestire i servizi. Il file [`docker-compose.yml`](docker-compose.yml:24-38) definisce il servizio PostgreSQL con le stesse credenziali.

## Diagnosi del Problema

L'errore indica che Alembic non riesce ad autenticarsi con PostgreSQL. Ci sono due possibili cause:

### 1. PostgreSQL non è in esecuzione
Il database PostgreSQL non è stato avviato, quindi Alembic non può connettersi.

### 2. Database non inizializzato
Il database PostgreSQL è in esecuzione, ma l'utente `trireason` o il database `trireason` non esistono ancora.

## Soluzioni

### Soluzione 1: Avviare PostgreSQL con Docker Compose (Consigliata)

Il progetto è configurato per usare Docker Compose. Avvia tutti i servizi (PostgreSQL, Redis, ecc.):

```bash
docker-compose up -d db
```

Questo comando:
- Avvia il servizio PostgreSQL in background (`-d`)
- Crea automaticamente l'utente `trireason` con password `trireason`
- Crea automaticamente il database `trireason`
- Espone PostgreSQL sulla porta `5432`

**Verifica che PostgreSQL sia in esecuzione:**
```bash
docker-compose ps
```

Dovresti vedere il servizio `db` con stato "Up" e "healthy".

### Soluzione 2: Verificare la Connessione al Database

Dopo aver avviato PostgreSQL, verifica che puoi connetterti:

```bash
docker-compose exec db psql -U trireason -d trireason
```

Se la connessione funziona, vedrai il prompt di PostgreSQL:
```
trireason=#
```

Esci con `\q`.

### Soluzione 3: PostgreSQL Locale (Se non usi Docker)

Se hai PostgreSQL installato localmente e non vuoi usare Docker:

1. **Verifica che PostgreSQL sia in esecuzione:**
   ```bash
   pg_isready -h localhost -p 5432
   ```

2. **Crea l'utente e il database:**
   ```sql
   -- Connettiti come superuser (es. postgres)
   psql -U postgres
   
   -- Crea l'utente
   CREATE USER trireason WITH PASSWORD 'trireason';
   
   -- Crea il database
   CREATE DATABASE trireason OWNER trireason;
   
   -- Esci
   \q
   ```

3. **Verifica la connessione:**
   ```bash
   psql -U trireason -d trireason -h localhost
   ```

## Workflow Completo

Ecco il workflow completo per far funzionare Alembic:

### Passo 1: Avvia PostgreSQL
```bash
docker-compose up -d db
```

### Passo 2: Verifica che PostgreSQL sia pronto
```bash
docker-compose ps
```

Attendi che lo stato sia "healthy" (potrebbe richiedere alcuni secondi).

### Passo 3: Esegui le migrazioni Alembic
```bash
alembic upgrade head
```

### Passo 4: Verifica le tabelle create
```bash
docker-compose exec db psql -U trireason -d trireason -c "\dt"
```

Dovresti vedere le tabelle create dalle migrazioni.

## Troubleshooting

### Errore: "port is already allocated"
Se la porta 5432 è già in uso:

```bash
# Trova il processo che usa la porta 5432
netstat -ano | findstr :5432

# Ferma il servizio PostgreSQL locale se è in esecuzione
# oppure modifica la porta in docker-compose.yml
```

### Errore: "database does not exist"
Se il database non esiste:

```bash
# Ricrea i container da zero
docker-compose down -v
docker-compose up -d db
```

### Errore: "connection refused"
Se PostgreSQL non risponde:

```bash
# Controlla i log del container
docker-compose logs db

# Riavvia il servizio
docker-compose restart db
```

## Prossimi Passi

1. Avvia PostgreSQL: `docker-compose up -d db`
2. Attendi che sia "healthy": `docker-compose ps`
3. Esegui le migrazioni: `alembic upgrade head`
4. Verifica le tabelle: `docker-compose exec db psql -U trireason -d trireason -c "\dt"`

## Diagramma del Flusso

```mermaid
graph TD
    A[Esegui alembic upgrade head] --> B{PostgreSQL in esecuzione?}
    B -->|No| C[docker-compose up -d db]
    B -->|Sì| D{Database trireason esiste?}
    C --> E[Attendi healthy status]
    E --> F[Esegui alembic upgrade head]
    D -->|No| G[Crea database manualmente]
    D -->|Sì| H{Credenziali corrette?}
    G --> F
    H -->|No| I[Verifica alembic.ini]
    H -->|Sì| F
    I --> F
    F --> J[Migrazioni completate]
```
