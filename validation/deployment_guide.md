# 🚀 Production Deployment Guide

## 📋 Overview

This guide provides comprehensive instructions for deploying the Graph-Sitter + Codegen + Contexten integration system to production environments.

**Target Audience**: DevOps Engineers, System Administrators, Platform Engineers  
**Prerequisites**: Docker, Kubernetes, PostgreSQL, Redis knowledge  
**Estimated Deployment Time**: 4-6 hours  

## 🏗️ Architecture Overview

### System Components
```mermaid
graph TB
    LB[Load Balancer] --> API[API Gateway]
    API --> GS[Graph-Sitter Service]
    API --> CG[Codegen Service]
    API --> CT[Contexten Service]
    
    GS --> DB[(PostgreSQL)]
    CG --> DB
    CT --> DB
    
    GS --> REDIS[(Redis Cache)]
    CG --> REDIS
    CT --> REDIS
    
    GS --> FS[File Storage]
    CG --> FS
    CT --> FS
```

### Infrastructure Requirements

#### Minimum Production Environment
```yaml
# Resource Requirements
Compute:
  CPU: 16 cores (4 cores per service + 4 for system)
  Memory: 64GB (16GB per service + 16GB for system)
  Storage: 1TB SSD (500GB data + 500GB logs/temp)

Database:
  PostgreSQL: 14+ with 32GB RAM, 500GB storage
  Redis: 8GB RAM, 100GB storage

Network:
  Bandwidth: 1Gbps minimum
  Load Balancer: SSL termination, health checks
  CDN: Static asset delivery (optional)
```

#### Recommended Production Environment
```yaml
# Recommended Resources
Compute:
  CPU: 32 cores (8 cores per service + 8 for system)
  Memory: 128GB (32GB per service + 32GB for system)
  Storage: 2TB NVMe SSD

Database:
  PostgreSQL: Cluster with replication, 64GB RAM
  Redis: Cluster with replication, 16GB RAM

Network:
  Bandwidth: 10Gbps
  Multi-AZ deployment
  CDN with global edge locations
```

## 🐳 Container Deployment

### Docker Images

#### Build Production Images
```bash
# Build Graph-Sitter image
docker build -t graph-sitter:latest -f docker/Dockerfile.graph-sitter .

# Build Codegen SDK image
docker build -t codegen-sdk:latest -f docker/Dockerfile.codegen .

# Build Contexten image
docker build -t contexten:latest -f docker/Dockerfile.contexten .
```

#### Docker Compose (Development/Testing)
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: graph_sitter_prod
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  graph-sitter:
    image: graph-sitter:latest
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/graph_sitter_prod
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    depends_on:
      - postgres
      - redis
    ports:
      - "8001:8000"

  codegen-sdk:
    image: codegen-sdk:latest
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/graph_sitter_prod
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    depends_on:
      - postgres
      - redis
    ports:
      - "8002:8000"

  contexten:
    image: contexten:latest
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/graph_sitter_prod
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379
    depends_on:
      - postgres
      - redis
    ports:
      - "8003:8000"

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - graph-sitter
      - codegen-sdk
      - contexten

volumes:
  postgres_data:
  redis_data:
```

## ☸️ Kubernetes Deployment

### Namespace Setup
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: graph-sitter-prod
  labels:
    name: graph-sitter-prod
    environment: production
```

### ConfigMaps and Secrets
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: graph-sitter-config
  namespace: graph-sitter-prod
data:
  LOG_LEVEL: "INFO"
  ENVIRONMENT: "production"
  API_VERSION: "v1"
  
---
apiVersion: v1
kind: Secret
metadata:
  name: graph-sitter-secrets
  namespace: graph-sitter-prod
type: Opaque
data:
  DATABASE_URL: <base64-encoded-database-url>
  REDIS_URL: <base64-encoded-redis-url>
  JWT_SECRET: <base64-encoded-jwt-secret>
  API_KEY: <base64-encoded-api-key>
