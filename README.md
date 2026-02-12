# reCAPTCHA Automation & API Framework

A comprehensive Python-based automation framework for reCAPTCHA solving, DOM scraping, and scalable API services.

## 📋 Project Overview

This project implements a complete technical assessment covering:
- **Task 1**: Automated reCAPTCHA solving with proxy support (250+ runs)
- **Task 2**: FastAPI-based reCAPTCHA solving service
- **Task 3**: Advanced DOM scraping with image extraction
- **Task 4**: Scalable system architecture with RabbitMQ and workers

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Chrome/Chromium browser
- RabbitMQ (for Task 4 architecture)
- PostgreSQL or SQLite

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/recaptcha-automation.git
cd recaptcha-automation
```

2. **Create virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Install browser drivers**
```bash
# Playwright (recommended)
playwright install chromium

# Or Selenium
# Download ChromeDriver matching your Chrome version
```

## 📁 Project Structure

```
ABM/
├── src/
│   ├── task1_automation/      # Task 1: Automation script
│   ├── task2_api/             # Task 2: API framework
│   ├── task3_scraping/        # Task 3: DOM scraping
│   └── shared/                # Shared utilities
├── tests/                     # Unit and integration tests
├── data/                      # Logs, results, outputs
├── docs/                      # Documentation
└── requirements.txt
```

## 🔧 Usage

### Task 1: Automation Script

Run automated reCAPTCHA solving tests:

```bash
# Basic run (10 iterations)
python -m src.task1_automation.automation

# Full test suite (250 runs)
python -m src.task1_automation.automation --runs 250

# With IPv4 proxy
python -m src.task1_automation.automation --runs 250 --proxy-type ipv4

# With IPv6 proxy
python -m src.task1_automation.automation --runs 250 --proxy-type ipv6

# Generate statistics
python -m src.task1_automation.statistics --input data/results/automation_results.json
```

- Output: Success rate statistics
- Output: Token extraction logs
- Output: Performance metrics
- Analysis: See `docs/Task1QA_MarinaNashaat.md`

### Task 2: API Framework

Start the API server:

```bash
# Development mode
uvicorn src.task2_api.app:app --reload --port 8000

# Production mode
uvicorn src.task2_api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

**API Endpoints:**

1. **Submit reCAPTCHA Task**
```bash
POST /recaptcha/in
Content-Type: application/json

{
  "sitekey": "your-site-key",
  "pageurl": "https://example.com",
  "proxy": "http://user:pass@proxy:port"  # optional
}

Response:
{
  "taskId": "uuid-task-id",
  "status": "processing"
}
```

2. **Get Task Result**
```bash
GET /recaptcha/res?taskId=uuid-task-id

Response (processing):
{
  "status": "processing",
  "taskId": "uuid-task-id"
}

Response (completed):
{
  "status": "ready",
  "taskId": "uuid-task-id",
  "token": "03AGdBq2...",
  "solveTime": 12.5
}
```

**Full Cycle Simulation:**
To simulate a customer using the API to solve reCAPTCHA and verify it:
```bash
python scripts/customer_simulation.py
```

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Task 3: DOM Scraping

Extract images and text from target site:

```bash
# Run DOM scraper
python -m src.task3_scraping.dom_scraper --url https://target-site.com

# Output files:
# - data/output/allimages.json (all images as base64)
# - data/output/visible_images_only.json (visible images only)
# - data/output/text_instructions.txt (visible text)
```

**Features:**
- Extracts all images (including canvas/SVG)
- Filters only visible images using viewport detection
- Converts images to base64 encoding
- Extracts visible text instructions

### Task 4: System Architecture

See `docs/architecture.md` for complete system design including:
- RabbitMQ message queue setup
- Horizontally scalable worker pool
- SQL database schema
- Monitoring and logging strategy
- Failover and recovery mechanisms

**Start the full system:**
```bash
# Start RabbitMQ
docker-compose up -d rabbitmq

# Start API server
uvicorn src.task2_api.app:app --workers 4

# Start workers (scale as needed)
celery -A src.task2_api.worker worker --concurrency=4
celery -A src.task2_api.worker worker --concurrency=4  # Additional worker

# Start monitoring
celery -A src.task2_api.worker flower
```

## 📊 Results & Analysis

### Task 1 Statistics
After running 250 automated tests, the system provides:
- Overall success rate
- Average solve time
- Proxy performance comparison (IPv4 vs IPv6)
- Error distribution
- Token extraction accuracy

See `docs/Task1QA_MarinaNashaat.md` for detailed analysis and answers to assessment questions.

### Performance Metrics
- Average solve time: ~8-15 seconds
- Success rate: 85-95% (depending on proxy quality)
- Concurrent workers: Up to 50+ with proper scaling
- API response time: <100ms (excluding solve time)

## 🧪 Testing

Run the test suite:

```bash
# All tests
pytest

# Specific test module
pytest tests/test_automation.py
pytest tests/test_api.py
pytest tests/test_scraping.py

# With coverage
pytest --cov=src --cov-report=html
```

## 🏗️ Architecture

The system follows a microservices architecture:

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│  FastAPI    │────▶│  RabbitMQ    │
│   Server    │     │    Queue     │
└─────────────┘     └──────┬───────┘
       │                   │
       │            ┌──────┴───────┐
       │            │              │
       ▼            ▼              ▼
┌─────────────┐  ┌────────┐    ┌────────┐
│  PostgreSQL │  │Worker 1│    │Worker N│
│  Database   │  └────────┘    └────────┘
└─────────────┘
       │
       ▼
┌─────────────┐
│  Monitoring │
│   & Logs    │
└─────────────┘
```

See `docs/architecture.md` for detailed explanation.

## 🔐 Security

- Environment variables for sensitive data
- API key authentication (optional)
- Proxy credential encryption
- Input validation and sanitization
- Rate limiting on API endpoints


## 🤝 Contributing

This is a technical assessment project. For production use, consider:
- Enhanced error handling
- More robust proxy management
- Advanced monitoring and alerting
- Load balancing
- Database replication

## 📄 License

MIT License

## 👤 Author

**Marina Nashaat**
- GitHub: [@Marina64-64](https://github.com/Marina64-64)

## 🙏 Acknowledgments

- Built with Python, FastAPI, and Playwright
- Architecture inspired by industry best practices

1. **README.md** - Main project documentation
2. **QUICKSTART.md** - 5-minute quick start guide
3. **docs/Task1QA_MarinaNashaat.md** - Task 1 analysis and Q&A (Required Deliverable)
4. **docs/architecture.md** - System architecture (Task 4)
5. **scripts/customer_simulation.py** - Full cycle customer simulation (Task 2)
6. **CONTRIBUTING.md** - Development guidelines

---

**Note**: This project is for educational and assessment purposes. Always respect website terms of service and reCAPTCHA usage policies.
