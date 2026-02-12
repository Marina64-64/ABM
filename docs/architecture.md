# System Architecture Documentation

## Overview

This document describes the scalable system architecture for the reCAPTCHA solving service, designed to handle high-volume concurrent requests with reliability, monitoring, and failover capabilities.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Load Balancer                           │
│                      (nginx / HAProxy)                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────┐             ┌─────────────────┐
│   FastAPI       │             │   FastAPI       │
│   Server 1      │             │   Server N      │
│   (Port 8000)   │             │   (Port 800N)   │
└────────┬────────┘             └────────┬────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │      RabbitMQ Cluster         │
         │   (Message Queue / Broker)    │
         │                               │
         │  ┌─────────┐   ┌─────────┐    │
         │  │ Queue 1 │   │ Queue N │    │
         │  └─────────┘   └─────────┘    │
         └───────────────┬───────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────┐             ┌─────────────────┐
│  Celery Worker  │             │  Celery Worker  │
│     Pool 1      │    ...      │     Pool N      │
│  (4 concurrent) │             │  (4 concurrent) │
└────────┬────────┘             └────────┬────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │    PostgreSQL Database        │
         │    (Primary + Replica)        │
         │                               │
         │  ┌──────────────────────┐     │
         │  │  Tasks Table         │     │
         │  │  Results Cache       │     │
         │  └──────────────────────┘     │
         └───────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────┐             ┌─────────────────┐
