import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    this.readyState = MockWebSocket.CONNECTING;
    
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  send(message: string) {
    if (this.readyState === MockWebSocket.OPEN) {
      // Simulate message being sent
      console.log('Mock WebSocket sending:', message);
    } else {
      throw new Error('WebSocket is not connected');
    }
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }

  // Method to simulate receiving a message
  simulateMessage(data: string) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data }));
    }
  }

  // Method to simulate an error
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
}

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock location
Object.defineProperty(window, 'location', {
  value: {
    protocol: 'https:',
    host: 'localhost:3000',
  },
});

// Replace global WebSocket with mock
global.WebSocket = MockWebSocket as any;

describe('useWebSocket', () => {
  let mockWebSocket: MockWebSocket;

  beforeEach(() => {
    mockLocalStorage.getItem.mockClear();
    jest.clearAllTimers();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('initializes with correct connection status', () => {
    const { result } = renderHook(() => useWebSocket('/test-ws'));
    
    expect(result.current.connectionStatus).toBe('Connecting');
    expect(result.current.lastMessage).toBe(null);
  });

  it('connects with authentication token', () => {
    mockLocalStorage.getItem.mockReturnValue('test-token');
    
    const { result } = renderHook(() => useWebSocket('/test-ws'));
    
    expect(result.current.connectionStatus).toBe('Connecting');
    
    // Simulate connection opening
    act(() => {
      jest.advanceTimersByTime(0);
    });
    
    expect(result.current.connectionStatus).toBe('Connected');
  });

  it('connects without authentication token', () => {
    mockLocalStorage.getItem.mockReturnValue(null);
    
    const { result } = renderHook(() => useWebSocket('/test-ws'));
    
    expect(result.current.connectionStatus).toBe('Connecting');
    
    // Simulate connection opening
    act(() => {
      jest.advanceTimersByTime(0);
    });
    
    expect(result.current.connectionStatus).toBe('Connected');
  });

  it('receives messages correctly', () => {
    const { result } = renderHook(() => useWebSocket('/test-ws'));
    
    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(0);
    });
    
    // Get the WebSocket instance
    const wsInstance = (global.WebSocket as any).mock?.instances?.[0];
    
    if (wsInstance) {
      // Simulate receiving a message
      act(() => {
        wsInstance.simulateMessage('test message');
      });
      
      expect(result.current.lastMessage).toBe('test message');
    }
  });

  it('handles connection errors', () => {
    const { result } = renderHook(() => useWebSocket('/test-ws'));
    
    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(0);
    });
    
    // Get the WebSocket instance
    const wsInstance = (global.WebSocket as any).mock?.instances?.[0];
    
    if (wsInstance) {
      // Simulate an error
      act(() => {
        wsInstance.simulateError();
      });
      
      expect(result.current.connectionStatus).toBe('Error');
    }
  });

  it('handles connection close', () => {
    const { result } = renderHook(() => useWebSocket('/test-ws'));
    
    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(0);
    });
    
    // Get the WebSocket instance
    const wsInstance = (global.WebSocket as any).mock?.instances?.[0];
    
    if (wsInstance) {
      // Simulate connection close
      act(() => {
        wsInstance.close();
      });
      
      expect(result.current.connectionStatus).toBe('Disconnected');
    }
  });

  it('attempts to reconnect after disconnection', () => {
    const { result } = renderHook(() => useWebSocket('/test-ws'));
    
    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(0);
    });
    
    // Get the WebSocket instance
    const wsInstance = (global.WebSocket as any).mock?.instances?.[0];
    
    if (wsInstance) {
      // Simulate connection close
      act(() => {
        wsInstance.close();
      });
      
      expect(result.current.connectionStatus).toBe('Disconnected');
      
      // Advance timers to trigger reconnection
      act(() => {
        jest.advanceTimersByTime(5000);
      });
      
      // Should attempt to reconnect
      expect(result.current.connectionStatus).toBe('Connecting');
    }
  });

  it('sends messages when connected', () => {
    const { result } = renderHook(() => useWebSocket('/test-ws'));
    
    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(0);
    });
    
    expect(result.current.connectionStatus).toBe('Connected');
    
    // Mock the send method
    const sendSpy = jest.spyOn(WebSocket.prototype, 'send');
    
    act(() => {
      result.current.sendMessage('test message');
    });
    
    expect(sendSpy).toHaveBeenCalledWith('test message');
    
    sendSpy.mockRestore();
  });

  it('does not send messages when disconnected', () => {
    const { result } = renderHook(() => useWebSocket('/test-ws'));
    
    // Don't wait for connection, try to send immediately
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    
    act(() => {
      result.current.sendMessage('test message');
    });
    
    expect(consoleSpy).toHaveBeenCalledWith('WebSocket not connected');
    
    consoleSpy.mockRestore();
  });

  it('sends ping messages periodically when connected', () => {
    const { result } = renderHook(() => useWebSocket('/test-ws'));
    
    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(0);
    });
    
    expect(result.current.connectionStatus).toBe('Connected');
    
    // Mock the send method
    const sendSpy = jest.spyOn(WebSocket.prototype, 'send');
    
    // Advance timers to trigger ping
    act(() => {
      jest.advanceTimersByTime(30000);
    });
    
    expect(sendSpy).toHaveBeenCalledWith('ping');
    
    sendSpy.mockRestore();
  });

  it('cleans up on unmount', () => {
    const { result, unmount } = renderHook(() => useWebSocket('/test-ws'));
    
    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(0);
    });
    
    const closeSpy = jest.spyOn(WebSocket.prototype, 'close');
    
    unmount();
    
    expect(closeSpy).toHaveBeenCalled();
    
    closeSpy.mockRestore();
  });
});