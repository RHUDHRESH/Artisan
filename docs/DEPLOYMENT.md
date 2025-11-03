# Artisan Hub - Deployment Guide

## Pre-Deployment Checklist

### 1. System Requirements

- **Python:** 3.9 or higher
- **Ollama:** Latest version installed and running
- **RAM:** Minimum 8GB (16GB recommended for 4B model)
- **Storage:** 10GB free space for models and data
- **OS:** Windows, Linux, or macOS

### 2. Ollama Setup

```bash
# Verify Ollama is running
ollama list

# Pull required models
ollama pull gemma3:4b
ollama pull gemma3:1b
ollama pull gemma3:embed

# Verify all models
ollama list | grep gemma3
```

### 3. Python Environment

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 4. Configuration

Create `.env` file:
```env
SERPAPI_KEY=your_key_here
OLLAMA_BASE_URL=http://localhost:11434
CHROMA_DB_PATH=./data/chroma_db
LOG_LEVEL=INFO
```

### 5. Verify Installation

```bash
# Run deployment check
./deployment_check.sh  # Linux/Mac
.\deployment_check.ps1  # Windows

# Run tests
pytest backend/tests/test_ollama_setup.py
```

---

## Production Deployment

### Option 1: Local Deployment (Recommended)

1. **Start Ollama:**
   ```bash
   ollama serve
   ```

2. **Start Backend:**
   ```bash
   cd backend
   python main.py
   ```

3. **Serve Frontend:**
   - Option A: Open `frontend/index.html` directly
   - Option B: Use simple HTTP server:
     ```bash
     cd frontend
     python -m http.server 3000
     ```

### Option 2: Systemd Service (Linux)

Create `/etc/systemd/system/artisan-hub.service`:
```ini
[Unit]
Description=Artisan Hub API
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/artisan-hub/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable artisan-hub
sudo systemctl start artisan-hub
```

### Option 3: Docker (Future)

Docker setup can be added for containerized deployment.

---

## Security Considerations

### Production Settings

1. **CORS Configuration:**
   Update `backend/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Specific origins
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

2. **Environment Variables:**
   - Never commit `.env` file
   - Use secure secrets management
   - Rotate SERPAPI_KEY regularly

3. **Rate Limiting:**
   Consider adding rate limiting for production:
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

4. **Input Validation:**
   Always validate inputs using validators

---

## Monitoring

### Logs

Logs are stored in `data/logs/`:
- `app_YYYY-MM-DD.log` - Application logs
- Search logs in agent execution logs
- Verification logs in verifier

### Health Checks

Monitor health endpoint:
```bash
curl http://localhost:8000/health
```

### Ollama Monitoring

Check Ollama status:
```bash
ollama list
curl http://localhost:11434/api/tags
```

---

## Backup & Recovery

### Important Data to Backup

1. **ChromaDB Data:**
   ```bash
   cp -r data/chroma_db/ backup/chroma_db/
   ```

2. **User Profiles:**
   (If using Firebase, backup Firebase data)

3. **Configuration:**
   ```bash
   cp .env backup/.env
   ```

### Recovery

1. Restore ChromaDB:
   ```bash
   cp -r backup/chroma_db/* data/chroma_db/
   ```

2. Restore configuration:
   ```bash
   cp backup/.env .env
   ```

---

## Troubleshooting

### Backend Won't Start

1. Check if port 8000 is available
2. Verify Ollama is running
3. Check Python dependencies
4. Review logs in `data/logs/`

### Models Not Loading

1. Verify models installed: `ollama list`
2. Check Ollama is running: `curl http://localhost:11434/api/tags`
3. Restart Ollama service

### Search Not Working

1. Verify SERPAPI_KEY in .env
2. Check API credits at serpapi.com
3. Review search logs

### Performance Issues

1. **Slow Responses:**
   - Use 1B model for simple queries
   - Reduce number of search results
   - Enable caching

2. **High Memory Usage:**
   - Close unused browser instances
   - Limit concurrent requests
   - Use smaller batch sizes

---

## Scaling

### Horizontal Scaling

For multiple instances:
1. Use shared ChromaDB (network storage)
2. Load balancer in front
3. Shared session storage

### Vertical Scaling

1. Increase RAM for larger models
2. Use GPU acceleration (if available)
3. Optimize batch processing

---

## Maintenance

### Regular Tasks

1. **Weekly:**
   - Review logs for errors
   - Check SERPAPI credit usage
   - Clean up old cache files

2. **Monthly:**
   - Update dependencies
   - Review and optimize queries
   - Backup ChromaDB

3. **Quarterly:**
   - Review and update models
   - Performance optimization
   - Security audit

---

## Support

For issues or questions:
1. Check logs in `data/logs/`
2. Review error messages
3. Check Ollama status
4. Verify environment variables

---

## Production Checklist

- [ ] Ollama models installed and verified
- [ ] Python dependencies installed
- [ ] Environment variables configured
- [ ] CORS properly configured
- [ ] Logging configured
- [ ] Health checks working
- [ ] Backup strategy in place
- [ ] Monitoring set up
- [ ] Security measures implemented
- [ ] Documentation updated

