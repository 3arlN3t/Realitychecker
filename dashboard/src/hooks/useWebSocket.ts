import { useState, useEffect, useCallback } from 'react';

type ConnectionStatus = 'Connecting' | 'Connected' | 'Disconnected' | 'Error';

interface UseWebSocketReturn {
  lastMessage: string | null;
  sendMessage: (message: string) => void;
  connectionStatus: ConnectionStatus;
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('Disconnected');

  // Get the token from localStorage
  const getAuthToken = () => localStorage.getItem('token');

  // Create WebSocket connection
  useEffect(() => {
    // Add token to URL if available
    const token = getAuthToken();
    const wsUrl = token ? `${url}?token=${token}` : url;
    
    // Determine WebSocket protocol based on current protocol
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const fullUrl = `${protocol}//${host}${wsUrl}`;
    
    setConnectionStatus('Connecting');
    const ws = new WebSocket(fullUrl);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnectionStatus('Connected');
    };
    
    ws.onmessage = (event) => {
      setLastMessage(event.data);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('Error');
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnectionStatus('Disconnected');
    };
    
    setSocket(ws);
    
    // Cleanup on unmount
    return () => {
      ws.close();
    };
  }, [url]);

  // Reconnect logic
  useEffect(() => {
    if (connectionStatus === 'Disconnected' || connectionStatus === 'Error') {
      const reconnectTimer = setTimeout(() => {
        console.log('Attempting to reconnect WebSocket...');
        // Force component re-render to recreate the WebSocket
        setSocket(null);
      }, 5000); // Try to reconnect after 5 seconds
      
      return () => clearTimeout(reconnectTimer);
    }
  }, [connectionStatus]);

  // Send message function
  const sendMessage = useCallback((message: string) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(message);
    } else {
      console.error('WebSocket not connected');
    }
  }, [socket]);

  // Send ping every 30 seconds to keep connection alive
  useEffect(() => {
    if (connectionStatus === 'Connected') {
      const pingInterval = setInterval(() => {
        sendMessage('ping');
      }, 30000);
      
      return () => clearInterval(pingInterval);
    }
  }, [connectionStatus, sendMessage]);

  return { lastMessage, sendMessage, connectionStatus };
};