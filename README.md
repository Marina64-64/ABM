# reCAPTCHA Automation & Verification Framework

A professional Python-based framework for reCAPTCHA behavioral verification, DOM analysis, and automated interaction testing.

This framework is a production-grade solution for analyzing reCAPTCHA behavior and performing automated interaction testing. It was developed to demonstrate best practices in:
- **Interaction Simulation**: Analyzing reCAPTCHA v3 score behavior under automated conditions.
- **RESTful Service Design**: A clean, scalable API built with FastAPI and Pydantic v2.
- **DOM Intelligence**: Viewport-aware analysis to mimic human visual data extraction.
- **Enterprise Architecture**: A distributed worker system using RabbitMQ and Celery.

## 🏗️ System Architecture (Task 4)

The framework utilizes a decoupled, event-driven architecture designed for high throughput and fault tolerance:

```mermaid
graph TD
    User([External Client]) -->|HTTP POST| API[FastAPI Service]
    API -->|Async Task| Broker[RabbitMQ Message Queue]
    API -.->|Query| DB[(PostgreSQL)]
    
    Broker -->|Consume| W1[Worker Node 1]
    Broker -->|Consume| W2[Worker Node 2]
    
    W1 -->|Automation| Site{Target Site}
    W2 -->|Automation| Site
    
    W1 -->|Update| DB
    W2 -->|Update| DB
```

Full architecture specifications are available in [docs/architecture.md](docs/architecture.md).

## 🚀 Quick Start (Production Setup)

The entire environment (DB, Queue, API, and Workers) can be launched using Docker:

```bash
# 1. Start all services
docker-compose up -d

# 2. Access Documentation
# API: http://localhost:8000/docs
# Queue Monitor: http://localhost:15672 (guest/guest)
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Marina64-64/ABM.git
cd ABM
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

- **Verification Run (Recommended for Reviewers)**:
  ```bash
  python -m src.task1_automation.automation --runs 250
  ```
- **Results Output**: The final behavioral metrics are logged to `data/results/automation_results.json`.
- **Analysis Report**: Comprehensive findings are available in `docs/Task1QA_MarinaNashaat.md`.

**Sample Execution Log:**
```text
INFO | Run 1: Navigating to https://cd.captchaaiplus.com/recaptcha-v3-2.php
INFO | Run 1: Clicking 'Run reCAPTCHA v3 test' button
SUCCESS | Run 1: Verification Successful. Score: 0.9
INFO | Run 2: Navigating to https://cd.captchaaiplus.com/recaptcha-v3-2.php
...
SUCCESS | Completed 250 verification runs. Average Score: 0.82
```

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
To simulate a user interaction flow and verify the automated response:
```bash
python scripts/customer_simulation.py
```

**Example API Response (Task 2):**
```json
{
  "status": "ready",
  "taskId": "550e8400-e29b-41d4-a716-446655440000",
  "token": "03AGdBq25S-...",
  "solveTime": 12.35
}
```

**Example Scraper Output (Task 3):**
```json
[
  {
    "index": 0,
    "src": "https://example.com/logo.png",
    "base64": "iVBORw0KGgoAAAANSUhEUgAA...",
    "type": "img"
  }
]
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
# Total system launch (Recommended)
docker-compose up -d

# Manual start (optional)
uvicorn src.task2_api.app:app --workers 4
celery -A src.task2_api.worker worker --concurrency=4
```

## 📊 Performance Benchmarks (Observed)

The following metrics were observed in a controlled test environment using a suite of **250 automated runs**. *Actual results may vary based on site configuration, network latency, and IP reputation.*

| Metric | Measured Result |
|--------|-----------------|
| **Successful Verifications** | **84.8%** |
| **High Trust Score (0.9)** | **16.8%** |
| **Avg. Interaction Time** | **12.3s** |

---

## 🛠️ Technical Rationale

### **Why FastAPI?**
FastAPI was selected because its native `async/await` support is ideal for handling concurrent I/O-bound tasks (like browser automation) without blocking the API response cycles.

### **Reliable Interaction Modeling**
Instead of legacy Selenium, this project utilizes **Playwright** for its superior support for modern browser features, precise viewport control, and its ability to simulate realistic human-like behavioral markers.

### **Scalability & Resiliency**
The system is built on a decoupled architecture (Broker -> Worker) to ensure that a failure in one automation node does not affect the availability of the API service.

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

## 📬 Submission Checklist

The following deliverables are included in this project for the ABM Egypt technical assessment:

1.  ✅ **GitHub Repository**: [https://github.com/Marina64-64/ABM](https://github.com/Marina64-64/ABM)
2.  ✅ **Task 1 Q&A (PDF)**: `Task1QA_MarinaNashaat.pdf` (Included in submission)
3.  ✅ **Task 4 Architecture**: Detailed design specs in `docs/architecture.md`.
4.  ✅ **Functional Codebase**: Fully automated verification and API framework.

**Submission Package Summary:**
- [x] Comprehensive README.md
- [x] Verified Interaction Scripts (Task 1)
- [x] RESTful API Service (Task 2)
- [x] DOM Scraper (Task 3)
- [x] System Architecture Documentation (Task 4)
