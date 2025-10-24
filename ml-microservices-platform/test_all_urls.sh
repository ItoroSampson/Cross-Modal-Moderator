#!/bin/bash
CODESPACE="urban-carnival-q7pq56j7p4rgh4qg9"

echo "🌐 Testing All Possible URL Formats"
echo "==================================="

urls=(
    "https://${CODESPACE}-8000.preview.app.github.dev/health"
    "https://8000-${CODESPACE}.preview.app.github.dev/health"
    "https://${CODESPACE}.preview.app.github.dev:8000/health"
    "http://${CODESPACE}-8000.preview.app.github.dev/health"
    "http://8000-${CODESPACE}.preview.app.github.dev/health"
)

for url in "${urls[@]}"; do
    echo -n "Testing: $url ... "
    if curl -k -s --connect-timeout 5 "$url" | grep -q "healthy"; then
        echo "✅ WORKING!"
        echo "   🎯 USE THIS URL: $url"
        break
    else
        echo "❌ failed"
    fi
done

echo ""
echo "🔍 Port Forwarding Status:"
gh codespace ports list
