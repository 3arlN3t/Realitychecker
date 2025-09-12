#!/bin/bash

# Redis Restart Script with Health Monitoring
# This script safely restarts Redis with the new optimized configuration

set -e

echo "🔧 Redis Restart and Optimization Script"
echo "========================================"

# Function to check if Redis is running
check_redis_status() {
    if docker-compose ps redis | grep -q "Up"; then
        echo "✅ Redis container is running"
        return 0
    else
        echo "❌ Redis container is not running"
        return 1
    fi
}

# Function to test Redis connectivity
test_redis_connection() {
    echo "🔍 Testing Redis connection..."
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis is responding to ping"
        return 0
    else
        echo "❌ Redis is not responding"
        return 1
    fi
}

# Function to show Redis info
show_redis_info() {
    echo "📊 Redis Information:"
    echo "--------------------"
    docker-compose exec -T redis redis-cli info server | grep -E "(redis_version|uptime_in_seconds|tcp_port)"
    docker-compose exec -T redis redis-cli info memory | grep -E "(used_memory_human|maxmemory_human|maxmemory_policy)"
    docker-compose exec -T redis redis-cli info clients | grep -E "(connected_clients|blocked_clients)"
}

# Main execution
echo "1️⃣ Checking current Redis status..."
if check_redis_status; then
    echo "2️⃣ Stopping Redis container..."
    docker-compose stop redis
    sleep 2
fi

echo "3️⃣ Removing old Redis container..."
docker-compose rm -f redis || true

echo "4️⃣ Starting Redis with new configuration..."
docker-compose up -d redis

echo "5️⃣ Waiting for Redis to start..."
sleep 5

# Wait for Redis to be ready
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if test_redis_connection; then
        break
    fi
    echo "⏳ Waiting for Redis... (attempt $attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Redis failed to start after $max_attempts attempts"
    echo "📋 Checking Redis logs..."
    docker-compose logs --tail=20 redis
    exit 1
fi

echo "6️⃣ Redis started successfully!"
show_redis_info

echo "7️⃣ Restarting application to pick up new Redis settings..."
docker-compose restart app

echo "8️⃣ Waiting for application to start..."
sleep 10

echo "9️⃣ Final health check..."
if check_redis_status && test_redis_connection; then
    echo "✅ Redis optimization completed successfully!"
    echo ""
    echo "📈 Recommended next steps:"
    echo "   • Monitor application logs for Redis stability"
    echo "   • Run: python redis_diagnostics.py for detailed health check"
    echo "   • Check webhook response times in the next few minutes"
    echo ""
    echo "🔍 To monitor Redis performance:"
    echo "   docker-compose exec redis redis-cli monitor"
else
    echo "❌ Redis optimization may have issues"
    echo "📋 Check logs with: docker-compose logs redis"
fi