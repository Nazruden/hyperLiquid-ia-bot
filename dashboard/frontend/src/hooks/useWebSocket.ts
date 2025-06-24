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

// Enhanced interface for state sync support
interface BotModeState {
  mode: "STANDBY" | "ACTIVE";
  monitoring_enabled: boolean;
  active_cryptos: Record<string, unknown>;
  crypto_count: number;
  last_updated?: string;
}

interface BotProcessState {
  status: "running" | "stopped" | "starting" | "stopping";
  pid?: number;
  uptime: number;
  external_process?: boolean;
  restart_count?: number;
  last_updated?: string;
}

interface ActivityItem {
  id: string;
  timestamp: string;
  activity_type: string;
  token?: string;
  title: string;
  description: string;
  severity: "SUCCESS" | "INFO" | "WARNING" | "ERROR";
  data?: Record<string, unknown>;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  connectionError: string | null;
  lastMessage: WebSocketMessage | null;
  botStatus: BotStatus | null;
  liveMetrics: LiveMetrics | null;

  // Enhanced state sync support
  botModeState: BotModeState | null;
  botProcessState: BotProcessState | null;
  activityStream: ActivityItem[];

  // Connection methods
  connect: () => void;
  disconnect: () => void;
  sendMessage: (message: Record<string, unknown>) => void;

  // State sync methods
  requestFullStateSync: () => void;
  clearActivityStream: () => void;
  clearCachedState: () => void;

  // Connection stats
  connectionStats: {
    totalMessages: number;
    lastHeartbeat?: string;
    connectionTime?: string;
  };
}

