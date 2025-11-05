# Production Deployment Guide

**Last Updated:** 5 November 2025  
**Purpose:** Complete guide for deploying SonicLayer AI to production

---

## 🎯 Deployment Options Overview

| Option | Complexity | Cost | Scalability | Best For |
|--------|-----------|------|-------------|----------|
| **Docker Compose** | ⭐ Low | $ | Low-Medium | Small teams, demos |
| **Systemd Services** | ⭐⭐ Medium | $ | Medium | Linux servers, no Docker |
| **Kubernetes** | ⭐⭐⭐⭐ High | $$ | High | Enterprise, auto-scaling |
| **Cloud Platform** | ⭐⭐⭐ Medium | $$$ | Very High | Managed services |
| **Hybrid** | ⭐⭐⭐ Medium | $$ | High | Mix of approaches |

---

## 📋 Pre-Deployment Checklist

### Environment Requirements

- [ ] Python 3.10 or higher
- [ ] 4GB+ RAM (8GB recommended for Whisper + models)
- [ ] 10GB+ disk space (models + audio storage)
- [ ] Redis server (local or cloud)
- [ ] LM Studio or external LLM API
- [ ] Nginx or reverse proxy (for production)

### Security Checklist

- [ ] Remove debug mode (`uvicorn --reload` → `uvicorn`)
- [ ] Set strong Redis password
- [ ] Configure CORS for specific domains (not `*`)
- [ ] Use HTTPS/TLS certificates
- [ ] Set API rate limiting
- [ ] Secure file upload size limits
- [ ] Environment variable secrets (not hardcoded)
- [ ] Firewall rules configured
- [ ] Regular security updates enabled

### Performance Checklist

- [ ] Model caching configured
- [ ] Redis persistence enabled (RDB + AOF)
- [ ] Log rotation configured
- [ ] Monitoring/alerts set up
- [ ] Backup strategy defined
- [ ] Load testing completed

---

## 🐳 Option 1: Docker Compose (Recommended for Most)

**Best For:** Quick deployment, consistent environments, small-medium scale

### Current Setup (Development)

```yaml
# docker-compose.yml (current)
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
  
  langflow:
    image: langflow/langflow:latest
    ports:
      - "7860:7860"
    environment:
      - LANGFLOW_DATABASE_URL=sqlite:///./langflow.db
    volumes:
      - langflow_data:/app/langflow

volumes:
  redis_data:
  langflow_data:
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Redis with authentication
  redis:
    image: redis:7-alpine
    restart: always
    ports:
      - "127.0.0.1:6379:6379"  # Localhost only
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  # Langflow
  langflow:
    image: langflow/langflow:latest
    restart: always
    ports:
      - "127.0.0.1:7860:7860"
    environment:
      - LANGFLOW_DATABASE_URL=sqlite:///./langflow.db
      - LANGFLOW_LOG_LEVEL=INFO
    volumes:
      - langflow_data:/app/langflow
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860/health"]
      interval: 60s
      timeout: 10s
      retries: 3
  
  # FastAPI Backend
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - LANGFLOW_BASE_URL=http://langflow:7860
      - LANGFLOW_API_KEY=${LANGFLOW_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      redis:
        condition: service_healthy
      langflow:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/segments/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  # RQ Worker
  worker:
    build:
      context: .
      dockerfile: Dockerfile
    restart: always
    command: rq worker transcript_tasks --url redis://redis:6379/0
    environment:
      - REDIS_URL=redis://redis:6379/0
      - LANGFLOW_BASE_URL=http://langflow:7860
      - LANGFLOW_API_KEY=${LANGFLOW_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    depends_on:
      - redis
      - langflow
  
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./uploads:/usr/share/nginx/html/uploads:ro
    depends_on:
      - backend

volumes:
  redis_data:
  langflow_data:
```

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download models at build time (optional, saves startup time)
RUN python -c "import whisper; whisper.load_model('base')"
RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='facebook/bart-large-mnli')"

# Copy application code
COPY app /app/app
COPY dashboard /app/dashboard
COPY scripts /app/scripts

# Create directories
RUN mkdir -p /app/uploads /app/logs

# Expose port
EXPOSE 8000

# Run backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### Redis Configuration

```conf
# redis.conf
requirepass your_strong_password_here
maxmemory 2gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
dir /data
```

