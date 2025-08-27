#!/usr/bin/env python3
"""
Redis Diagnostics Script for Reality Checker WhatsApp Bot

This script provides comprehensive Redis health monitoring and diagnostics
to help identify and resolve connection stability issues.
"""

import asyncio
import time
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError, RedisError

async def check_redis_health(redis_url: str = "redis://localhost:6379/0") -> Dict[str, Any]:
    """Perform comprehensive Redis health check."""
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "redis_url": redis_url.replace("://", "://***@") if "@" in redis_url else redis_url,
        "connection_test": {"status": "unknown", "latency": None, "error": None},
        "info_stats": {},
        "memory_usage": {},
        "client_stats": {},
        "performance_metrics": {},
        "recommendations": []
    }
    
    try:
        # Create Redis client with conservative settings
        client = redis.from_url(
            redis_url,
            socket_timeout=10.0,
            socket_connect_timeout=10.0,
            retry_on_timeout=True,
            health_check_interval=30,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Test basic connectivity
        start_time = time.time()
        await asyncio.wait_for(client.ping(), timeout=5.0)
        latency = time.time() - start_time
        
        results["connection_test"] = {
            "status": "success",
            "latency": round(latency * 1000, 2),  # Convert to milliseconds
            "error": None
        }
        
        # Get Redis info
        info = await asyncio.wait_for(client.info(), timeout=5.0)
        
        # Extract key statistics
        results["info_stats"] = {
            "redis_version": info.get("redis_version", "unknown"),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            "connected_clients": info.get("connected_clients", 0),
            "blocked_clients": info.get("blocked_clients", 0),
            "total_connections_received": info.get("total_connections_received", 0),
            "rejected_connections": info.get("rejected_connections", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "expired_keys": info.get("expired_keys", 0),
            "evicted_keys": info.get("evicted_keys", 0)
        }
        
        # Memory usage analysis
        results["memory_usage"] = {
            "used_memory": info.get("used_memory", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "used_memory_rss": info.get("used_memory_rss", 0),
            "used_memory_peak": info.get("used_memory_peak", 0),
            "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
            "maxmemory": info.get("maxmemory", 0),
            "maxmemory_human": info.get("maxmemory_human", "0B"),
            "maxmemory_policy": info.get("maxmemory_policy", "unknown"),
            "mem_fragmentation_ratio": info.get("mem_fragmentation_ratio", 0)
        }
        
        # Client connection stats
        results["client_stats"] = {
            "connected_clients": info.get("connected_clients", 0),
            "client_recent_max_input_buffer": info.get("client_recent_max_input_buffer", 0),
            "client_recent_max_output_buffer": info.get("client_recent_max_output_buffer", 0),
            "blocked_clients": info.get("blocked_clients", 0)
        }
        
        # Performance metrics
        total_commands = info.get("total_commands_processed", 0)
        uptime = info.get("uptime_in_seconds", 1)
        commands_per_sec = total_commands / uptime if uptime > 0 else 0
        
        hit_rate = 0
        total_hits = info.get("keyspace_hits", 0)
        total_misses = info.get("keyspace_misses", 0)
        if total_hits + total_misses > 0:
            hit_rate = (total_hits / (total_hits + total_misses)) * 100
        
        results["performance_metrics"] = {
            "total_commands_processed": total_commands,
            "commands_per_second": round(commands_per_sec, 2),
            "keyspace_hit_rate": round(hit_rate, 2),
            "avg_ttl": info.get("avg_ttl", 0),
            "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0)
        }
        
        # Generate recommendations
        recommendations = []
        
        # Memory recommendations
        used_memory = info.get("used_memory", 0)
        max_memory = info.get("maxmemory", 0)
        if max_memory > 0:
            memory_usage_pct = (used_memory / max_memory) * 100
            if memory_usage_pct > 80:
                recommendations.append(f"HIGH MEMORY USAGE: {memory_usage_pct:.1f}% - Consider increasing maxmemory or optimizing data")
        
        # Connection recommendations
        connected_clients = info.get("connected_clients", 0)
        if connected_clients > 100:
            recommendations.append(f"HIGH CLIENT COUNT: {connected_clients} connections - Monitor for connection leaks")
        
        # Performance recommendations
        if latency > 100:  # > 100ms
            recommendations.append(f"HIGH LATENCY: {latency*1000:.1f}ms - Check network and Redis load")
        
        if hit_rate < 80:
            recommendations.append(f"LOW HIT RATE: {hit_rate:.1f}% - Review caching strategy")
        
        evicted_keys = info.get("evicted_keys", 0)
        if evicted_keys > 1000:
            recommendations.append(f"HIGH EVICTIONS: {evicted_keys} keys evicted - Consider increasing memory")
        
        results["recommendations"] = recommendations
        
        await client.close()
        
    except asyncio.TimeoutError:
        results["connection_test"] = {
            "status": "timeout",
            "latency": None,
            "error": "Connection timed out after 5 seconds"
        }
        results["recommendations"].append("CRITICAL: Redis connection timeout - Check Redis server status")
        
    except ConnectionError as e:
        results["connection_test"] = {
            "status": "connection_error",
            "latency": None,
            "error": str(e)
        }
        results["recommendations"].append("CRITICAL: Cannot connect to Redis - Check server and network")
        
    except Exception as e:
        results["connection_test"] = {
            "status": "error",
            "latency": None,
            "error": str(e)
        }
        results["recommendations"].append(f"ERROR: Unexpected error - {str(e)}")
    
    return results


async def monitor_redis_performance(redis_url: str = "redis://localhost:6379/0", duration: int = 60):
    """Monitor Redis performance over time."""
    
    print(f"🔍 Monitoring Redis performance for {duration} seconds...")
    print(f"📊 Redis URL: {redis_url.replace('://', '://***@') if '@' in redis_url else redis_url}")
    print("-" * 80)
    
    try:
        client = redis.from_url(
            redis_url,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
            encoding="utf-8",
            decode_responses=True
        )
        
        start_time = time.time()
        measurements = []
        
        while time.time() - start_time < duration:
            try:
                # Measure ping latency
                ping_start = time.time()
                await asyncio.wait_for(client.ping(), timeout=2.0)
                ping_latency = (time.time() - ping_start) * 1000  # Convert to ms
                
                # Get basic stats
                info = await asyncio.wait_for(client.info(), timeout=2.0)
                
                measurement = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "ping_latency_ms": round(ping_latency, 2),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                    "commands_per_sec": info.get("instantaneous_ops_per_sec", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0)
                }
                
                measurements.append(measurement)
                
                # Print real-time stats
                print(f"⏱️  {datetime.now().strftime('%H:%M:%S')} | "
                      f"Latency: {ping_latency:.1f}ms | "
                      f"Clients: {measurement['connected_clients']} | "
                      f"Memory: {measurement['used_memory_mb']}MB | "
                      f"Ops/sec: {measurement['commands_per_sec']}")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except asyncio.TimeoutError:
                print(f"⚠️  {datetime.now().strftime('%H:%M:%S')} | TIMEOUT - Redis not responding")
                measurements.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": "timeout"
                })
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"❌ {datetime.now().strftime('%H:%M:%S')} | ERROR - {str(e)}")
                measurements.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": str(e)
                })
                await asyncio.sleep(5)
        
        await client.close()
        
        # Calculate summary statistics
        successful_measurements = [m for m in measurements if "error" not in m]
        if successful_measurements:
            latencies = [m["ping_latency_ms"] for m in successful_measurements]
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            min_latency = min(latencies)
            
            print("\n" + "=" * 80)
            print("📈 PERFORMANCE SUMMARY")
            print("=" * 80)
            print(f"Total measurements: {len(measurements)}")
            print(f"Successful measurements: {len(successful_measurements)}")
            print(f"Error rate: {((len(measurements) - len(successful_measurements)) / len(measurements) * 100):.1f}%")
            print(f"Average latency: {avg_latency:.2f}ms")
            print(f"Min latency: {min_latency:.2f}ms")
            print(f"Max latency: {max_latency:.2f}ms")
            
            if avg_latency > 50:
                print("⚠️  WARNING: High average latency detected")
            if max_latency > 200:
                print("🚨 CRITICAL: Very high peak latency detected")
        
    except Exception as e:
        print(f"❌ Failed to monitor Redis: {e}")


