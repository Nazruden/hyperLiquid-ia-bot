import { useState, useEffect, useRef, useCallback } from "react";
import type {
  WebSocketMessage,
  BotStatus,
  LiveMetrics,
} from "../types/trading";

interface UseWebSocketOptions {
  url?: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  initialDelay?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  connectionError: string | null;
  lastMessage: WebSocketMessage | null;
  botStatus: BotStatus | null;
  liveMetrics: LiveMetrics | null;
  connect: () => void;
  disconnect: () => void;
  sendMessage: (message: Record<string, unknown>) => void;
}

export const useWebSocket = (
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const {
    url = "ws://localhost:8000/ws",
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    initialDelay = 2000, // Add initial delay to wait for server readiness
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const initialConnectionAttemptedRef = useRef(false);

  // Health check function to verify server readiness
  const checkServerHealth = useCallback(async (): Promise<boolean> => {
    try {
      // Create a timeout promise
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error("Health check timeout")), 5000)
      );

      const fetchPromise = fetch("http://localhost:8000/health", {
        method: "GET",
      });

      const response = await Promise.race([fetchPromise, timeoutPromise]);
      return response.ok;
    } catch (error) {
      console.log(
        "Server health check failed, will retry WebSocket connection:",
        error
      );
      return false;
    }
  }, []);

  const connect = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log("WebSocket already connected");
      return;
    }

    // For initial connection, check server health first
    if (!initialConnectionAttemptedRef.current) {
      console.log("Checking server health before WebSocket connection...");
      const serverReady = await checkServerHealth();
      if (!serverReady) {
        console.log("Server not ready, scheduling retry...");
        scheduleReconnect();
        return;
      }
    }

    console.log("Connecting to WebSocket:", url);
    setConnectionError(null);

    try {
      const ws = new WebSocket(url);

      // Set a connection timeout
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          console.log("WebSocket connection timeout");
          ws.close();
          setConnectionError("Connection timeout");
          if (reconnectCountRef.current < reconnectAttempts) {
            scheduleReconnect();
          }
        }
      }, 10000); // 10 second timeout

      ws.onopen = () => {
        clearTimeout(connectionTimeout);
        console.log("WebSocket connected");
        setIsConnected(true);
        setConnectionError(null);
        reconnectCountRef.current = 0;
        initialConnectionAttemptedRef.current = true;
      };

      ws.onclose = (event) => {
        clearTimeout(connectionTimeout);
        console.log("WebSocket disconnected:", event.code, event.reason);
        setIsConnected(false);

        // Attempt reconnection if not manually closed
        if (
          event.code !== 1000 && // Normal closure
          reconnectCountRef.current < reconnectAttempts
        ) {
          scheduleReconnect();
        }
      };

      ws.onerror = (error) => {
        clearTimeout(connectionTimeout);
        console.error("WebSocket error:", error);
        setConnectionError("WebSocket connection failed");
        setIsConnected(false);

        // Attempt reconnection
        if (reconnectCountRef.current < reconnectAttempts) {
          scheduleReconnect();
        } else {
          setConnectionError(
            `Failed to connect after ${reconnectAttempts} attempts`
          );
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log("Received WebSocket message:", message);

          setLastMessage({
            type: message.type,
            data: message.data,
            timestamp: new Date().toISOString(),
          });

          // Handle different message types
          switch (message.type) {
            case "connection":
              // Connection acknowledgment from server
              console.log(
                "✅ WebSocket connection acknowledged:",
                message.status
              );
              break;
            case "snapshot":
              // Initial data snapshot from server
              console.log("📊 Received data snapshot");
              if (message.data?.bot_status) {
                setBotStatus(message.data.bot_status);
              }
              if (message.data?.metrics) {
                setLiveMetrics(message.data.metrics);
              }
              break;
            case "bot_status":
              setBotStatus(message.data);
              break;
            case "live_metrics":
              setLiveMetrics(message.data);
              break;
            case "new_trade":
            case "position_update":
            case "ai_insight":
            case "alert":
              // These are handled by the lastMessage state
              break;
            case "pong":
              // Handle pong response (don't log as unknown)
              break;
            default:
              console.log("Unknown message type:", message.type);
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("Error creating WebSocket:", error);
      setConnectionError("Failed to create WebSocket connection");
    }
  }, [url, reconnectAttempts, checkServerHealth]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    reconnectCountRef.current += 1;

    // Exponential backoff with jitter for better reconnection behavior
    const baseDelay = reconnectInterval;
    const exponentialDelay =
      baseDelay * Math.pow(2, reconnectCountRef.current - 1);
    const maxDelay = 30000; // Cap at 30 seconds
    const jitter = Math.random() * 1000; // Add up to 1 second of jitter
    const finalDelay = Math.min(exponentialDelay + jitter, maxDelay);

    console.log(
      `Scheduling reconnect attempt ${
        reconnectCountRef.current
      }/${reconnectAttempts} in ${Math.round(finalDelay)}ms`
    );

    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, finalDelay);
  }, [connect, reconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    console.log("Disconnecting WebSocket");

    // Clear any pending reconnection
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close(1000, "Manual disconnect");
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionError(null);
    reconnectCountRef.current = 0;
  }, []);

  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log("Sending WebSocket message:", message);
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("Cannot send message: WebSocket not connected");
    }
  }, []);

  // Auto-connect on mount with initial delay
  useEffect(() => {
    if (autoConnect) {
      // Add initial delay to let the server fully start up
      const initialTimeout = setTimeout(() => {
        connect();
      }, initialDelay);

      return () => clearTimeout(initialTimeout);
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect, initialDelay]);

  // Ping to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        sendMessage({ type: "ping" });
      }
    }, 30000); // Ping every 30 seconds

    return () => clearInterval(pingInterval);
  }, [isConnected, sendMessage]);

  return {
    isConnected,
    connectionError,
    lastMessage,
    botStatus,
    liveMetrics,
    connect,
    disconnect,
    sendMessage,
  };
};