### Nginx Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    server {
        listen 80;
        server_name your-domain.com;
        
        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name your-domain.com;
        
        # SSL certificates
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        
        # File upload size limit
        client_max_body_size 50M;
        
        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 180s;  # For long Whisper transcriptions
        }
        
        # Audio file serving
        location /audio/ {
            alias /usr/share/nginx/html/uploads/;
            add_header Cache-Control "public, max-age=3600";
        }
        
        # Dashboard (if serving via Nginx)
        location / {
            root /usr/share/nginx/html/dashboard;
            try_files $uri $uri/ /index.html;
        }
    }
}
```

### Environment Variables

```bash
# .env.production
REDIS_URL=redis://:your_password@redis:6379/0
LANGFLOW_BASE_URL=http://langflow:7860
LANGFLOW_API_KEY=sk-your-api-key-here
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Deployment Commands

```bash
# 1. Prepare environment
cp .env.production .env
mkdir -p uploads logs ssl

# 2. Generate SSL certificates (or use Let's Encrypt)
# For Let's Encrypt:
certbot certonly --standalone -d your-domain.com

# 3. Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 4. Check health
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs backend
curl https://your-domain.com/api/segments/health

# 5. Monitor logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

### Scaling Workers

```bash
# Scale up to 3 workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=3

# Check worker status
docker-compose -f docker-compose.prod.yml exec worker rq info --url redis://redis:6379/0
```

---

## 🔧 Option 2: Systemd Services (No Docker)

**Best For:** Traditional Linux deployments, existing infrastructure, avoiding Docker overhead

### Directory Structure

```
/opt/soniclayer/
├── app/
├── dashboard/
├── uploads/
├── logs/
├── venv/
├── requirements.txt
└── config/
    ├── backend.env
    └── worker.env
```

### System Setup

```bash
# 1. Create dedicated user
sudo useradd -r -s /bin/false soniclayer

# 2. Install Python and dependencies
sudo apt-get install python3.11 python3.11-venv ffmpeg redis-server

# 3. Create application directory
sudo mkdir -p /opt/soniclayer
sudo chown soniclayer:soniclayer /opt/soniclayer

# 4. Clone repository (as soniclayer user)
sudo -u soniclayer git clone <repo-url> /opt/soniclayer

# 5. Set up virtual environment
cd /opt/soniclayer
sudo -u soniclayer python3.11 -m venv venv
sudo -u soniclayer venv/bin/pip install -r requirements.txt

# 6. Create required directories
sudo -u soniclayer mkdir -p uploads logs
```

### Redis Configuration

```bash
# /etc/redis/redis.conf
bind 127.0.0.1
requirepass your_strong_password_here
maxmemory 2gb
maxmemory-policy allkeys-lru
appendonly yes

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### Backend Service

```ini
# /etc/systemd/system/soniclayer-backend.service
[Unit]
Description=SonicLayer AI Backend
After=network.target redis-server.service
Requires=redis-server.service

[Service]
Type=notify
User=soniclayer
Group=soniclayer
WorkingDirectory=/opt/soniclayer
Environment="PATH=/opt/soniclayer/venv/bin"
EnvironmentFile=/opt/soniclayer/config/backend.env

ExecStart=/opt/soniclayer/venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --log-config /opt/soniclayer/config/logging.yaml

Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/soniclayer/uploads /opt/soniclayer/logs

[Install]
WantedBy=multi-user.target
```

### Worker Service

```ini
# /etc/systemd/system/soniclayer-worker@.service
[Unit]
Description=SonicLayer AI Worker %i
After=network.target redis-server.service soniclayer-backend.service
Requires=redis-server.service

[Service]
Type=simple
User=soniclayer
Group=soniclayer
WorkingDirectory=/opt/soniclayer
Environment="PATH=/opt/soniclayer/venv/bin"
EnvironmentFile=/opt/soniclayer/config/worker.env

ExecStart=/opt/soniclayer/venv/bin/rq worker transcript_tasks \
    --url redis://:${REDIS_PASSWORD}@localhost:6379/0 \
    --name worker-%i

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Langflow Service

```bash
# Install Langflow globally
sudo pip3 install langflow

# Create service
cat > /etc/systemd/system/langflow.service << 'EOF'
[Unit]
Description=Langflow LLM Chain Service
After=network.target