```

### Database Deployment
```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: graph-sitter-prod
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14
        env:
        - name: POSTGRES_DB
          value: graph_sitter_prod
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 500Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: graph-sitter-prod
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

### Application Deployments
```yaml
# graph-sitter-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graph-sitter
  namespace: graph-sitter-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: graph-sitter
  template:
    metadata:
      labels:
        app: graph-sitter
    spec:
      containers:
      - name: graph-sitter
        image: graph-sitter:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: graph-sitter-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: graph-sitter-secrets
              key: REDIS_URL
        resources:
          requests:
            memory: "8Gi"
            cpu: "2"
          limits:
            memory: "16Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: graph-sitter-service
  namespace: graph-sitter-prod
spec:
  selector:
    app: graph-sitter
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress Configuration
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: graph-sitter-ingress
  namespace: graph-sitter-prod
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.graph-sitter.com
    secretName: graph-sitter-tls
  rules:
  - host: api.graph-sitter.com
    http:
      paths:
      - path: /graph-sitter
        pathType: Prefix
        backend:
          service:
            name: graph-sitter-service
            port:
              number: 80
      - path: /codegen
        pathType: Prefix
        backend:
          service:
            name: codegen-service
            port:
              number: 80
      - path: /contexten
        pathType: Prefix
        backend:
          service:
            name: contexten-service
            port:
              number: 80
```

## 🔧 Configuration Management

### Environment Variables
```bash
# Production Environment Variables
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export DEBUG=false

# Database Configuration
export DATABASE_URL=postgresql://user:pass@host:5432/db
export DATABASE_POOL_SIZE=20
export DATABASE_MAX_OVERFLOW=30

# Redis Configuration
export REDIS_URL=redis://user:pass@host:6379
export REDIS_POOL_SIZE=10

# Security Configuration
export JWT_SECRET=your-jwt-secret
export API_KEY=your-api-key
export ENCRYPTION_KEY=your-encryption-key

# Performance Configuration
export WORKER_PROCESSES=4
export WORKER_CONNECTIONS=1000
export MAX_REQUEST_SIZE=100MB

# Monitoring Configuration
export SENTRY_DSN=your-sentry-dsn
export PROMETHEUS_ENDPOINT=http://prometheus:9090
export GRAFANA_ENDPOINT=http://grafana:3000
```

### Configuration Files
```yaml
# config/production.yaml
database:
  url: ${DATABASE_URL}
  pool_size: 20
  max_overflow: 30
  echo: false

redis:
  url: ${REDIS_URL}
  pool_size: 10
  socket_timeout: 30

security:
  jwt_secret: ${JWT_SECRET}
  api_key: ${API_KEY}
  encryption_key: ${ENCRYPTION_KEY}
  cors_origins:
    - "https://app.graph-sitter.com"
    - "https://dashboard.graph-sitter.com"

performance:
  worker_processes: 4
  worker_connections: 1000
  max_request_size: 104857600  # 100MB
  request_timeout: 300

monitoring:
  sentry_dsn: ${SENTRY_DSN}
  prometheus_endpoint: ${PROMETHEUS_ENDPOINT}
  log_level: INFO
  metrics_enabled: true

features:
  rate_limiting: true
  caching: true
  async_processing: true
  file_upload: true
```

## 🗄️ Database Setup

### PostgreSQL Configuration
```sql
-- Create production database
CREATE DATABASE graph_sitter_prod;
CREATE USER graph_sitter_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE graph_sitter_prod TO graph_sitter_user;

-- Performance tuning
ALTER SYSTEM SET shared_buffers = '16GB';
ALTER SYSTEM SET effective_cache_size = '48GB';
ALTER SYSTEM SET maintenance_work_mem = '2GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Reload configuration
SELECT pg_reload_conf();
```

### Database Migrations
```bash
# Run database migrations
python manage.py migrate --settings=config.production

# Create initial data
python manage.py loaddata initial_data.json

# Create superuser
python manage.py createsuperuser --settings=config.production
```

