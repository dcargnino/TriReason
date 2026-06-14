# Analisi: Supporto URL API Personalizzato per TriReason

## 📋 Sommario Esecutivo

**Obiettivo**: Permettere l'esecuzione di TriReason con API OpenAI-compatible locali (es. LM Studio, Ollama, LocalAI, vLLM) invece di utilizzare esclusivamente l'API OpenAI ufficiale.

**Fattibilità**: ✅ **COMPLETAMENTE POSSIBILE**

Il client `AsyncOpenAI` della libreria `openai` supporta nativamente la configurazione di un `base_url` personalizzato, rendendo questa modifica semplice e diretta.

---

## 🔍 Analisi dell'Architettura Attuale

### Struttura Corrente

Il progetto utilizza il client OpenAI in modo centralizzato attraverso il file [`src/trireason/agents/llm.py`](src/trireason/agents/llm.py:1):

```python
from openai import AsyncOpenAI
from trireason.config import settings

_client: AsyncOpenAI | None = None

def get_openai_client() -> AsyncOpenAI:
    """Return a singleton AsyncOpenAI client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client
```

### Configurazione Attuale

Il file [`src/trireason/config.py`](src/trireason/config.py:1) gestisce le configurazioni:

```python
class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    # ... altre configurazioni
```

### Utilizzo del Client

Tutti e tre gli agenti utilizzano la funzione [`chat_json()`](src/trireason/agents/llm.py:18) che internamente chiama [`get_openai_client()`](src/trireason/agents/llm.py:10):

- [`src/trireason/agents/generator.py`](src/trireason/agents/generator.py:1)
- [`src/trireason/agents/critic.py`](src/trireason/agents/critic.py:1)
- [`src/trireason/agents/refiner.py`](src/trireason/agents/refiner.py:1)

---

## 💡 Soluzione Proposta

### 1. Modifiche alla Configurazione

Aggiungere un nuovo parametro opzionale in [`config.py`](src/trireason/config.py:6):

```python
class Settings(BaseSettings):
    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_base_url: str | None = None  # ← NUOVO PARAMETRO
    # ... resto della configurazione
```

### 2. Modifiche al Client LLM

Aggiornare [`llm.py`](src/trireason/agents/llm.py:10) per utilizzare il `base_url` se fornito:

```python
def get_openai_client() -> AsyncOpenAI:
    """Return a singleton AsyncOpenAI client."""
    global _client
    if _client is None:
        client_kwargs = {"api_key": settings.openai_api_key}
        
        # Se è configurato un base_url personalizzato, usalo
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        
        _client = AsyncOpenAI(**client_kwargs)
    return _client
```

### 3. Aggiornamento File di Configurazione

Aggiornare [`.env.example`](.env.example:1) per documentare la nuova opzione:

```env
# OpenAI / LLM Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
# Optional: Custom API endpoint for OpenAI-compatible APIs (e.g., LM Studio, Ollama, LocalAI)
# OPENAI_BASE_URL=http://localhost:1234/v1
```

---

## 🎯 Casi d'Uso Supportati

### 1. **LM Studio**
```env
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
OPENAI_MODEL=local-model
```

### 2. **Ollama con OpenAI Compatibility**
```env
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=llama3.2
```

### 3. **LocalAI**
```env
OPENAI_BASE_URL=http://localhost:8080/v1
OPENAI_API_KEY=local
OPENAI_MODEL=gpt-3.5-turbo
```

### 4. **vLLM Server**
```env
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=vllm
OPENAI_MODEL=meta-llama/Llama-3.2-8B-Instruct
```

### 5. **OpenAI Ufficiale** (comportamento predefinito)
```env
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o
# OPENAI_BASE_URL non impostato
```

---

## 📊 Vantaggi della Soluzione

### ✅ Vantaggi Tecnici

1. **Minime Modifiche**: Solo 3 file da modificare
2. **Retrocompatibilità**: Funziona esattamente come prima se `OPENAI_BASE_URL` non è impostato
3. **Flessibilità**: Supporta qualsiasi API OpenAI-compatible
4. **Centralizzato**: Tutte le modifiche in un unico punto ([`llm.py`](src/trireason/agents/llm.py:1))
5. **Type-Safe**: Utilizza i tipi Python corretti

### 💰 Vantaggi Economici

1. **Zero Costi API**: Esecuzione completamente locale
2. **Privacy**: Nessun dato inviato a servizi esterni
3. **Controllo**: Pieno controllo sul modello utilizzato
4. **Offline**: Possibilità di lavorare senza connessione internet

### 🚀 Vantaggi Operativi

1. **Sviluppo**: Test locali senza consumare crediti API
2. **Produzione**: Deployment on-premise per dati sensibili
3. **Sperimentazione**: Facile testare diversi modelli locali
4. **Scalabilità**: Controllo completo sull'infrastruttura

---

## 🔧 Dettagli Implementativi

