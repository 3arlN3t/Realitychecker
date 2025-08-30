#!/usr/bin/env python3
"""
Continuous health monitoring script for Reality Checker WhatsApp Bot.

This script continuously monitors all external APIs and services,
providing real-time status updates and alerts.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import argparse


class HealthMonitor:
    """Continuous health monitoring system."""
    
    def __init__(self, base_url: str = "http://localhost:8000", interval: int = 30):
        self.base_url = base_url
        self.interval = interval
        self.previous_status = {}
        self.alert_history = []
        
    async def check_service_health(self, service: str) -> Dict[str, Any]:
        """Check health of a specific service."""
        endpoint = f"/health/{service}" if service != "overall" else "/health/detailed"
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                if response.status_code < 500:
                    data = response.json()
                    return {
                        "service": service,
                        "status": data.get("status", "unknown"),
                        "response_time_ms": data.get("response_time_ms", 0),
                        "message": data.get("message", ""),
                        "timestamp": datetime.now().isoformat(),
                        "http_status": response.status_code,
                        "healthy": True
                    }
                else:
                    return {
                        "service": service,
                        "status": "unhealthy",
                        "response_time_ms": 0,
                        "message": f"HTTP {response.status_code}",
                        "timestamp": datetime.now().isoformat(),
                        "http_status": response.status_code,
                        "healthy": False
                    }
                    
        except Exception as e:
            return {
                "service": service,
                "status": "error",
                "response_time_ms": 0,
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
                "http_status": 0,
                "healthy": False
            }
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services."""
        services = ["openai", "twilio", "database", "redis", "ngrok"]
        
        # Check all services concurrently
        results = await asyncio.gather(
            *[self.check_service_health(service) for service in services],
            return_exceptions=True
        )
        
        # Also get overall system health
        overall_result = await self.check_service_health("overall")
        
        service_results = {}
        for i, service in enumerate(services):
            if isinstance(results[i], Exception):
                service_results[service] = {
                    "service": service,
                    "status": "error",
                    "message": str(results[i]),
                    "healthy": False
                }
            else:
                service_results[service] = results[i]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall": overall_result,
            "services": service_results
        }
    
    def detect_status_changes(self, current_status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect changes in service status."""
        changes = []
        
        for service, current in current_status["services"].items():
            previous = self.previous_status.get("services", {}).get(service, {})
            
            if previous and previous.get("status") != current.get("status"):
                changes.append({
                    "service": service,
                    "previous_status": previous.get("status"),
                    "current_status": current.get("status"),
                    "timestamp": current.get("timestamp"),
                    "message": current.get("message", "")
                })
        
        return changes
    
    def print_status_summary(self, status: Dict[str, Any], changes: List[Dict[str, Any]]):
        """Print current status summary."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*60}")
        print(f"🏥 HEALTH MONITOR - {timestamp}")
        print(f"{'='*60}")
        
        # Overall status
        overall = status["overall"]
        overall_emoji = {
            "healthy": "✅",
            "degraded": "⚠️", 
            "unhealthy": "❌",
            "error": "💥"
        }.get(overall["status"], "❓")
        
        print(f"Overall System: {overall_emoji} {overall['status'].upper()}")
        print(f"Response Time: {overall.get('response_time_ms', 0):.1f}ms")
        
        # Individual services
        print(f"\n📊 Service Status:")
        for service, data in status["services"].items():
            status_emoji = {
                "healthy": "✅",
                "degraded": "⚠️",
                "unhealthy": "❌", 
                "not_configured": "⚙️",
                "not_available": "🚫",
                "error": "💥"
            }.get(data["status"], "❓")
            
            response_time = data.get("response_time_ms", 0)
            print(f"  {status_emoji} {service.upper():<10}: {data['status']:<12} ({response_time:>6.1f}ms)")
            
            if data.get("message") and data["status"] not in ["healthy", "not_available"]:
                print(f"     └─ {data['message']}")
        
        # Status changes
        if changes:
            print(f"\n🔄 Status Changes:")
            for change in changes:
                change_emoji = "🔴" if change["current_status"] in ["unhealthy", "error"] else "🟡" if change["current_status"] == "degraded" else "🟢"
                print(f"  {change_emoji} {change['service'].upper()}: {change['previous_status']} → {change['current_status']}")
                if change.get("message"):
                    print(f"     └─ {change['message']}")
        
        print(f"{'='*60}")
    
    def log_alert(self, alert: Dict[str, Any]):
        """Log an alert to history."""
        self.alert_history.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
    
    def check_for_alerts(self, status: Dict[str, Any], changes: List[Dict[str, Any]]):
        """Check for conditions that should trigger alerts."""
        # Alert on service failures
        for service, data in status["services"].items():
            if data["status"] in ["unhealthy", "error"] and service in ["openai", "twilio", "database"]:
                alert = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "service_failure",
                    "severity": "critical",
                    "service": service,
                    "message": f"{service.upper()} service is {data['status']}: {data.get('message', '')}",
                    "status": data["status"]
                }
                self.log_alert(alert)
                print(f"🚨 CRITICAL ALERT: {alert['message']}")
        
        # Alert on status changes to unhealthy
        for change in changes:
            if change["current_status"] in ["unhealthy", "error"]:
                alert = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "status_change",
                    "severity": "warning",
                    "service": change["service"],
                    "message": f"{change['service'].upper()} changed from {change['previous_status']} to {change['current_status']}",
                    "previous_status": change["previous_status"],
                    "current_status": change["current_status"]
                }
                self.log_alert(alert)
                print(f"⚠️  WARNING: {alert['message']}")
    
    async def monitor_continuously(self, quiet: bool = False):
        """Run continuous monitoring."""
        print(f"🏥 Starting health monitoring...")
        print(f"Base URL: {self.base_url}")
        print(f"Check interval: {self.interval} seconds")
        print(f"Press Ctrl+C to stop")
        
        try:
            while True:
                current_status = await self.check_all_services()
                changes = self.detect_status_changes(current_status)
                
                if not quiet:
                    self.print_status_summary(current_status, changes)
                
                # Check for alerts
                self.check_for_alerts(current_status, changes)
                
                # Update previous status
                self.previous_status = current_status
                
                # Wait for next check
                await asyncio.sleep(self.interval)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n💥 Monitoring error: {e}")
    
    async def run_single_check(self):
        """Run a single health check."""
        print(f"🏥 Running single health check...")
        
        status = await self.check_all_services()
        changes = self.detect_status_changes(status)
        
        self.print_status_summary(status, changes)
        
        # Return exit code based on overall health
        overall_status = status["overall"]["status"]
        if overall_status == "healthy":
            return 0
        elif overall_status == "degraded":
            return 1
        else:
            return 2


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Health monitoring for Reality Checker WhatsApp Bot")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the application")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run single check and exit")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode (only show alerts)")
    
    args = parser.parse_args()
    
    monitor = HealthMonitor(base_url=args.url, interval=args.interval)
    
    if args.once:
        exit_code = await monitor.run_single_check()
        exit(exit_code)
    else:
        await monitor.monitor_continuously(quiet=args.quiet)


if __name__ == "__main__":
    asyncio.run(main())