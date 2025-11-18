# Code Review Agents

AI-powered code review automation for Azure DevOps, GitLab, and GitHub using LLM capabilities (Azure OpenAI or Anthropic Claude).

## 🚀 Quick Start with Docker

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd Code-Review-Agent
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Start the application**
```bash
docker-compose up -d
```

4. **Access the application**
- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📦 Services

### API Backend (Port 8000)
FastAPI-based REST API for code review operations.

**Key Endpoints:**
- `POST /api/review` - Run code review on a PR
- `POST /api/fix` - Generate automated fixes
- `GET /api/config` - View current configuration
- `GET /health` - Health check

### Web UI (Port 3000)
Clean, modern web interface for easy interaction.

**Features:**
- Submit PRs for review
- Generate automated fixes
- View configuration
- Real-time status updates

## 🛠️ Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run API
uvicorn api.main:app --reload --port 8000

# Run tests
pytest tests/
```

### Docker Commands

```bash
# View logs
docker-compose logs -f

# Rebuild
docker-compose up --build

# Stop services
docker-compose down

# Clean up
docker-compose down -v --rmi all
```

## 📖 Documentation

- [Docker Guide](README.docker.md) - Detailed Docker deployment guide
- [Setup Guide](docs/SETUP.md) - Platform configuration
- [API Documentation](docs/API.md) - API reference
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues

## 🏗️ Architecture

```
┌─────────────────┐      ┌─────────────────┐
│   Web UI        │─────▶│   API Backend   │
│   (Port 3000)   │      │   (Port 8000)   │
│   Nginx/Static  │      │   FastAPI       │
└─────────────────┘      └────────┬────────┘
                                  │
                         ┌────────┴────────┐
                         │                 │
                    ┌────▼────┐      ┌────▼────┐
                    │ Review  │      │  Fix    │
                    │ Agent   │      │  Agent  │
                    └────┬────┘      └────┬────┘
                         │                │
                    ┌────▼────────────────▼────┐
                    │  Platform Integrations   │
                    │  GitHub/GitLab/Azure     │
                    └──────────────────────────┘
```

## 🔧 Configuration

### Required Environment Variables

```bash
# Platform Selection
PLATFORM=github  # github, gitlab, or azure_devops

# GitHub Example
GITHUB_TOKEN=ghp_xxxxx
GITHUB_REPOSITORY=owner/repo

# LLM Provider
LLM_PROVIDER=anthropic  # anthropic or azure_ai
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Optional Settings
REVIEW_DEPTH=standard  # quick, standard, deep
REVIEW_FOCUS=all      # all, security, performance, style, bugs
FIX_AUTO_CREATE_PR=true
```

See `.env.example` for all options.

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=. --cov-report=html tests/

# Test specific module
pytest tests/test_config.py -v
```

## 📊 Features

- ✅ **Multi-Platform**: GitHub, GitLab, Azure DevOps
- ✅ **Multi-LLM**: Anthropic Claude, Azure OpenAI
- ✅ **Smart Review**: Configurable depth and focus areas
- ✅ **Auto-Fix**: Generate and apply fixes automatically
- ✅ **Web UI**: Clean, modern interface
- ✅ **REST API**: Programmatic access
- ✅ **Docker**: Production-ready containers
- ✅ **Tested**: Comprehensive test suite

## 🤝 Contributing

Contributions welcome! Please ensure:
- Tests pass: `pytest tests/`
- Code is formatted
- Documentation is updated

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues:
- Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- View [API Documentation](docs/API.md)
- Open an issue on GitHub