### Modifiche Necessarie

#### File 1: [`src/trireason/config.py`](src/trireason/config.py:1)

**Linea da modificare**: Dopo la linea 9

**Modifica**:
```python
# Prima
openai_model: str = "gpt-4o"

# Dopo
openai_model: str = "gpt-4o"
openai_base_url: str | None = None
```

#### File 2: [`src/trireason/agents/llm.py`](src/trireason/agents/llm.py:1)

**Funzione da modificare**: [`get_openai_client()`](src/trireason/agents/llm.py:10)

**Modifica completa**:
```python
def get_openai_client() -> AsyncOpenAI:
    """Return a singleton AsyncOpenAI client.
    
    If settings.openai_base_url is set, uses that as the base URL
    for OpenAI-compatible APIs (e.g., LM Studio, Ollama, LocalAI).
    """
    global _client
    if _client is None:
        client_kwargs = {"api_key": settings.openai_api_key}
        
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        
        _client = AsyncOpenAI(**client_kwargs)
    return _client
```

#### File 3: [`.env.example`](.env.example:1)

**Sezione da modificare**: Linee 1-3

**Modifica**:
```env
# OpenAI / LLM Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
# Optional: Custom API endpoint for OpenAI-compatible local APIs
# Examples:
#   LM Studio:  http://localhost:1234/v1
#   Ollama:     http://localhost:11434/v1
#   LocalAI:    http://localhost:8080/v1
#   vLLM:       http://localhost:8000/v1
# OPENAI_BASE_URL=http://localhost:1234/v1
```

---

## 🧪 Testing e Validazione

### Test Manuali Consigliati

1. **Test con OpenAI Ufficiale** (regressione)
   ```bash
   # .env
   OPENAI_API_KEY=sk-proj-...
   OPENAI_MODEL=gpt-4o
   # OPENAI_BASE_URL non impostato
   ```

2. **Test con LM Studio**
   ```bash
   # Avvia LM Studio e carica un modello
   # .env
   OPENAI_BASE_URL=http://localhost:1234/v1
   OPENAI_API_KEY=lm-studio
   OPENAI_MODEL=local-model
   ```

3. **Test con Ollama**
   ```bash
   # Avvia Ollama: ollama serve
   # .env
   OPENAI_BASE_URL=http://localhost:11434/v1
   OPENAI_API_KEY=ollama
   OPENAI_MODEL=llama3.2
   ```

### Test Automatici

Aggiungere test unitari in [`tests/unit/test_agents.py`](tests/unit/test_agents.py:1):

```python
def test_custom_base_url_configuration():
    """Test that custom base_url is properly configured."""
    from trireason.config import settings
    from trireason.agents.llm import get_openai_client
    
    # Mock settings
    settings.openai_base_url = "http://localhost:1234/v1"
    
    client = get_openai_client()
    assert client.base_url == "http://localhost:1234/v1"
```

---

## 📚 Documentazione Aggiuntiva

### Aggiornamenti al README

Aggiungere una nuova sezione nel [`README.md`](README.md:1) dopo la sezione "Configurazione":

```markdown
### Utilizzo con API Locali

TriReason supporta l'utilizzo di API OpenAI-compatible locali per esecuzione completamente offline e senza costi.

#### Configurazione per LM Studio

1. Avvia LM Studio e carica un modello
2. Abilita il server locale (di default su porta 1234)
3. Configura il file `.env`:
   ```env
   OPENAI_BASE_URL=http://localhost:1234/v1
   OPENAI_API_KEY=lm-studio
   OPENAI_MODEL=nome-del-modello-locale
   ```

#### Configurazione per Ollama

1. Installa e avvia Ollama: `ollama serve`
2. Scarica un modello: `ollama pull llama3.2`
3. Configura il file `.env`:
   ```env
   OPENAI_BASE_URL=http://localhost:11434/v1
   OPENAI_API_KEY=ollama
   OPENAI_MODEL=llama3.2
   ```

#### Altri Provider Supportati

Qualsiasi servizio che implementa l'API OpenAI è compatibile:
- LocalAI
- vLLM
- Text Generation WebUI (con estensione OpenAI)
- FastChat
- E molti altri...
```

---

## ⚠️ Considerazioni e Limitazioni

### Compatibilità dei Modelli

1. **JSON Mode**: Non tutti i modelli locali supportano `response_format={"type": "json_object"}`
   - **Soluzione**: Potrebbe essere necessario rendere questo parametro opzionale
   - **Impatto**: Gli agenti potrebbero ricevere risposte non-JSON

2. **Qualità del Modello**: Modelli locali più piccoli potrebbero non performare come GPT-4
   - **Raccomandazione**: Usare modelli con almeno 7B parametri
   - **Modelli consigliati**: Llama 3.2 8B, Mistral 7B, Qwen 2.5 7B