### Redis Configuration
```conf
# redis.conf
bind 0.0.0.0
port 6379
requirepass your_redis_password

# Memory management
maxmemory 8gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Security
protected-mode yes
tcp-keepalive 300

# Performance
tcp-backlog 511
timeout 0
databases 16
```

## 🔒 Security Configuration

### SSL/TLS Setup
```bash
# Generate SSL certificates (using Let's Encrypt)
certbot certonly --nginx -d api.graph-sitter.com

# Configure nginx SSL
server {
    listen 443 ssl http2;
    server_name api.graph-sitter.com;
    
    ssl_certificate /etc/letsencrypt/live/api.graph-sitter.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.graph-sitter.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
}
```

### Firewall Configuration
```bash
# UFW firewall rules
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow from 10.0.0.0/8 to any port 5432  # PostgreSQL
ufw allow from 10.0.0.0/8 to any port 6379  # Redis
ufw enable
```

### Secrets Management
```bash
# Using Kubernetes secrets
kubectl create secret generic graph-sitter-secrets \
  --from-literal=database-url="postgresql://user:pass@host:5432/db" \
  --from-literal=redis-url="redis://user:pass@host:6379" \
  --from-literal=jwt-secret="your-jwt-secret" \
  --namespace=graph-sitter-prod

# Using HashiCorp Vault (alternative)
vault kv put secret/graph-sitter \
  database_url="postgresql://user:pass@host:5432/db" \
  redis_url="redis://user:pass@host:6379" \
  jwt_secret="your-jwt-secret"
```

## 📊 Monitoring Setup

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'graph-sitter'
    static_configs:
      - targets: ['graph-sitter-service:8000']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'codegen-sdk'
    static_configs:
      - targets: ['codegen-service:8000']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'contexten'
    static_configs:
      - targets: ['contexten-service:8000']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Grafana Dashboards
```json
{
  "dashboard": {
    "title": "Graph-Sitter Production Dashboard",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx errors/sec"
          }
        ]
      }
    ]
  }
}
```

### Alerting Rules
```yaml
# alerting-rules.yml
groups:
  - name: graph-sitter-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: DatabaseConnectionFailure
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"
          description: "PostgreSQL database is not responding"
```

## 🚀 Deployment Process

### Pre-Deployment Checklist
- [ ] All tests passing in CI/CD pipeline
- [ ] Security scan completed with no critical issues
- [ ] Performance benchmarks validated
- [ ] Database migrations tested
- [ ] Configuration files reviewed
- [ ] Secrets properly configured
- [ ] Monitoring and alerting configured
- [ ] Backup procedures tested
- [ ] Rollback plan prepared

### Deployment Steps

#### 1. Infrastructure Preparation
```bash
# Create namespace
kubectl apply -f namespace.yaml

# Apply secrets and configmaps
kubectl apply -f secrets.yaml
kubectl apply -f configmap.yaml

# Deploy database
kubectl apply -f postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
```

#### 2. Database Setup
```bash
# Run migrations
kubectl exec -it postgres-0 -- psql -U postgres -d graph_sitter_prod -f /migrations/schema.sql

# Verify database
kubectl exec -it postgres-0 -- psql -U postgres -d graph_sitter_prod -c "SELECT version();"
```

#### 3. Application Deployment
```bash
# Deploy applications
kubectl apply -f graph-sitter-deployment.yaml
kubectl apply -f codegen-deployment.yaml
kubectl apply -f contexten-deployment.yaml

# Wait for deployments
kubectl wait --for=condition=available deployment/graph-sitter --timeout=300s
kubectl wait --for=condition=available deployment/codegen-sdk --timeout=300s
kubectl wait --for=condition=available deployment/contexten --timeout=300s
```

#### 4. Service and Ingress Setup
```bash
# Deploy services
kubectl apply -f services.yaml

# Deploy ingress
kubectl apply -f ingress.yaml

# Verify ingress
kubectl get ingress -n graph-sitter-prod
```