export const useWebSocket = (
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const {
    url = "ws://localhost:8000/ws",
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    initialDelay = 2000,
  } = options;

  // Existing state
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics | null>(null);

  // Enhanced state sync support
  const [botModeState, setBotModeState] = useState<BotModeState | null>(() => {
    // Try to restore from localStorage on initial load
    try {
      const stored = localStorage.getItem("bot-mode-state");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [botProcessState, setBotProcessState] =
    useState<BotProcessState | null>(() => {
      // Try to restore from localStorage on initial load
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
  const initialConnectionAttemptedRef = useRef(false);

  // Health check function to verify server readiness
  const checkServerHealth = useCallback(async (): Promise<boolean> => {
    try {
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

  // Enhanced message handler for state sync
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleWebSocketMessage = useCallback((message: any) => {
    console.log("Received WebSocket message:", message);

    // Update message stats
    setConnectionStats((prev) => ({
      ...prev,
      totalMessages: prev.totalMessages + 1,
    }));

    setLastMessage({
      type: message.type,
      data: message.data,
      timestamp: new Date().toISOString(),
    });

    // Handle different message types
    switch (message.type) {
      case "connection":
        console.log("✅ WebSocket connection acknowledged:", message.status);
        break;

      case "snapshot":
        console.log("📊 Received data snapshot");
        if (message.data?.bot_status) {
          setBotStatus(message.data.bot_status);

          // ✅ FIX: Extract mode data from bot_status and sync to botModeState
          // This ensures validation uses the same data as the display
          const botStatus = message.data.bot_status;
          if (
            botStatus.mode !== undefined ||
            botStatus.active_cryptos !== undefined
          ) {
            setBotModeState({
              mode: botStatus.mode || "STANDBY",
              monitoring_enabled: botStatus.monitoring_enabled || false,
              active_cryptos: botStatus.active_cryptos || {},
              crypto_count:
                botStatus.crypto_count ||
                Object.keys(botStatus.active_cryptos || {}).length,
              last_updated: botStatus.last_updated || new Date().toISOString(),
            });
            console.log("🔄 Synced bot_status to botModeState:", {
              mode: botStatus.mode,
              active_cryptos_count: Object.keys(botStatus.active_cryptos || {})
                .length,
            });
          }
        }
        if (message.data?.metrics) {
          setLiveMetrics(message.data.metrics);
        }
        break;

      // ===== STATE SYNC MESSAGE HANDLERS =====
      case "full_state_sync":
        console.log("🔄 Received full state sync");
        if (message.data?.bot_mode) {
          setBotModeState(message.data.bot_mode);
        }
        if (message.data?.bot_process) {
          setBotProcessState(message.data.bot_process);
        }
        if (message.data?.activity_stream) {
          setActivityStream(message.data.activity_stream);
        }
        break;

      case "state_sync_mode_change":
      case "bot_mode_update":
        console.log("🔄 Bot mode state updated:", message.data);
        setBotModeState(message.data);
        break;

      case "state_sync_process_status":
      case "bot_process_update":
        console.log("🔄 Bot process state updated:", message.data);
        setBotProcessState(message.data);
        break;

      case "state_sync_crypto_config":
      case "crypto_config_update":
        console.log("🔄 Crypto config updated:", message.data);
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
        console.log("🔄 Crypto activation updated:", message.data);
        setBotModeState((prev) =>
          prev
            ? {
                ...prev,
                active_cryptos: message.data.active_cryptos || {},
                last_updated: message.data.timestamp,
              }
            : null
        );
        break;

      case "activity_update":
        console.log("📝 New activity:", message.data);
        if (message.data?.activity) {
          setActivityStream((prev) => {
            const newStream = [...prev, message.data.activity];
            // Keep only last 100 activities
            return newStream.slice(-100);
          });
        }
        break;

      // ===== LEGACY MESSAGE HANDLERS =====
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

      case "heartbeat":
        setConnectionStats((prev) => ({
          ...prev,
          lastHeartbeat: message.timestamp,
        }));
        break;

      case "pong":
        // Handle pong response
        break;

      case "ping":
        // Respond to server ping
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: "pong" }));
        }
        break;

      case "health_check":
        console.log("🏥 Health check from server");
        break;

      case "state_reset":
        console.log("🔄 State reset received");
        setBotModeState(message.data?.bot_mode || null);
        setBotProcessState(message.data?.bot_process || null);
        setActivityStream([]);
        break;

      default:
        console.log("Unknown message type:", message.type);
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
      }, 10000);

      ws.onopen = () => {
        clearTimeout(connectionTimeout);
        console.log("WebSocket connected");
        setIsConnected(true);
        setConnectionError(null);
        reconnectCountRef.current = 0;
        initialConnectionAttemptedRef.current = true;

        // Update connection stats
        setConnectionStats((prev) => ({
          ...prev,
          connectionTime: new Date().toISOString(),
        }));

        // ✅ FIX: Remove automatic sync on connection to prevent message flood
        // State sync will be requested by components only when needed
        console.log("🔌 WebSocket connected - state sync available on demand");
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
          handleWebSocketMessage(message);
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("Error creating WebSocket:", error);
      setConnectionError("Failed to create WebSocket connection");
    }
  }, [url, reconnectAttempts, checkServerHealth, handleWebSocketMessage]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    reconnectCountRef.current += 1;

    // Exponential backoff with jitter
    const baseDelay = reconnectInterval;
    const exponentialDelay =
      baseDelay * Math.pow(2, reconnectCountRef.current - 1);
    const maxDelay = 30000;
    const jitter = Math.random() * 1000;
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

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, "Manual disconnect");
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionError(null);
    reconnectCountRef.current = 0;

    // Clear cached state (useful for debugging sync issues)
    clearCachedState();
  }, []);

  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log("Sending WebSocket message:", message);
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("Cannot send message: WebSocket not connected");
    }
  }, []);

  // Enhanced state sync methods with debouncing
  const lastSyncRef = useRef<number>(0);
  const SYNC_COOLDOWN = 1000; // 1 second cooldown between sync requests

  const requestFullStateSync = useCallback(() => {
    const now = Date.now();
    const timeSinceLastSync = now - lastSyncRef.current;

    if (timeSinceLastSync < SYNC_COOLDOWN) {
      console.log(
        `🔄 Sync request ignored - cooldown active (${
          SYNC_COOLDOWN - timeSinceLastSync
        }ms remaining)`
      );
      return;
    }

    lastSyncRef.current = now;
    console.log("🔄 Sending full state sync request");
    sendMessage({ type: "request_full_state_sync" });
  }, [sendMessage]);

  const clearActivityStream = useCallback(() => {
    setActivityStream([]);
  }, []);

  // Clear cached state (useful for debugging sync issues)
  const clearCachedState = useCallback(() => {
    try {
      localStorage.removeItem("bot-mode-state");
      localStorage.removeItem("bot-process-state");
      setBotModeState(null);
      setBotProcessState(null);
      console.log("🗑️ Cleared cached state");
    } catch (error) {
      console.warn("Failed to clear cached state:", error);
    }
  }, []);

  // Auto-connect on mount with initial delay
  useEffect(() => {
    if (autoConnect) {
      const initialTimeout = setTimeout(() => {
        connect();
      }, initialDelay);

      return () => clearTimeout(initialTimeout);
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect, initialDelay]);

  // Persist critical state to localStorage
  useEffect(() => {
    if (botModeState) {
      try {
        localStorage.setItem("bot-mode-state", JSON.stringify(botModeState));
      } catch (error) {
        console.warn("Failed to persist bot mode state:", error);
      }
    }
  }, [botModeState]);

  useEffect(() => {
    if (botProcessState) {
      try {
        localStorage.setItem(
          "bot-process-state",
          JSON.stringify(botProcessState)
        );
      } catch (error) {
        console.warn("Failed to persist bot process state:", error);
      }
    }
  }, [botProcessState]);

  // Ping to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        sendMessage({ type: "ping" });
      }
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [isConnected, sendMessage]);

  return {
    isConnected,
    connectionError,
    lastMessage,
    botStatus,
    liveMetrics,

    // Enhanced state sync support
    botModeState,
    botProcessState,
    activityStream,

    // Connection methods
    connect,
    disconnect,
    sendMessage,

    // State sync methods
    requestFullStateSync,
    clearActivityStream,
    clearCachedState,

    // Connection stats
    connectionStats,
  };
};
