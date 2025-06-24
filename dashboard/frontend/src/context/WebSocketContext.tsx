import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  useCallback,
  type ReactNode,
} from "react";
import type {
  WebSocketMessage,
  BotStatus,
  LiveMetrics,
  BotModeState,
  BotProcessState,
  ActivityItem,
  UseWebSocketReturn,
} from "../types/trading";

// We no longer need to import anything from the old hook
// import {
//   BotModeState,
//   BotProcessState,
//   ActivityItem,
//   UseWebSocketReturn,
// } from "../hooks/useWebSocket"; // We'll move the hook's logic here

export const WebSocketContext = createContext<UseWebSocketReturn | undefined>(
  undefined
);

interface WebSocketProviderProps {
  children: ReactNode;
  url?: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
  url = "ws://localhost:8000/ws",
  autoConnect = true,
  reconnectAttempts = 5,
  reconnectInterval = 3000,
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics | null>(null);
  const [botModeState, setBotModeState] = useState<BotModeState | null>(() => {
    try {
      const stored = localStorage.getItem("bot-mode-state");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [botProcessState, setBotProcessState] =
    useState<BotProcessState | null>(() => {
      try {
        const stored = localStorage.getItem("bot-process-state");
        return stored ? JSON.parse(stored) : null;
      } catch {
        return null;
      }
    });
  const [activityStream, setActivityStream] = useState<ActivityItem[]>([]);
  const [connectionStats, setConnectionStats] = useState({
    totalMessages: 0,
    lastHeartbeat: undefined as string | undefined,
    connectionTime: undefined as string | undefined,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleWebSocketMessage = useCallback((event: MessageEvent) => {
    const message = JSON.parse(event.data);
    console.log("Received WebSocket message:", message);

    setConnectionStats((prev) => ({
      ...prev,
      totalMessages: prev.totalMessages + 1,
    }));
    setLastMessage({
      type: message.type,
      data: message.data,
      timestamp: new Date().toISOString(),
    });

    switch (message.type) {
      case "connection":
        console.log("✅ WebSocket connection acknowledged:", message.status);
        break;
      case "snapshot":
        console.log("📊 Received data snapshot");
        if (message.data?.bot_status) {
          setBotStatus(message.data.bot_status);
          const {
            mode,
            monitoring_enabled,
            active_cryptos,
            crypto_count,
            last_updated,
          } = message.data.bot_status;
          setBotModeState({
            mode: mode || "STANDBY",
            monitoring_enabled: monitoring_enabled || false,
            active_cryptos: active_cryptos || {},
            crypto_count:
              crypto_count || Object.keys(active_cryptos || {}).length,
            last_updated: last_updated || new Date().toISOString(),
          });
        }
        if (message.data?.metrics) setLiveMetrics(message.data.metrics);
        break;
      case "full_state_sync":
        if (message.data?.bot_mode) setBotModeState(message.data.bot_mode);
        if (message.data?.bot_process)
          setBotProcessState(message.data.bot_process);
        if (message.data?.activity_stream)
          setActivityStream(message.data.activity_stream);
        break;
      case "bot_mode_update":
        setBotModeState(message.data);
        break;
      case "bot_process_update":
        setBotProcessState(message.data);
        break;
      case "crypto_config_update":
        setBotModeState((prev) =>
          prev
            ? {
                ...prev,
                active_cryptos: message.data.active_cryptos || {},
                crypto_count: message.data.crypto_count || 0,
                last_updated: message.data.timestamp,
              }
            : null
        );
        break;
      case "crypto_activation_update":
        setBotModeState((prev) =>
          prev
            ? { ...prev, active_cryptos: message.data.active_cryptos || {} }
            : null
        );
        break;
      case "activity_update":
        setActivityStream((prev) =>
          [message.data.activity, ...prev].slice(0, 100)
        );
        break;
      case "heartbeat":
        setConnectionStats((prev) => ({
          ...prev,
          lastHeartbeat: message.timestamp,
        }));
        break;
      case "pong":
        break;
      default:
        console.warn("Unhandled WebSocket message type:", message.type);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current || reconnectCountRef.current >= reconnectAttempts) return;

    disconnect(); // Ensure any existing connection is closed

    try {
      const socket = new WebSocket(url);
      wsRef.current = socket;

      socket.onopen = () => {
        console.log("WebSocket connected");
        setIsConnected(true);
        setConnectionError(null);
        reconnectCountRef.current = 0;
        setConnectionStats((prev) => ({
          ...prev,
          connectionTime: new Date().toISOString(),
        }));
      };

      socket.onmessage = handleWebSocketMessage;

      socket.onerror = (error) => {
        console.error("WebSocket error:", error);
        setConnectionError("WebSocket connection failed.");
      };

      socket.onclose = () => {
        console.log("WebSocket disconnected");
        setIsConnected(false);
        wsRef.current = null;
        if (reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current++;
          reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
        } else {
          setConnectionError("Connection failed after multiple retries.");
        }
      };
    } catch (error) {
      console.error("WebSocket instantiation error:", error);
      setConnectionError("Failed to create WebSocket connection.");
    }
  }, [
    url,
    reconnectAttempts,
    reconnectInterval,
    handleWebSocketMessage,
    disconnect,
  ]);

  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.error("WebSocket not connected. Cannot send message.");
    }
  }, []);

  const requestFullStateSync = useCallback(() => {
    sendMessage({ type: "request_full_state_sync" });
  }, [sendMessage]);

  const clearActivityStream = () => setActivityStream([]);

  const clearCachedState = useCallback(() => {
    localStorage.removeItem("bot-mode-state");
    localStorage.removeItem("bot-process-state");
    setBotModeState(null);
    setBotProcessState(null);
  }, []);

  useEffect(() => {
    if (autoConnect) {
      // Use a small delay on initial connect to allow UI to settle
      const timeoutId = setTimeout(() => connect(), 500);
      return () => clearTimeout(timeoutId);
    }
  }, [autoConnect, connect]);

  useEffect(() => {
    return () => disconnect();
  }, [disconnect]);

  useEffect(() => {
    if (botModeState)
      localStorage.setItem("bot-mode-state", JSON.stringify(botModeState));
    if (botProcessState)
      localStorage.setItem(
        "bot-process-state",
        JSON.stringify(botProcessState)
      );
  }, [botModeState, botProcessState]);

  const value: UseWebSocketReturn = {
    isConnected,
    connectionError,
    lastMessage,
    botStatus,
    liveMetrics,
    botModeState,
    botProcessState,
    activityStream,
    connectionStats,
    connect,
    disconnect,
    sendMessage,
    requestFullStateSync,
    clearActivityStream,
    clearCachedState,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

// Custom hook to use the WebSocket context
export const useWebSocket = (): UseWebSocketReturn => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return context;
};
