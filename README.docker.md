# Docker Deployment Guide

## Quick Start

### 1. Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### 2. Configuration

Create a `.env` file with your credentials:

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 3. Build and Run

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 4. Access the Application

- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Services

### API Backend (Port 8000)

The FastAPI backend exposes REST APIs for code review and fix operations.

**Endpoints:**
- `GET /` - Health check
- `GET /health` - Health check
- `GET /api/config` - Get current configuration
- `POST /api/review` - Run code review
- `POST /api/fix` - Generate fixes

### Web UI (Port 3000)

Clean, modern web interface built with vanilla HTML/CSS/JS.

**Features:**
- Review pull requests
- Generate automated fixes
- Real-time status updates
- Configuration display

## Docker Commands

### Build Images

```bash
# Build API image
docker build -f Dockerfile.api -t code-review-api .

# Build UI image
docker build -f Dockerfile.ui -t code-review-ui .

# Build both with compose
docker-compose build
```

### Start Services

```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# Start specific service
docker-compose up api
docker-compose up ui
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop specific service
docker-compose stop api
```

### View Logs

```bash
# View all logs
docker-compose logs

# Follow logs
docker-compose logs -f

# View specific service logs
docker-compose logs api
docker-compose logs ui

# Last 100 lines
docker-compose logs --tail=100 api
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
```

## Environment Variables

Required variables in `.env`:

```bash
# Platform
PLATFORM=github  # or gitlab, azure_devops

# Platform Credentials
GITHUB_TOKEN=your_token
GITHUB_REPOSITORY=owner/repo

# LLM Provider
LLM_PROVIDER=anthropic  # or azure_ai
ANTHROPIC_API_KEY=your_key

# Optional Settings
REVIEW_DEPTH=standard
REVIEW_FOCUS=all
LOG_LEVEL=INFO
```

## Production Deployment

### Using Docker Compose

```bash
# Production compose file
docker-compose -f docker-compose.prod.yml up -d
```

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml code-review
```

### Using Kubernetes

```bash
# Create namespace
kubectl create namespace code-review

# Create secret from .env
kubectl create secret generic code-review-secret \
  --from-env-file=.env \
  -n code-review

# Apply manifests
kubectl apply -f k8s/ -n code-review
```

## Health Checks

### API Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### Docker Health Check

```bash
docker-compose ps
```

Should show "healthy" status for API service.

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Check if ports are available
netstat -an | grep 8000
netstat -an | grep 3000
```

### API Can't Connect to Platform

1. Check .env file has correct credentials
2. Verify network connectivity:
   ```bash
   docker-compose exec api ping github.com
   ```

### UI Can't Connect to API

1. Check API is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check browser console for CORS errors

### Permission Errors

```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Rebuild with no cache
docker-compose build --no-cache
```

## Development

### Hot Reload

For development with hot reload:

```bash
# API with auto-reload
docker-compose up api

# Make changes - API will reload automatically
```

### Shell Access

```bash
# Access API container
docker-compose exec api /bin/bash

# Access UI container
docker-compose exec ui /bin/sh
```

### Run Tests

```bash
# Run tests in container
docker-compose exec api pytest tests/

# Run with coverage
docker-compose exec api pytest --cov=. tests/
```

## Cleanup

```bash
# Remove containers and networks
docker-compose down

# Remove containers, networks, and volumes
docker-compose down -v

# Remove all (including images)
docker-compose down --rmi all -v

# Prune system
docker system prune -a
```

## Monitoring

### Resource Usage

```bash
# View resource usage
docker stats

# Specific service
docker stats code-review-api
```

### Logs

```bash
# Export logs
docker-compose logs > logs.txt

# Search logs
docker-compose logs | grep ERROR
```

## Scaling

```bash
# Scale API service
docker-compose up -d --scale api=3

# With load balancer
docker-compose -f docker-compose.lb.yml up -d
```
