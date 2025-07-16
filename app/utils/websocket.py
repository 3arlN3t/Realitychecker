"""
WebSocket server for real-time metrics and alerts broadcasting.

This module provides WebSocket functionality for sending real-time updates
to connected dashboard clients.
"""

import asyncio
import json
from typing import Dict, Set, Any, Optional
from datetime import datetime, timezone

import websockets
from fastapi import WebSocket, WebSocketDisconnect

from app.utils.logging import get_logger
from app.utils.metrics import get_metrics_collector
from app.utils.error_tracking import get_error_tracker, Alert

logger = get_logger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Set[WebSocket] = set()
        self.authenticated_connections: Dict[WebSocket, str] = {}  # WebSocket -> user_id
        self._broadcast_task: Optional[asyncio.Task] = None
        self._running = False
        logger.info("WebSocket manager initialized")
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Connect a new WebSocket client.
        
        Args:
            websocket: The WebSocket connection
            user_id: User identifier for the connection
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        self.authenticated_connections[websocket] = user_id
        logger.info(f"WebSocket client connected: {user_id}")
        
        # Start broadcast task if not running
        if not self._running:
            self.start_broadcast_task()
    
    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket client.
        
        Args:
            websocket: The WebSocket connection to disconnect
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if websocket in self.authenticated_connections:
            user_id = self.authenticated_connections.pop(websocket)
            logger.info(f"WebSocket client disconnected: {user_id}")
        
        # Stop broadcast task if no connections
        if not self.active_connections and self._running:
            self.stop_broadcast_task()
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast
        """
        if not self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to client: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_metrics(self):
        """Broadcast current metrics to all connected clients."""
        metrics_collector = get_metrics_collector()
        current_metrics = metrics_collector.get_current_metrics()
        
        await self.broadcast({
            "type": "metrics_update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": current_metrics
        })
    
    async def broadcast_alert(self, alert: Alert):
        """
        Broadcast an alert to all connected clients.
        
        Args:
            alert: The alert to broadcast
        """
        await self.broadcast({
            "type": "alert",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": alert.id,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "alert_timestamp": alert.timestamp.isoformat(),
                "context": alert.context
            }
        })
    
    async def _broadcast_loop(self):
        """Background task that periodically broadcasts metrics."""
        try:
            while self._running:
                await self.broadcast_metrics()
                await asyncio.sleep(5)  # Broadcast every 5 seconds
        except asyncio.CancelledError:
            logger.info("Broadcast task cancelled")
        except Exception as e:
            logger.error(f"Error in broadcast loop: {e}", exc_info=True)
    
    def start_broadcast_task(self):
        """Start the background broadcast task."""
        if self._broadcast_task is None or self._broadcast_task.done():
            self._running = True
            self._broadcast_task = asyncio.create_task(self._broadcast_loop())
            logger.info("Started WebSocket broadcast task")
    
    def stop_broadcast_task(self):
        """Stop the background broadcast task."""
        if self._broadcast_task and not self._broadcast_task.done():
            self._running = False
            self._broadcast_task.cancel()
            logger.info("Stopped WebSocket broadcast task")


# Global WebSocket manager instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


def reset_websocket_manager():
    """Reset the global WebSocket manager (useful for testing)."""
    global _websocket_manager
    if _websocket_manager:
        if _websocket_manager._running:
            _websocket_manager.stop_broadcast_task()
    _websocket_manager = None


# Alert handler for WebSocket broadcasts
def websocket_alert_handler(alert: Alert):
    """
    Alert handler that broadcasts alerts via WebSocket.
    
    Args:
        alert: The alert to broadcast
    """
    manager = get_websocket_manager()
    
    # Create task to broadcast alert
    asyncio.create_task(manager.broadcast_alert(alert))