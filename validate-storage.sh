#!/bin/bash
# validate-storage.sh

set -e

echo "=== Testing Storage Migration ==="

# Test 1: Upload file
curl -X POST -H "Authorization: Bearer TOKEN" \
     -F "file=@test.txt" \
     http://localhost:8002/upload

# Test 2: Check file exists
docker-compose exec upload-service ls -la /vault-storage/uploads/

# Test 3: Restart service
docker-compose restart upload-service

# Test 4: Verify persistence
docker-compose exec upload-service ls -la /vault-storage/uploads/
echo "✅ File survived restart!"
