"""
Tests for WebSocket real-time monitoring functionality.

This module tests WebSocket connections, metrics broadcasting, and alert notifications.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from websockets.exceptions import ConnectionClosedOK

from app.main import app
from app.utils.websocket import (
    WebSocketManager, get_websocket_manager, reset_websocket_manager,
    websocket_alert_handler
)
from app.utils.error_tracking import Alert, AlertType, AlertSeverity
from app.utils.metrics import get_metrics_collector, reset_metrics_collector


class TestWebSocketManager:
    """Test cases for the WebSocketManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_websocket_manager()
        self.manager = WebSocketManager()
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        """Test WebSocket connection and disconnection."""
        # Create mock WebSocket
        mock_websocket = AsyncMock(spec=WebSocket)
        
        # Connect
        await self.manager.connect(mock_websocket, "test_user")
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()
        assert mock_websocket in self.manager.active_connections
        assert self.manager.authenticated_connections[mock_websocket] == "test_user"
        
        # Disconnect
        self.manager.disconnect(mock_websocket)
        
        # Verify disconnection
        assert mock_websocket not in self.manager.active_connections
        assert mock_websocket not in self.manager.authenticated_connections
    
    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting messages to connected clients."""
        # Create mock WebSockets
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        
        # Connect both
        await self.manager.connect(mock_websocket1, "user1")
        await self.manager.connect(mock_websocket2, "user2")
        
        # Broadcast a message
        test_message = {"type": "test", "data": "hello"}
        await self.manager.broadcast(test_message)
        
        # Verify both received the message
        mock_websocket1.send_json.assert_called_once_with(test_message)
        mock_websocket2.send_json.assert_called_once_with(test_message)
    
    @pytest.mark.asyncio
    async def test_broadcast_with_disconnected_client(self):
        """Test broadcasting with a client that disconnects during send."""
        # Create mock WebSockets
        mock_websocket1 = AsyncMock(spec=WebSocket)
        mock_websocket2 = AsyncMock(spec=WebSocket)
        
        # Make the second one fail when sending
        mock_websocket2.send_json.side_effect = ConnectionClosedOK(1000, "Client disconnected")
        
        # Connect both
        await self.manager.connect(mock_websocket1, "user1")
        await self.manager.connect(mock_websocket2, "user2")
        
        # Broadcast a message
        test_message = {"type": "test", "data": "hello"}
        await self.manager.broadcast(test_message)
        
        # Verify first client received the message
        mock_websocket1.send_json.assert_called_once_with(test_message)
        
        # Verify second client was disconnected
        assert mock_websocket2 not in self.manager.active_connections
    
    @pytest.mark.asyncio
    async def test_broadcast_metrics(self):
        """Test broadcasting metrics to connected clients."""
        # Reset metrics collector
        reset_metrics_collector()
        metrics = get_metrics_collector()
        
        # Record some test metrics
        metrics.record_request("GET", "/test", 200, 0.5)
        
        # Create mock WebSocket
        mock_websocket = AsyncMock(spec=WebSocket)
        
        # Connect
        await self.manager.connect(mock_websocket, "test_user")
        
        # Broadcast metrics
        await self.manager.broadcast_metrics()
        
        # Verify message was sent
        assert mock_websocket.send_json.called
        
        # Get the sent message
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "metrics_update"
        assert "timestamp" in call_args
        assert "data" in call_args
        assert "requests" in call_args["data"]
        assert call_args["data"]["requests"]["total"] == 1
    
    @pytest.mark.asyncio
    async def test_broadcast_alert(self):
        """Test broadcasting alerts to connected clients."""
        # Create a test alert
        alert = Alert(
            id="test-alert-1",
            alert_type=AlertType.ERROR_RATE,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            message="This is a test alert",
            timestamp=datetime.now(timezone.utc),
            context={"test": "data"}
        )
        
        # Create mock WebSocket
        mock_websocket = AsyncMock(spec=WebSocket)
        
        # Connect
        await self.manager.connect(mock_websocket, "test_user")
        
        # Broadcast alert
        await self.manager.broadcast_alert(alert)
        
        # Verify message was sent
        assert mock_websocket.send_json.called
        
        # Get the sent message
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "alert"
        assert "timestamp" in call_args
        assert "data" in call_args
        assert call_args["data"]["id"] == "test-alert-1"
        assert call_args["data"]["title"] == "Test Alert"
        assert call_args["data"]["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_broadcast_task_lifecycle(self):
        """Test starting and stopping the broadcast task."""
        # Start the broadcast task
        self.manager.start_broadcast_task()
        assert self.manager._running is True
        assert self.manager._broadcast_task is not None
        
        # Stop the broadcast task
        self.manager.stop_broadcast_task()
        assert self.manager._running is False
        
        # Wait for task to complete
        await asyncio.sleep(0.1)
        assert self.manager._broadcast_task.done()


@pytest.mark.asyncio
async def test_websocket_alert_handler():
    """Test the WebSocket alert handler function."""
    # Reset WebSocket manager
    reset_websocket_manager()
    manager = get_websocket_manager()
    
    # Create a mock for the broadcast_alert method
    original_broadcast_alert = manager.broadcast_alert
    manager.broadcast_alert = AsyncMock()
    
    try:
        # Create a test alert
        alert = Alert(
            id="test-alert-1",
            alert_type=AlertType.ERROR_RATE,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            message="This is a test alert",
            timestamp=datetime.now(timezone.utc),
            context={"test": "data"}
        )
        
        # Call the handler
        websocket_alert_handler(alert)
        
        # Wait for the async task to complete
        await asyncio.sleep(0.1)
        
        # Verify broadcast_alert was called with the alert
        manager.broadcast_alert.assert_called_once()
        assert manager.broadcast_alert.call_args[0][0] == alert
        
    finally:
        # Restore original method
        manager.broadcast_alert = original_broadcast_alert


class TestWebSocketEndpoint:
    """Test cases for the WebSocket endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_websocket_endpoint_authentication(self, client):
        """Test WebSocket endpoint authentication."""
        # Mock the authentication service
        with patch("app.api.monitoring.get_auth_service") as mock_get_auth:
            mock_auth_service = AsyncMock()
            mock_get_auth.return_value = mock_auth_service
            
            # Mock token validation - invalid token
            mock_auth_service.validate_jwt_token.return_value = Mock(valid=False)
            
            # Try to connect with invalid token
            with pytest.raises(Exception):
                with client.websocket_connect("/monitoring/ws?token=invalid") as websocket:
                    pass
            
            # Mock token validation - valid token
            mock_auth_service.validate_jwt_token.return_value = Mock(valid=True, user_id="test_user")
            
            # Connect with valid token
            with patch("app.api.monitoring.get_websocket_manager") as mock_get_manager:
                mock_manager = AsyncMock()
                mock_get_manager.return_value = mock_manager
                
                # Mock the connect method
                mock_manager.connect = AsyncMock()
                
                # Try to connect
                try:
                    with client.websocket_connect("/monitoring/ws?token=valid") as websocket:
                        # This will fail because we're mocking, but we just want to verify the connect call
                        websocket.receive_text()
                except:
                    pass
                
                # Verify connect was called with the user ID
                mock_manager.connect.assert_called_once()
                assert mock_manager.connect.call_args[0][1] == "test_user"


if __name__ == "__main__":
    pytest.main([__file__])