[Service]
Type=simple
User=soniclayer
WorkingDirectory=/opt/soniclayer
Environment="PATH=/usr/local/bin"

ExecStart=/usr/local/bin/langflow run \
    --host 0.0.0.0 \
    --port 7860 \
    --backend-only

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### Environment Files

```bash
# /opt/soniclayer/config/backend.env
REDIS_URL=redis://:your_password@localhost:6379/0
LANGFLOW_BASE_URL=http://localhost:7860
LANGFLOW_API_KEY=sk-your-api-key-here
LOG_LEVEL=INFO
ENVIRONMENT=production

# /opt/soniclayer/config/worker.env
REDIS_PASSWORD=your_password
LANGFLOW_BASE_URL=http://localhost:7860
LANGFLOW_API_KEY=sk-your-api-key-here
LOG_LEVEL=INFO
```

### Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable redis-server
sudo systemctl enable langflow
sudo systemctl enable soniclayer-backend
sudo systemctl enable soniclayer-worker@1
sudo systemctl enable soniclayer-worker@2

# Start services
sudo systemctl start redis-server
sudo systemctl start langflow
sudo systemctl start soniclayer-backend
sudo systemctl start soniclayer-worker@1
sudo systemctl start soniclayer-worker@2

# Check status
sudo systemctl status soniclayer-backend
sudo systemctl status soniclayer-worker@1
sudo systemctl status langflow

# View logs
sudo journalctl -u soniclayer-backend -f
sudo journalctl -u soniclayer-worker@1 -f
```

### Nginx Setup (Same as Docker)

```bash
# Install Nginx
sudo apt-get install nginx

# Copy nginx.conf (see Docker section above)
sudo cp nginx.conf /etc/nginx/nginx.conf

# Enable and start
sudo systemctl enable nginx
sudo systemctl restart nginx
```

---

## ☁️ Option 3: Cloud Platform Deployment

### AWS Deployment

#### Using EC2 + ECS

```bash
# 1. Create EC2 instance (t3.large recommended)
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.large \
    --key-name your-key \
    --security-groups soniclayer-sg

# 2. Install Docker on EC2
ssh -i your-key.pem ec2-user@<public-ip>
sudo yum install docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# 3. Use Docker Compose method (see Option 1)
```

#### Using Elastic Beanstalk

```bash
# 1. Create Dockerrun.aws.json
cat > Dockerrun.aws.json << 'EOF'
{
  "AWSEBDockerrunVersion": "3",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-registry/soniclayer-backend:latest",
      "memory": 2048,
      "essential": true,
      "portMappings": [{"containerPort": 8000, "hostPort": 80}]
    },
    {
      "name": "worker",
      "image": "your-registry/soniclayer-backend:latest",
      "memory": 2048,
      "command": ["rq", "worker", "transcript_tasks"]
    }
  ]
}
EOF

# 2. Deploy
eb init soniclayer --platform docker
eb create soniclayer-prod
eb deploy
```

#### Using RDS for Redis

```bash
# Use AWS ElastiCache instead of local Redis
REDIS_URL=redis://soniclayer.abcdef.ng.0001.use1.cache.amazonaws.com:6379/0
```

### Google Cloud Platform

```bash
# 1. Build and push to Container Registry
gcloud builds submit --tag gcr.io/project-id/soniclayer-backend

# 2. Deploy to Cloud Run
gcloud run deploy soniclayer-backend \
    --image gcr.io/project-id/soniclayer-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 4Gi \
    --timeout 180s
```

### Azure

```bash
# Deploy to Azure Container Instances
az container create \
    --resource-group soniclayer-rg \
    --name soniclayer-backend \
    --image your-registry/soniclayer-backend:latest \
    --cpu 2 \
    --memory 4 \
    --port 8000 \
    --environment-variables \
        REDIS_URL="redis://..." \
        LANGFLOW_BASE_URL="http://..."
