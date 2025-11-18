#!/bin/bash

echo "🐳 Testing Docker Setup..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

echo "✅ Docker is installed"

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed"
    exit 1
fi

echo "✅ docker-compose is installed"

# Check .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found, copying from .env.example"
    cp .env.example .env
fi

echo "✅ .env file exists"

# Test building images
echo ""
echo "📦 Building images..."

# Build API image
docker build -f Dockerfile.api -t code-review-api:test . > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ API image built successfully"
else
    echo "❌ API image build failed"
    exit 1
fi

# Build UI image
docker build -f Dockerfile.ui -t code-review-ui:test . > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ UI image built successfully"
else
    echo "❌ UI image build failed"
    exit 1
fi

echo ""
echo "🎉 All Docker tests passed!"
echo ""
echo "To start the application:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop:"
echo "  docker-compose down"
