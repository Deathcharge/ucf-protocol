# UCF Protocol: Deployment Guide

**Version**: 1.0.0  
**Last Updated**: April 10, 2026  
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Cloud Platform Deployment](#cloud-platform-deployment)
6. [Security Configuration](#security-configuration)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Performance Tuning](#performance-tuning)
9. [Disaster Recovery](#disaster-recovery)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers production deployment of UCF Protocol across multiple platforms and environments.

### Deployment Options

| Platform | Complexity | Scalability | Cost | Best For |
|----------|-----------|-------------|------|----------|
| **Docker** | Low | Medium | Low | Development, small deployments |
| **Kubernetes** | High | High | Medium | Production, large scale |
| **AWS** | Medium | High | Medium-High | Enterprise, cloud-native |
| **Azure** | Medium | High | Medium-High | Enterprise, Microsoft stack |
| **GCP** | Medium | High | Medium-High | Enterprise, Google stack |

---

## Pre-Deployment Checklist

Before deploying to production, ensure:

- [ ] All tests passing (107+ tests)
- [ ] Code review completed
- [ ] Security audit performed
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Backup strategy defined
- [ ] Monitoring configured
- [ ] Incident response plan ready
- [ ] Team trained on deployment
- [ ] Rollback procedure documented

### Verification Script

```bash
#!/bin/bash
# Deployment verification script

echo "Running pre-deployment checks..."

# Run tests
echo "✓ Running tests..."
pytest tests/ -v --tb=short

# Check code quality
echo "✓ Checking code quality..."
pylint ucf_*.py --disable=all --enable=E,F

# Verify dependencies
echo "✓ Verifying dependencies..."
pip check

# Check configuration
echo "✓ Checking configuration..."
python -c "from ucf_protocol import UCFProtocol; print('✓ UCF Protocol imports successfully')"

echo "✓ All pre-deployment checks passed!"
```

---

## Docker Deployment

### Dockerfile

```dockerfile
# Multi-stage build for optimized image
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Set environment variables
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    UCF_LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "ucf_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  ucf-protocol:
    build: .
    container_name: ucf-protocol
    ports:
      - "8000:8000"
    environment:
      - UCF_LOG_LEVEL=INFO
      - UCF_CACHE_SIZE=1000
      - UCF_CACHE_ENABLED=true
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    networks:
      - ucf-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: ucf-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - ucf-network

  prometheus:
    image: prom/prometheus:latest
    container_name: ucf-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    restart: unless-stopped
    networks:
      - ucf-network

volumes:
  redis-data:
  prometheus-data:

networks:
  ucf-network:
    driver: bridge
```

### Build and Run

```bash
# Build image
docker build -t ucf-protocol:latest .

# Run container
docker run -d \
  --name ucf-protocol \
  -p 8000:8000 \
  -e UCF_LOG_LEVEL=INFO \
  -v $(pwd)/logs:/app/logs \
  ucf-protocol:latest

# Run with docker-compose
docker-compose up -d

# View logs
docker logs -f ucf-protocol

# Stop container
docker stop ucf-protocol
docker rm ucf-protocol
```

---

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ucf-protocol
  namespace: ucf-system
  labels:
    app: ucf-protocol
    version: v1

spec:
  replicas: 3
  
  selector:
    matchLabels:
      app: ucf-protocol
  
  template:
    metadata:
      labels:
        app: ucf-protocol
    
    spec:
      containers:
      - name: ucf-protocol
        image: ucf-protocol:latest
        imagePullPolicy: Always
        
        ports:
        - containerPort: 8000
          name: http
        
        env:
        - name: UCF_LOG_LEVEL
          value: "INFO"
        - name: UCF_CACHE_SIZE
          value: "1000"
        - name: REDIS_URL
          value: "redis://redis:6379"
        
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: data
          mountPath: /app/data
      
      volumes:
      - name: logs
        emptyDir: {}
      - name: data
        persistentVolumeClaim:
          claimName: ucf-data-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: ucf-protocol
  namespace: ucf-system
  labels:
    app: ucf-protocol

spec:
  type: LoadBalancer
  selector:
    app: ucf-protocol
  
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ucf-data-pvc
  namespace: ucf-system

spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace ucf-system

# Apply manifests
kubectl apply -f deployment.yaml

# Check deployment status
kubectl get deployment -n ucf-system
kubectl get pods -n ucf-system
kubectl get svc -n ucf-system

# View logs
kubectl logs -n ucf-system deployment/ucf-protocol -f

# Scale deployment
kubectl scale deployment ucf-protocol -n ucf-system --replicas=5

# Update image
kubectl set image deployment/ucf-protocol \
  ucf-protocol=ucf-protocol:v1.1.0 \
  -n ucf-system
```

---

## Cloud Platform Deployment

### AWS Deployment

#### ECS (Elastic Container Service)

```bash
# Create ECR repository
aws ecr create-repository --repository-name ucf-protocol

# Build and push image
docker build -t ucf-protocol:latest .
docker tag ucf-protocol:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/ucf-protocol:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/ucf-protocol:latest

# Create ECS task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create ECS service
aws ecs create-service \
  --cluster ucf-cluster \
  --service-name ucf-protocol \
  --task-definition ucf-protocol:1 \
  --desired-count 3
```

#### Lambda Deployment

```python
# lambda_handler.py
import json
from ucf_protocol import UCFProtocol

def lambda_handler(event, context):
    """AWS Lambda handler for UCF Protocol."""
    try:
        body = json.loads(event['body'])
        
        # Process request
        phase = UCFProtocol.get_phase(body['harmony'])
        
        message = UCFProtocol.format_state_update(
            harmony=body['harmony'],
            resilience=body['resilience'],
            throughput=body['throughput'],
            focus=body['focus'],
            friction=body['friction'],
            velocity=body['velocity'],
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'phase': phase,
                'message': message,
            }),
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }
```

### Azure Deployment

```bash
# Create resource group
az group create --name ucf-rg --location eastus

# Create container registry
az acr create --resource-group ucf-rg \
  --name ucfprotocol --sku Basic

# Build image
az acr build --registry ucfprotocol \
  --image ucf-protocol:latest .

# Create App Service
az appservice plan create --name ucf-plan \
  --resource-group ucf-rg --sku B1 --is-linux

az webapp create --resource-group ucf-rg \
  --plan ucf-plan --name ucf-protocol \
  --deployment-container-image-name-user ucfprotocol.azurecr.io/ucf-protocol:latest
```

### GCP Deployment

```bash
# Create GCP project
gcloud projects create ucf-protocol

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/ucf-protocol/ucf-protocol:latest

# Deploy to Cloud Run
gcloud run deploy ucf-protocol \
  --image gcr.io/ucf-protocol/ucf-protocol:latest \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --allow-unauthenticated
```

---

## Security Configuration

### Environment Variables

```bash
# .env.production
UCF_LOG_LEVEL=WARNING
UCF_CACHE_SIZE=5000
UCF_CACHE_ENABLED=true
UCF_ENABLE_METRICS=true
UCF_ENABLE_PROFILING=false

# Security
ENABLE_HTTPS=true
SSL_CERT_PATH=/etc/ssl/certs/cert.pem
SSL_KEY_PATH=/etc/ssl/private/key.pem

# Database
DATABASE_URL=postgresql://user:password@host:5432/ucf_db
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=secure_password

# Authentication
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# API Keys
API_KEY_VALIDATION=true
ALLOWED_API_KEYS=key1,key2,key3
```

### Security Best Practices

```python
# security.py
import os
from functools import wraps
from flask import request, jsonify
import jwt

def require_api_key(f):
    """Decorator to require API key."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        allowed_keys = os.getenv('ALLOWED_API_KEYS', '').split(',')
        
        if api_key not in allowed_keys:
            return jsonify({'error': 'Invalid API key'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_jwt(f):
    """Decorator to require JWT token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Token required'}), 401
        
        try:
            jwt.decode(
                token,
                os.getenv('JWT_SECRET'),
                algorithms=[os.getenv('JWT_ALGORITHM', 'HS256')],
            )
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
```

---

## Monitoring and Logging

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ucf-protocol'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Logging Configuration

```python
# logging_config.py
import logging
import logging.handlers
import os

def setup_logging():
    """Configure logging for production."""
    log_level = os.getenv('UCF_LOG_LEVEL', 'INFO')
    log_dir = os.getenv('LOG_DIR', './logs')
    
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('ucf_protocol')
    logger.setLevel(getattr(logging, log_level))
    
    # File handler (rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'ucf_protocol.log'),
        maxBytes=10485760,  # 10MB
        backupCount=10,
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

---

## Performance Tuning

### Caching Strategy

```python
# Implement caching for frequently accessed data
from ucf_advanced_features import CacheManager, EvictionPolicy

cache = CacheManager(
    max_size=5000,
    policy=EvictionPolicy.LRU,
)

def get_metrics_cached(metric_id):
    """Get metrics with caching."""
    cached = cache.get(f"metrics:{metric_id}")
    if cached:
        return cached
    
    metrics = fetch_metrics(metric_id)
    cache.set(f"metrics:{metric_id}", metrics)
    return metrics
```

### Connection Pooling

```python
# Use connection pooling for databases
from sqlalchemy import create_engine

engine = create_engine(
    os.getenv('DATABASE_URL'),
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)
```

---

## Disaster Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh - Daily backup script

BACKUP_DIR="/backups/ucf-protocol"
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

# Backup database
pg_dump $DATABASE_URL > $BACKUP_DIR/db-$(date +%Y%m%d-%H%M%S).sql

# Backup configuration
tar -czf $BACKUP_DIR/config-$(date +%Y%m%d-%H%M%S).tar.gz ./config

# Remove old backups
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

echo "Backup completed successfully"
```

### Recovery Procedure

```bash
#!/bin/bash
# recover.sh - Recovery script

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./recover.sh <backup_file>"
    exit 1
fi

# Stop services
systemctl stop ucf-protocol

# Restore database
psql $DATABASE_URL < $BACKUP_FILE

# Restore configuration
tar -xzf config-backup.tar.gz

# Start services
systemctl start ucf-protocol

echo "Recovery completed successfully"
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| High memory usage | Cache too large | Reduce cache size or implement eviction |
| Slow response times | Database queries | Add indexes, optimize queries |
| Connection errors | Network issues | Check connectivity, firewall rules |
| Pod crashes | Resource limits | Increase CPU/memory limits |
| Data loss | No backup | Implement backup strategy |

### Debug Mode

```bash
# Enable debug logging
export UCF_LOG_LEVEL=DEBUG

# Run with profiling
python -m cProfile -o profile.stats ucf_protocol.py

# Analyze profile
python -m pstats profile.stats
```

---

## References

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Azure Container Instances](https://docs.microsoft.com/en-us/azure/container-instances/)
- [Google Cloud Run](https://cloud.google.com/run/docs)

---

**Document Version**: 1.0.0  
**Last Updated**: April 10, 2026  
**Author**: Manus AI  
**Status**: Production Ready