```

---

## 🔄 Option 4: Kubernetes (Enterprise Scale)

### Kubernetes Manifests

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: soniclayer

---
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: soniclayer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc

---
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: soniclayer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/soniclayer-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: soniclayer-secrets
              key: redis-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /segments/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10

---
# k8s/worker.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker
  namespace: soniclayer
spec:
  replicas: 5
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
      - name: worker
        image: your-registry/soniclayer-backend:latest
        command: ["rq", "worker", "transcript_tasks"]
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: soniclayer-secrets
              key: redis-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: soniclayer
spec:
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: soniclayer-ingress
  namespace: soniclayer
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - soniclayer.example.com
    secretName: soniclayer-tls
  rules:
  - host: soniclayer.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -n soniclayer
kubectl get services -n soniclayer

# Scale workers
kubectl scale deployment worker --replicas=10 -n soniclayer

# View logs
kubectl logs -f deployment/backend -n soniclayer
```

---

## 📊 Monitoring & Logging

### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=your_password
```

### Application Metrics

```python
# Add to app/main.py
from prometheus_client import Counter, Histogram, generate_latest

upload_counter = Counter('soniclayer_uploads_total', 'Total audio uploads')
transcription_duration = Histogram('soniclayer_transcription_seconds', 'Transcription duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Centralized Logging

```yaml
# Use ELK Stack or Loki
services:
  loki:
    image: grafana/loki
    ports:
      - "3100:3100"
  
  promtail:
    image: grafana/promtail
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml
```

---

## 🔐 Security Best Practices

1. **API Authentication**
   ```python
   # Add API key middleware
   from fastapi import Security, HTTPException
   from fastapi.security import APIKeyHeader
   
   api_key_header = APIKeyHeader(name="X-API-Key")
   
   async def verify_api_key(api_key: str = Security(api_key_header)):
       if api_key != os.getenv("API_KEY"):
           raise HTTPException(status_code=403, detail="Invalid API Key")
   
   @router.post("/evaluate/", dependencies=[Depends(verify_api_key)])
   async def evaluate_audio(...):
       ...
   ```

2. **Rate Limiting**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/evaluate/")
   @limiter.limit("10/minute")
   async def evaluate_audio(...):
       ...
   ```

3. **File Upload Validation**
   ```python
   import magic
   
   def validate_audio_file(file_bytes: bytes):
       mime = magic.from_buffer(file_bytes, mime=True)
       if mime not in ['audio/wav', 'audio/x-wav', 'audio/wave']:
           raise HTTPException(400, "Only WAV files allowed")
   ```

---

## 📈 Performance Tuning

### Model Optimization

```python
# Use smaller Whisper model for faster transcription
model = whisper.load_model("tiny")  # vs "base"

# Cache model in memory
@lru_cache(maxsize=1)
def get_whisper_model():
    return whisper.load_model("base")
```

### Redis Optimization

```conf
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
tcp-backlog 511
timeout 0
tcp-keepalive 300
```

### Worker Scaling

```bash
# Monitor queue depth
rq info --url redis://localhost:6379/0

# Auto-scale based on queue length
if queue_length > 100:
    scale_workers(+2)
```

---

## 🔄 Backup & Recovery

### Redis Backup

```bash
# Automated backups
0 2 * * * redis-cli --rdb /backups/redis-$(date +\%Y\%m\%d).rdb

# Restore from backup
redis-cli SHUTDOWN SAVE
cp /backups/redis-20251105.rdb /var/lib/redis/dump.rdb
systemctl start redis
```

### Audio Files Backup

```bash
# Sync to S3
aws s3 sync /opt/soniclayer/uploads s3://soniclayer-backups/uploads/

# Or use rsync
rsync -avz /opt/soniclayer/uploads/ backup-server:/backups/uploads/
```

---

## 🎯 Recommended Stack by Use Case

### Small Team / Demo (< 100 users)
- **Docker Compose** on single server (Option 1)
- 4GB RAM, 2 vCPUs
- Cost: ~$20-40/month (DigitalOcean, Linode)

### Medium Business (100-1000 users)
- **Systemd Services** on dedicated server (Option 2)
- 8GB RAM, 4 vCPUs
- External Redis (managed)
- Cost: ~$100-200/month

### Enterprise (1000+ users)
- **Kubernetes** cluster (Option 4)
- Auto-scaling workers
- Managed services (RDS, ElastiCache)
- CDN for audio files
- Cost: ~$500-2000/month

---

## 📚 Related Documentation

- [README.md](README.md) - Development setup
- [ARCHITECTURE_PERSONAS_WORKERS.md](ARCHITECTURE_PERSONAS_WORKERS.md) - System architecture
- [TODO.md](TODO.md) - Future improvements
