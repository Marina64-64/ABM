# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/recaptcha-automation.git
cd recaptcha-automation

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (optional for basic testing)
# The defaults will work for demo purposes
```

### Step 3: Run Your First Test

#### Task 1: Automation (10 runs)
```bash
python -m src.task1_automation.automation --runs 10
```

**Expected Output:**
- Browser automation starts
- reCAPTCHA solving attempts
- Results saved to `data/results/automation_results.json`
- Statistics displayed in console

#### Task 2: API Server
```bash
# Terminal 1: Start API server
uvicorn src.task2_api.app:app --reload

# Terminal 2: Test with client
python -m src.task2_api.client \
    --sitekey 6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ- \
    --pageurl https://www.google.com/recaptcha/api2/demo
```

**Expected Output:**
- API server starts on http://localhost:8000
- Client submits task and polls for result
- Token returned upon success

#### Task 3: DOM Scraping
```bash
python -m src.task3_scraping.dom_scraper \
    --url https://www.google.com/recaptcha/api2/demo
```

**Expected Output:**
- Page scraped for images and text
- Files created:
  - `data/output/allimages.json`
  - `data/output/visible_images_only.json`
  - `data/output/text_instructions.txt`

### Step 4: View API Documentation

```bash
# Start API server (if not already running)
uvicorn src.task2_api.app:app --reload

# Open browser to:
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

### Step 5: Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser
```

## 📊 Full Scale Test (250 runs)

```bash
# Run full automation test suite
python -m src.task1_automation.automation --runs 250

# This will take 2-3 hours
# Results will be saved to data/results/
```

## 🐳 Docker Quick Start

```bash
# Build and run with Docker Compose
docker-compose up -d

# Services available:
# - API: http://localhost:8000
# - RabbitMQ Management: http://localhost:15672
# - Flower (Celery Monitor): http://localhost:5555
```

## 🔧 Troubleshooting

### Issue: Playwright browser not found
```bash
playwright install chromium
```

### Issue: Permission denied on Linux
```bash
chmod +x setup.sh
./setup.sh
```

### Issue: Port 8000 already in use
```bash
# Use different port
uvicorn src.task2_api.app:app --port 8001
```

### Issue: Database locked
```bash
# Remove database file and restart
rm data/recaptcha.db
```

## 📚 Next Steps

1. **Read the Documentation**
   - [Architecture](docs/architecture.md)
   - [Task 1 Q&A](docs/task1_qa.md)

2. **Customize Configuration**
   - Edit `.env` for your proxies
   - Adjust timeouts and concurrency
   - Configure database (PostgreSQL for production)

3. **Deploy to Production**
   - Use Docker Compose or Kubernetes
   - Set up monitoring (Prometheus + Grafana)
   - Configure load balancing

## 🎯 Common Use Cases

### Use Case 1: Test with Proxy
```bash
# Edit .env to add proxy
PROXY_IPV4_HOST=your-proxy.com
PROXY_IPV4_PORT=8080
PROXY_IPV4_USER=username
PROXY_IPV4_PASSWORD=password

# Run with IPv4 proxy
python -m src.task1_automation.automation --runs 10 --proxy-type ipv4
```

### Use Case 2: API Integration
```python
import httpx

# Submit task
response = httpx.post("http://localhost:8000/recaptcha/in", json={
    "sitekey": "your-sitekey",
    "pageurl": "https://example.com"
})
task_id = response.json()["taskId"]

# Get result
result = httpx.get(f"http://localhost:8000/recaptcha/res?taskId={task_id}")
print(result.json())
```

### Use Case 3: Batch Processing
```bash
# Run multiple automation instances in parallel
for i in {1..5}; do
    python -m src.task1_automation.automation --runs 50 &
done
wait
```

## 💡 Tips

- Start with small test runs (10-20) before scaling to 250
- Monitor resource usage (CPU, memory) during runs
- Use proxies for production to avoid IP blocking
- Check logs in `data/logs/` for debugging
- API documentation at `/docs` is interactive - try it!

## 🆘 Getting Help

- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Open an issue on GitHub for bugs
- Review logs in `data/logs/` for error details

---

**Ready to go!** Start with Task 1 automation and explore from there. 🎉
