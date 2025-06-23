import { useState, useEffect, useRef, useCallback } from "react";
import { io, Socket } from "socket.io-client";
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
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics | null>(null);

  const socketRef = useRef<Socket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (socketRef.current?.connected) {
      console.log("WebSocket already connected");
      return;
    }

    console.log("Connecting to WebSocket:", url);
    setConnectionError(null);

    // Create socket connection
    const socket = io(url, {
      transports: ["websocket", "polling"],
      timeout: 10000,
      reconnection: false, // We'll handle reconnection manually
    });

    socket.on("connect", () => {
      console.log("WebSocket connected");
      setIsConnected(true);
      setConnectionError(null);
      reconnectCountRef.current = 0;
    });

    socket.on("disconnect", (reason) => {
      console.log("WebSocket disconnected:", reason);
      setIsConnected(false);

      // Attempt reconnection if not manually disconnected
      if (
        reason !== "io client disconnect" &&
        reconnectCountRef.current < reconnectAttempts
      ) {
        scheduleReconnect();
      }
    });

    socket.on("connect_error", (error) => {
      console.error("WebSocket connection error:", error);
      setConnectionError(error.message);
      setIsConnected(false);

      // Attempt reconnection
      if (reconnectCountRef.current < reconnectAttempts) {
        scheduleReconnect();
      } else {
        setConnectionError(
          `Failed to connect after ${reconnectAttempts} attempts`
        );
      }
    });

    // Handle different message types
    socket.on("bot_status", (data: BotStatus) => {
      console.log("Received bot status:", data);
      setBotStatus(data);
      setLastMessage({
        type: "bot_status",
        data,
        timestamp: new Date().toISOString(),
      });
    });

    socket.on("live_metrics", (data: LiveMetrics) => {
      console.log("Received live metrics:", data);
      setLiveMetrics(data);
      setLastMessage({
        type: "live_metrics",
        data,
        timestamp: new Date().toISOString(),
      });
    });

    socket.on("new_trade", (data) => {
      console.log("Received new trade:", data);
      setLastMessage({
        type: "new_trade",
        data,
        timestamp: new Date().toISOString(),
      });
    });

    socket.on("position_update", (data) => {
      console.log("Received position update:", data);
      setLastMessage({
        type: "position_update",
        data,
        timestamp: new Date().toISOString(),
      });
    });

    socket.on("ai_insight", (data) => {
      console.log("Received AI insight:", data);
      setLastMessage({
        type: "ai_insight",
        data,
        timestamp: new Date().toISOString(),
      });
    });

    socket.on("alert", (data) => {
      console.log("Received alert:", data);
      setLastMessage({
        type: "alert",
        data,
        timestamp: new Date().toISOString(),
      });
    });

    socketRef.current = socket;
  }, [url, reconnectAttempts]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    reconnectCountRef.current += 1;
    console.log(
      `Scheduling reconnect attempt ${reconnectCountRef.current}/${reconnectAttempts} in ${reconnectInterval}ms`
    );

    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, reconnectInterval);
  }, [connect, reconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    console.log("Disconnecting WebSocket");

    // Clear any pending reconnection
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Disconnect socket
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }

    setIsConnected(false);
    setConnectionError(null);
    reconnectCountRef.current = 0;
  }, []);

  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (socketRef.current?.connected) {
      console.log("Sending WebSocket message:", message);
      socketRef.current.emit("message", message);
    } else {
      console.warn("Cannot send message: WebSocket not connected");
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

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
