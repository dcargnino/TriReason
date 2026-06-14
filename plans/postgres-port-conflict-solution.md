# Risoluzione Conflitto Porta PostgreSQL

## Problema

L'errore indica che la porta `5432` è già occupata da un'altra istanza di PostgreSQL:

```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

Hai già un'istanza PostgreSQL in esecuzione (probabilmente installata localmente su Windows) che sta usando la porta 5432.

## Soluzioni Possibili

### Soluzione 1: Usare l'Istanza PostgreSQL Esistente (Consigliata)

Se hai già PostgreSQL in esecuzione, puoi usarlo direttamente senza Docker. Devi solo creare l'utente e il database.

#### Passo 1: Verifica la connessione a PostgreSQL locale

```bash
psql -U postgres -h localhost
```

Se richiede una password, usa quella che hai impostato durante l'installazione di PostgreSQL.

#### Passo 2: Crea l'utente e il database

Una volta connesso a PostgreSQL, esegui questi comandi SQL:

```sql
-- Crea l'utente trireason
CREATE USER trireason WITH PASSWORD 'trireason';

-- Crea il database trireason
CREATE DATABASE trireason OWNER trireason;

-- Concedi tutti i privilegi
GRANT ALL PRIVILEGES ON DATABASE trireason TO trireason;

-- Esci
\q
```

#### Passo 3: Verifica la connessione

```bash
psql -U trireason -d trireason -h localhost
```

Se funziona, sei pronto per eseguire Alembic:

```bash
alembic upgrade head
```

### Soluzione 2: Cambiare Porta per Docker PostgreSQL

Se vuoi usare Docker PostgreSQL su una porta diversa, modifica [`docker-compose.yml`](docker-compose.yml:30-31).

#### Modifica docker-compose.yml

Cambia la porta esposta da `5432:5432` a `5433:5432` (o un'altra porta libera):

```yaml
db:
  image: postgres:16-alpine
  environment:
    POSTGRES_USER: trireason
    POSTGRES_PASSWORD: trireason
    POSTGRES_DB: trireason
  ports:
    - "5433:5432"  # Cambia qui: porta_host:porta_container
  volumes:
    - pgdata:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U trireason"]
    interval: 5s
    timeout: 3s
    retries: 5
```

#### Modifica alembic.ini

Aggiorna la porta in [`alembic.ini`](alembic.ini:3):

```ini
sqlalchemy.url = postgresql+asyncpg://trireason:trireason@localhost:5433/trireason
```

#### Modifica .env (se esiste)

Se hai un file `.env`, aggiorna anche lì:

```env
DATABASE_URL=postgresql+asyncpg://trireason:trireason@localhost:5433/trireason
```

#### Avvia Docker PostgreSQL

```bash
docker-compose up -d db
```

### Soluzione 3: Fermare PostgreSQL Locale

Se non hai bisogno dell'istanza PostgreSQL locale, puoi fermarla temporaneamente.

#### Windows - Fermare il Servizio PostgreSQL

**Opzione A: Tramite Services (GUI)**
1. Premi `Win + R`
2. Digita `services.msc` e premi Invio
3. Cerca "postgresql" nella lista
4. Clic destro → "Stop"

**Opzione B: Tramite PowerShell (come Amministratore)**
```powershell
# Lista i servizi PostgreSQL
Get-Service | Where-Object {$_.Name -like "*postgres*"}

# Ferma il servizio (sostituisci con il nome corretto)
Stop-Service -Name "postgresql-x64-16"
```

**Opzione C: Tramite cmd (come Amministratore)**
```cmd
# Lista i servizi PostgreSQL
sc query | findstr postgres

# Ferma il servizio (sostituisci con il nome corretto)
net stop postgresql-x64-16
```

Dopo aver fermato il servizio, puoi avviare Docker PostgreSQL:

```bash
docker-compose up -d db
```

## Raccomandazione

**Usa la Soluzione 1** (PostgreSQL locale esistente) perché:

1. ✅ Non richiede modifiche ai file di configurazione
2. ✅ Più semplice e veloce
3. ✅ Evita conflitti di porta
4. ✅ Usa le risorse già disponibili

## Workflow Consigliato

### Passo 1: Crea utente e database in PostgreSQL locale

```bash
# Connettiti come superuser
psql -U postgres -h localhost

# Esegui i comandi SQL
CREATE USER trireason WITH PASSWORD 'trireason';
CREATE DATABASE trireason OWNER trireason;
GRANT ALL PRIVILEGES ON DATABASE trireason TO trireason;
\q
```

### Passo 2: Verifica la connessione

```bash
psql -U trireason -d trireason -h localhost
```

Se richiede una password, digita: `trireason`

### Passo 3: Esegui le migrazioni Alembic

```bash
alembic upgrade head
```

### Passo 4: Verifica le tabelle create

```bash
psql -U trireason -d trireason -h localhost -c "\dt"
```

## Troubleshooting

### Errore: "psql: command not found"

PostgreSQL non è nel PATH. Trova l'installazione di PostgreSQL (es. `C:\Program Files\PostgreSQL\16\bin`) e:

**Opzione A: Usa il path completo**
```cmd
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h localhost
```

**Opzione B: Aggiungi al PATH temporaneamente**
```cmd
set PATH=%PATH%;C:\Program Files\PostgreSQL\16\bin
psql -U postgres -h localhost
```

### Errore: "password authentication failed"

Se non ricordi la password di PostgreSQL:

1. Trova il file `pg_hba.conf` (es. `C:\Program Files\PostgreSQL\16\data\pg_hba.conf`)
2. Cambia temporaneamente `md5` in `trust` per la connessione locale
3. Riavvia il servizio PostgreSQL
4. Connettiti senza password e cambia la password
5. Ripristina `md5` in `pg_hba.conf`
6. Riavvia nuovamente il servizio

### Errore: "database already exists"

Se il database esiste già, puoi:

**Opzione A: Usare il database esistente**
```bash
alembic upgrade head
```

**Opzione B: Ricreare il database**
```sql
DROP DATABASE trireason;
CREATE DATABASE trireason OWNER trireason;
```

## Diagramma delle Soluzioni

```mermaid
graph TD
    A[Porta 5432 già in uso] --> B{Quale soluzione?}
    B -->|Soluzione 1| C[Usa PostgreSQL locale]
    B -->|Soluzione 2| D[Cambia porta Docker]
    B -->|Soluzione 3| E[Ferma PostgreSQL locale]
    
    C --> C1[Crea utente e database]
    C1 --> C2[Esegui alembic upgrade head]
    
    D --> D1[Modifica docker-compose.yml]
    D1 --> D2[Modifica alembic.ini]
    D2 --> D3[Avvia Docker PostgreSQL]
    D3 --> C2
    
    E --> E1[Ferma servizio PostgreSQL]
    E1 --> E2[Avvia Docker PostgreSQL]
    E2 --> C2
    
    C2 --> F[Migrazioni completate]
```