#### 5. Monitoring Setup
```bash
# Deploy monitoring stack
kubectl apply -f monitoring/prometheus.yaml
kubectl apply -f monitoring/grafana.yaml
kubectl apply -f monitoring/alertmanager.yaml

# Configure dashboards
kubectl apply -f monitoring/dashboards/
```

### Post-Deployment Verification

#### Health Checks
```bash
# Check pod status
kubectl get pods -n graph-sitter-prod

# Check service endpoints
kubectl get endpoints -n graph-sitter-prod

# Test API endpoints
curl -k https://api.graph-sitter.com/health
curl -k https://api.graph-sitter.com/graph-sitter/health
curl -k https://api.graph-sitter.com/codegen/health
curl -k https://api.graph-sitter.com/contexten/health
```

#### Performance Validation
```bash
# Load testing
ab -n 1000 -c 10 https://api.graph-sitter.com/graph-sitter/health

# Monitor metrics
kubectl port-forward svc/prometheus 9090:9090
# Open http://localhost:9090 in browser
```

#### Security Validation
```bash
# SSL certificate check
openssl s_client -connect api.graph-sitter.com:443 -servername api.graph-sitter.com

# Security headers check
curl -I https://api.graph-sitter.com/
```

## 🔄 Maintenance and Updates

### Rolling Updates
```bash
# Update application image
kubectl set image deployment/graph-sitter graph-sitter=graph-sitter:v2.0.0 -n graph-sitter-prod

# Monitor rollout
kubectl rollout status deployment/graph-sitter -n graph-sitter-prod

# Rollback if needed
kubectl rollout undo deployment/graph-sitter -n graph-sitter-prod
```

### Database Maintenance
```bash
# Backup database
kubectl exec postgres-0 -- pg_dump -U postgres graph_sitter_prod > backup.sql

# Vacuum and analyze
kubectl exec postgres-0 -- psql -U postgres -d graph_sitter_prod -c "VACUUM ANALYZE;"

# Check database size
kubectl exec postgres-0 -- psql -U postgres -d graph_sitter_prod -c "SELECT pg_size_pretty(pg_database_size('graph_sitter_prod'));"
```

### Log Management
```bash
# View application logs
kubectl logs -f deployment/graph-sitter -n graph-sitter-prod

# Aggregate logs with fluentd/elasticsearch
kubectl apply -f logging/fluentd.yaml
kubectl apply -f logging/elasticsearch.yaml
kubectl apply -f logging/kibana.yaml
```

## 🆘 Troubleshooting

### Common Issues

#### Pod Startup Issues
```bash
# Check pod events
kubectl describe pod <pod-name> -n graph-sitter-prod

# Check logs
kubectl logs <pod-name> -n graph-sitter-prod --previous

# Check resource usage
kubectl top pods -n graph-sitter-prod
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl exec -it <app-pod> -- nc -zv postgres 5432

# Check database logs
kubectl logs postgres-0 -n graph-sitter-prod

# Verify credentials
kubectl get secret graph-sitter-secrets -o yaml
```

#### Performance Issues
```bash
# Check resource limits
kubectl describe pod <pod-name> -n graph-sitter-prod

# Monitor metrics
kubectl port-forward svc/grafana 3000:3000
# Open http://localhost:3000 in browser

# Check database performance
kubectl exec postgres-0 -- psql -U postgres -d graph_sitter_prod -c "SELECT * FROM pg_stat_activity;"
```

### Emergency Procedures

#### Service Outage
1. Check pod status and restart if necessary
2. Verify database connectivity
3. Check ingress and load balancer status
4. Review recent deployments and rollback if needed
5. Escalate to on-call engineer if issue persists

#### Database Issues
1. Check database pod status
2. Verify storage availability
3. Check database logs for errors
4. Restore from backup if necessary
5. Contact database administrator

#### Security Incident
1. Isolate affected components
2. Review access logs
3. Change all credentials
4. Apply security patches
5. Conduct security audit

---

**Document Version**: 1.0  
**Last Updated**: May 31, 2025  
**Next Review**: June 7, 2025  
**Maintained by**: DevOps Team

