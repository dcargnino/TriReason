# Installation Troubleshooting Guide

## Port Conflict Errors

### Problem: "Bind for 0.0.0.0:5432 failed: port is already allocated"

This error occurs when trying to start PostgreSQL via Docker, but port 5432 is already in use.

### Solutions:

#### Solution 1: Use Existing PostgreSQL Installation (Recommended if you have PostgreSQL installed)

If you already have PostgreSQL installed locally, you can use it instead of running it in Docker:

1. **Verify PostgreSQL is running:**
   ```bash
   # Windows (PowerShell)
   Get-Service postgresql*
   
   # Windows (cmd.exe)
   sc query postgresql*
   
   # Linux/macOS
   sudo systemctl status postgresql
   # or
   pg_isready
   ```

2. **Create the database and user:**
   ```bash
   # Connect to PostgreSQL
   psql -U postgres
   
   # In psql prompt, run:
   CREATE USER trireason WITH PASSWORD 'trireason';
   CREATE DATABASE trireason OWNER trireason;
   GRANT ALL PRIVILEGES ON DATABASE trireason TO trireason;
   \q
   ```

3. **Update your `.env` file** to use the local PostgreSQL:
   ```env
   DATABASE_URL=postgresql+asyncpg://trireason:trireason@localhost:5432/trireason
   ```

4. **Skip the Docker PostgreSQL command** and proceed with Redis:
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

#### Solution 2: Use Different Ports for Docker Containers

Map Docker containers to different host ports:

```bash
# PostgreSQL on port 5433 instead of 5432
docker run -d -p 5433:5432 -e POSTGRES_USER=trireason -e POSTGRES_PASSWORD=trireason -e POSTGRES_DB=trireason postgres:16-alpine

# Redis on port 6380 instead of 6379 (if needed)
docker run -d -p 6380:6379 redis:7-alpine
```

Then update your `.env` file:
```env
DATABASE_URL=postgresql+asyncpg://trireason:trireason@localhost:5433/trireason
REDIS_URL=redis://localhost:6380/0
```

#### Solution 3: Stop Existing PostgreSQL Service

If you don't need the existing PostgreSQL instance:

**Windows:**
```powershell
# PowerShell (as Administrator)
Stop-Service postgresql-x64-16  # Adjust version number as needed

# Or disable it permanently
Set-Service postgresql-x64-16 -StartupType Disabled
```

**Linux/macOS:**
```bash
# Stop PostgreSQL
sudo systemctl stop postgresql

# Or disable it permanently
sudo systemctl disable postgresql
```

Then retry the Docker command.

#### Solution 4: Find and Stop Conflicting Docker Container

Check if another Docker container is using the port:

```bash
# List all running containers
docker ps

# Stop specific container
docker stop <container-id>

# Or stop all containers
docker stop $(docker ps -q)
```

### Problem: "Bind for 0.0.0.0:6379 failed: port is already allocated" (Redis)

Same solutions apply for Redis port 6379:

1. Use existing Redis installation
2. Map to different port: `docker run -d -p 6380:6379 redis:7-alpine`
3. Stop existing Redis service
4. Stop conflicting Docker container

## Virtual Environment Issues

### Problem: "python: command not found" or "python3: command not found"

**Solution:**
- On Windows: Use `py` instead of `python`
- On Linux/macOS: Use `python3` instead of `python`

```bash
# Windows
py -m venv venv

# Linux/macOS
python3 -m venv venv
```

### Problem: Cannot activate virtual environment on Windows PowerShell

**Error:** "cannot be loaded because running scripts is disabled on this system"

**Solution:** Enable script execution:
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then retry activation:
```powershell
venv\Scripts\Activate.ps1
```

### Problem: pip install fails with permission errors

**Solution:** Ensure virtual environment is activated (you should see `(venv)` in your prompt)

If still failing:
```bash
# Use --user flag (not recommended in venv, but works as fallback)
pip install --user -e .
```

## Docker Issues

### Problem: "docker: command not found"

**Solution:** Install Docker Desktop from https://www.docker.com/products/docker-desktop

### Problem: Docker daemon not running

**Solution:**
- Windows/macOS: Start Docker Desktop application
- Linux: `sudo systemctl start docker`

## Database Migration Issues

### Problem: "alembic: command not found"

**Solution:** Ensure virtual environment is activated and dependencies are installed:
```bash
# Activate venv first
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -e .

# Retry migration
alembic upgrade head
```

### Problem: Cannot connect to database during migration

**Solution:**
1. Verify PostgreSQL is running
2. Check `.env` file has correct DATABASE_URL
3. Test connection:
   ```bash
   # Install psycopg2 for testing
   pip install psycopg2-binary
   
   # Test connection (Python)
   python -c "import psycopg2; conn = psycopg2.connect('postgresql://trireason:trireason@localhost:5432/trireason'); print('Connected!')"
   ```

## Frontend Installation Issues

### Problem: "npm: command not found"

**Solution:** Install Node.js from https://nodejs.org/ (version 18 or higher)

### Problem: npm install fails with EACCES errors

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Retry installation
cd frontend
npm install
```

## General Tips

1. **Always activate virtual environment** before running Python commands
2. **Check port availability** before starting services:
   ```bash
   # Windows
   netstat -ano | findstr :5432
   netstat -ano | findstr :6379
   
   # Linux/macOS
   lsof -i :5432
   lsof -i :6379
   ```
3. **Use Docker Compose** (Option 1) for easier setup - it handles all services automatically
4. **Check logs** for detailed error messages:
   ```bash
   # Docker logs
   docker logs <container-id>
   
   # Application logs
   tail -f logs/app.log  # if logging to file
   ```
