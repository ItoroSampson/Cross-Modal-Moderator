#!/bin/bash
echo "🔍 Microservices Diagnostic Report"
echo "=================================="

echo ""
echo "1. Docker Container Status:"
docker-compose ps

echo ""
echo "2. Recent Logs (last 10 lines each):"
echo "--- Orchestrator ---"
docker-compose logs --tail=10 orchestrator
echo "--- Fusion Service ---"
docker-compose logs --tail=10 fusion-service

echo ""
echo "3. Port Binding Check:"
docker-compose port orchestrator 8000
docker-compose port fusion-service 8005

echo ""
echo "4. Service Health Checks:"
curl -s http://localhost:8001/health || echo "Image service not responding"
curl -s http://localhost:8002/health || echo "Text service not responding"
curl -s http://localhost:8003/health || echo "Context service not responding"
curl -s http://localhost:8004/health || echo "Risk service not responding"
curl -s http://localhost:8005/health || echo "Fusion service not responding"
curl -s http://localhost:8006/health || echo "Feedback service not responding"
curl -s http://localhost:8000/health || echo "Orchestrator not responding"