3. **Temperatura e Parametri**: Alcuni server potrebbero ignorare certi parametri
   - **Impatto**: Risultati potrebbero variare rispetto a OpenAI

### Performance

1. **Velocità**: Modelli locali su CPU saranno più lenti
   - **Raccomandazione**: GPU consigliata per performance accettabili
   
2. **Memoria**: Modelli grandi richiedono molta RAM/VRAM
   - **Requisiti minimi**: 16GB RAM per modelli 7B, 32GB+ per modelli 13B+

### Gestione Errori

Potrebbe essere utile aggiungere logging più dettagliato per debug:

```python
def get_openai_client() -> AsyncOpenAI:
    """Return a singleton AsyncOpenAI client."""
    global _client
    if _client is None:
        client_kwargs = {"api_key": settings.openai_api_key}
        
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
            logger.info(f"Using custom OpenAI base URL: {settings.openai_base_url}")
        else:
            logger.info("Using official OpenAI API")
        
        _client = AsyncOpenAI(**client_kwargs)
    return _client
```

---

## 🎯 Miglioramenti Futuri (Opzionali)

### 1. Supporto JSON Mode Opzionale

Rendere il `response_format` configurabile per modelli che non lo supportano:

```python
class Settings(BaseSettings):
    # ...
    openai_force_json_mode: bool = True  # Nuovo parametro
```

### 2. Timeout Configurabile

Per modelli locali lenti:

```python
class Settings(BaseSettings):
    # ...
    openai_timeout: int = 60  # Secondi
```

### 3. Retry Logic

Per gestire instabilità di server locali:

```python
class Settings(BaseSettings):
    # ...
    openai_max_retries: int = 3
```

### 4. Multiple Providers

Supporto per più provider simultanei (avanzato):

```python
class Settings(BaseSettings):
    # ...
    llm_providers: dict[str, dict] = {
        "openai": {"api_key": "...", "base_url": None},
        "local": {"api_key": "local", "base_url": "http://localhost:1234/v1"}
    }
    default_provider: str = "openai"
```

---

## 📋 Checklist Implementazione

### Modifiche Obbligatorie

- [ ] Aggiungere `openai_base_url: str | None = None` in [`config.py`](src/trireason/config.py:6)
- [ ] Modificare [`get_openai_client()`](src/trireason/agents/llm.py:10) per supportare `base_url`
- [ ] Aggiornare [`.env.example`](.env.example:1) con documentazione ed esempi

### Documentazione

- [ ] Aggiungere sezione "Utilizzo con API Locali" nel [`README.md`](README.md:1)
- [ ] Documentare provider supportati
- [ ] Aggiungere esempi di configurazione
- [ ] Documentare limitazioni e requisiti

### Testing

- [ ] Test con OpenAI ufficiale (regressione)
- [ ] Test con LM Studio
- [ ] Test con Ollama
- [ ] Test con `base_url` non impostato (comportamento predefinito)
- [ ] Test gestione errori (URL non valido, server non raggiungibile)

### Opzionale

- [ ] Aggiungere logging per debug
- [ ] Aggiungere test automatici
- [ ] Considerare supporto JSON mode opzionale
- [ ] Documentare modelli consigliati

---

## 🚀 Stima Complessità

| Aspetto | Complessità | Note |
|---------|-------------|------|
| **Modifiche Codice** | 🟢 Bassa | Solo 3 file, ~10 righe di codice |
| **Testing** | 🟡 Media | Richiede setup di server locali |
| **Documentazione** | 🟡 Media | Necessaria documentazione dettagliata |
| **Rischio Regressione** | 🟢 Basso | Modifiche retrocompatibili |
| **Manutenibilità** | 🟢 Alta | Soluzione pulita e centralizzata |

---

## 📝 Conclusioni

### Risposta alla Richiesta

**SÌ, è completamente possibile definire un URL custom per le chiamate API in locale.**

La libreria `openai` supporta nativamente questa funzionalità attraverso il parametro `base_url` del client `AsyncOpenAI`. Le modifiche necessarie sono:

1. **Minime**: Solo 3 file da modificare
2. **Sicure**: Completamente retrocompatibili
3. **Flessibili**: Supportano qualsiasi API OpenAI-compatible

### Raccomandazioni

1. **Implementare subito**: Le modifiche sono semplici e a basso rischio
2. **Testare accuratamente**: Verificare con diversi provider locali
3. **Documentare bene**: Fornire esempi chiari per gli utenti
4. **Considerare miglioramenti futuri**: JSON mode opzionale, timeout configurabili

### Prossimi Passi

1. Approvare questo piano di analisi
2. Procedere con l'implementazione delle modifiche
3. Testare con provider locali comuni (LM Studio, Ollama)
4. Aggiornare la documentazione
5. Rilasciare la feature

---

**Documento creato**: 2026-02-09  
**Versione**: 1.0  
**Stato**: ✅ Pronto per implementazione