async def main():
    """Main diagnostics function."""
    import os
    
    # Get Redis URL from environment or use default
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    print("🔧 Redis Diagnostics Tool")
    print("=" * 50)
    
    # Perform health check
    print("\n1️⃣ Performing Redis Health Check...")
    health_results = await check_redis_health(redis_url)
    
    print(f"\n📊 REDIS HEALTH REPORT")
    print("-" * 30)
    print(f"Connection Status: {health_results['connection_test']['status']}")
    if health_results['connection_test']['latency']:
        print(f"Connection Latency: {health_results['connection_test']['latency']}ms")
    
    if health_results['info_stats']:
        print(f"Redis Version: {health_results['info_stats']['redis_version']}")
        print(f"Connected Clients: {health_results['info_stats']['connected_clients']}")
        print(f"Memory Usage: {health_results['memory_usage']['used_memory_human']}")
        print(f"Hit Rate: {health_results['performance_metrics']['keyspace_hit_rate']:.1f}%")
    
    if health_results['recommendations']:
        print(f"\n⚠️  RECOMMENDATIONS:")
        for rec in health_results['recommendations']:
            print(f"   • {rec}")
    
    # Save detailed results
    with open("redis_health_report.json", "w") as f:
        json.dump(health_results, f, indent=2)
    print(f"\n💾 Detailed report saved to: redis_health_report.json")
    
    # Ask if user wants to monitor performance
    try:
        response = input("\n🔍 Would you like to monitor Redis performance for 60 seconds? (y/N): ")
        if response.lower().startswith('y'):
            await monitor_redis_performance(redis_url, 60)
    except KeyboardInterrupt:
        print("\n👋 Diagnostics interrupted by user")
    except EOFError:
        print("\n📝 Skipping performance monitoring")


if __name__ == "__main__":
    asyncio.run(main())