│  Redis Cache    │             │  Monitoring     │
│  (Session/      │             │  & Logging      │
│   Results)      │             │  (Prometheus/   │
│                 │             │   Grafana/ELK)  │
└─────────────────┘             └─────────────────┘
```

## Components

### 1. Load Balancer (nginx/HAProxy)

**Purpose**: Distribute incoming HTTP requests across multiple API servers.

**Features**:
- Round-robin or least-connections distribution
- Health checks on backend servers
- SSL/TLS termination
- Rate limiting
- Request buffering

**Configuration Example** (nginx):
```nginx
upstream api_servers {
    least_conn;
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.recaptcha-solver.com;
    
    location / {
        proxy_pass http://api_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. FastAPI Servers (Horizontally Scalable)

**Purpose**: Handle HTTP API requests and manage task lifecycle.

**Responsibilities**:
- Accept reCAPTCHA solving requests
- Generate unique task IDs
- Publish tasks to RabbitMQ queue
- Query task status from database
- Return results to clients

**Scaling**:
- Run multiple instances behind load balancer
- Stateless design allows easy horizontal scaling
- Each instance runs with multiple workers (uvicorn --workers 4)

**Deployment**:
```bash
# Server 1
uvicorn src.task2_api.app:app --host 0.0.0.0 --port 8000 --workers 4

# Server 2
uvicorn src.task2_api.app:app --host 0.0.0.0 --port 8001 --workers 4

# Server N
uvicorn src.task2_api.app:app --host 0.0.0.0 --port 800N --workers 4
```

### 3. RabbitMQ Message Queue

**Purpose**: Decouple API servers from worker processes, enabling async task processing.

**Features**:
- Persistent message storage
- Message acknowledgment
- Dead letter queues for failed tasks
- Priority queues for urgent tasks
- Clustering for high availability

**Queue Configuration**:
```python
# Queue settings
queue_name = "recaptcha_tasks"
durable = True  # Survive broker restart
auto_delete = False
exclusive = False

# Message properties
delivery_mode = 2  # Persistent messages
priority = 0-10  # Task priority
```

**Clustering**:
- Run RabbitMQ in cluster mode (3+ nodes)
- Mirrored queues for redundancy
- Automatic failover

### 4. Celery Worker Pool (Horizontally Scalable)

**Purpose**: Execute reCAPTCHA solving tasks asynchronously.

**Responsibilities**:
- Consume tasks from RabbitMQ queue
- Launch browser automation (Playwright)
- Solve reCAPTCHA challenges
- Update database with results
- Handle retries and failures

**Scaling**:
- Deploy multiple worker instances across servers
- Each worker runs multiple concurrent tasks
- Auto-scaling based on queue depth

**Deployment**:
```bash
# Worker Pool 1 (Server 1)
celery -A src.task2_api.worker worker \
    --concurrency=4 \
    --loglevel=info \
    --hostname=worker1@%h

# Worker Pool 2 (Server 2)
celery -A src.task2_api.worker worker \
    --concurrency=4 \
    --loglevel=info \
    --hostname=worker2@%h

# Auto-scaling worker
celery -A src.task2_api.worker worker \
    --autoscale=10,2 \
    --loglevel=info
```

**Resource Management**:
- Each worker limited to 4 concurrent browser instances
- Memory limits per worker (2GB recommended)
- CPU affinity for optimal performance

### 5. PostgreSQL Database (Primary + Replica)

**Purpose**: Persistent storage for tasks, results, and metadata.

**Schema**:
```sql
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY,
    sitekey VARCHAR(255) NOT NULL,
    pageurl TEXT NOT NULL,
    proxy TEXT,
    status VARCHAR(20) NOT NULL,
    token TEXT,
    solve_time REAL,
    error TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

**Replication**:
- Primary-replica setup (1 primary, 2+ replicas)
- Asynchronous replication for read scaling
- Automatic failover with pg_auto_failover or Patroni

**Connection Pooling**:
- PgBouncer for connection pooling
- Max 100 connections per API server
- Transaction pooling mode

### 6. Redis Cache

**Purpose**: High-speed caching for frequently accessed data.

**Use Cases**:
- Task result caching (TTL: 1 hour)
- Session management
- Rate limiting counters
- Worker status tracking

**Configuration**:
```python
# Cache task results
redis.setex(f"task:{task_id}", 3600, json.dumps(result))

# Rate limiting
redis.incr(f"rate_limit:{client_ip}")
redis.expire(f"rate_limit:{client_ip}", 60)
```

### 7. Monitoring & Logging

**Components**:

#### Prometheus (Metrics Collection)
- API request rates and latencies
- Worker task throughput
- Queue depth and processing time
- Database query performance
- System resource usage (CPU, memory, disk)

**Metrics Example**:
```python
from prometheus_client import Counter, Histogram

task_counter = Counter('recaptcha_tasks_total', 'Total tasks processed')
solve_time_histogram = Histogram('recaptcha_solve_time_seconds', 'Time to solve')
```

#### Grafana (Visualization)
- Real-time dashboards
- Task success/failure rates
- System health overview
- Alert visualization

#### ELK Stack (Centralized Logging)
- **Elasticsearch**: Log storage and indexing
- **Logstash**: Log aggregation and processing
- **Kibana**: Log visualization and search

**Log Aggregation**:
- All API servers send logs to Logstash
- All workers send logs to Logstash
- Structured JSON logging format
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

#### Flower (Celery Monitoring)
- Real-time worker monitoring
- Task history and statistics
- Worker pool management
- Web UI on port 5555

```bash
celery -A src.task2_api.worker flower --port=5555
```

## Failover & Recovery Mechanisms

### 1. API Server Failover

**Mechanism**:
- Load balancer health checks every 5 seconds
- Failed server removed from pool automatically
- Requests redistributed to healthy servers

**Recovery**:
- Automatic retry on server restart
- Graceful shutdown with connection draining
- Zero-downtime deployments with rolling updates

### 2. RabbitMQ Failover

**Mechanism**:
- Clustered RabbitMQ nodes (3+ nodes)
- Mirrored queues across nodes
- Automatic leader election on failure

**Recovery**:
- Messages persisted to disk
- Unacknowledged messages requeued
- Clients automatically reconnect

### 3. Worker Failover

**Mechanism**:
- Task acknowledgment after completion
- Failed tasks automatically requeued
- Max retry attempts: 3
- Exponential backoff between retries

**Recovery**:
```python
@celery.task(bind=True, max_retries=3)
def solve_task(self, task_id):
    try:
        # Solve reCAPTCHA
        pass
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### 4. Database Failover

**Mechanism**:
- Primary-replica setup with automatic failover
- Health checks on primary database
- Replica promoted to primary on failure

**Tools**:
- **Patroni**: Automatic PostgreSQL failover
- **pg_auto_failover**: Simple failover solution
- **PgBouncer**: Connection pooling and failover routing

**Recovery**:
- Automatic reconnection on failover
- Read queries routed to replicas
- Write queries to primary only

### 5. Redis Failover

**Mechanism**:
- Redis Sentinel for automatic failover
- Master-slave replication
- Sentinel monitors master health

**Recovery**:
- Automatic master promotion
- Client libraries handle reconnection
- Cache rebuild on failure (acceptable for non-critical data)

## Scaling Strategy

### Horizontal Scaling

#### API Servers
- Add more FastAPI instances behind load balancer
- Each instance handles 1000+ req/sec
- Scale based on CPU/memory usage

#### Workers
- Add more Celery worker instances
- Each worker handles 4 concurrent tasks
- Scale based on queue depth

**Auto-Scaling Rules**:
```yaml
# Kubernetes HPA example
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-server-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Vertical Scaling

- Increase worker concurrency (4 → 8 → 16)
- Larger database instances
- More RabbitMQ memory

### Geographic Distribution

- Deploy in multiple regions
- Regional load balancers
- Data replication across regions
- Latency-based routing

## Performance Optimization

### 1. Caching Strategy
- Cache task results in Redis (1 hour TTL)
- Database query result caching
- CDN for static assets

### 2. Connection Pooling
- Database connection pooling (PgBouncer)
- HTTP connection pooling (httpx)
- Browser instance reuse

### 3. Async Processing
- All I/O operations async (asyncio)
- Non-blocking database queries
- Concurrent task processing

### 4. Resource Limits
- Worker memory limits (2GB per worker)
- Browser timeout (60 seconds)
- Queue size limits (10,000 tasks)
- Rate limiting (60 req/min per IP)

## Security Considerations

### 1. API Security
- API key authentication
- Rate limiting per client
- Input validation and sanitization
- HTTPS/TLS encryption

### 2. Network Security
- Private network for internal services
- Firewall rules (allow only necessary ports)
- VPN for admin access
- DDoS protection

### 3. Data Security
- Encrypted database connections
- Sensitive data encryption at rest
- Proxy credentials encrypted
- Regular security audits

## Deployment Architecture

### Docker Compose (Development)

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - rabbitmq
      - postgres
      - redis
  
  worker:
    build: .
    command: celery -A src.task2_api.worker worker --concurrency=4
    depends_on:
      - rabbitmq
      - postgres
  
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: recaptcha
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  flower:
    build: .
    command: celery -A src.task2_api.worker flower
    ports:
      - "5555:5555"
```

### Kubernetes (Production)

- Separate deployments for API, workers, databases
- StatefulSets for databases
- ConfigMaps for configuration
- Secrets for sensitive data
- Ingress for load balancing
- Persistent volumes for data

## Monitoring Dashboards

### Key Metrics to Monitor

1. **API Metrics**
   - Request rate (req/sec)
   - Response time (p50, p95, p99)
   - Error rate (%)
   - Active connections

2. **Worker Metrics**
   - Tasks processed/sec
   - Average solve time
   - Success rate (%)
   - Active workers

3. **Queue Metrics**
   - Queue depth
   - Message rate
   - Consumer count
   - Unacknowledged messages

4. **Database Metrics**
   - Query latency
   - Connection count
   - Replication lag
   - Disk usage

5. **System Metrics**
   - CPU usage (%)
   - Memory usage (%)
   - Disk I/O
   - Network throughput

## Disaster Recovery

### Backup Strategy
- Database backups every 6 hours
- Transaction log backups every 15 minutes
- Backup retention: 30 days
- Offsite backup storage (S3/GCS)

### Recovery Procedures
1. **Database Recovery**: Restore from latest backup
2. **Queue Recovery**: Messages persisted to disk
3. **Configuration Recovery**: Infrastructure as Code (Terraform)
4. **Monitoring Recovery**: Grafana dashboard exports

### RTO/RPO Targets
- **RTO** (Recovery Time Objective): < 15 minutes
- **RPO** (Recovery Point Objective): < 15 minutes

## Conclusion

This architecture provides:
- ✅ **Scalability**: Horizontal scaling of all components
- ✅ **Reliability**: Redundancy and automatic failover
- ✅ **Performance**: Async processing and caching
- ✅ **Monitoring**: Comprehensive metrics and logging
- ✅ **Security**: Multiple layers of protection
- ✅ **Maintainability**: Clear separation of concerns

The system can handle **1000+ concurrent tasks** with proper scaling and can be deployed in various environments from development (Docker Compose) to production (Kubernetes).
