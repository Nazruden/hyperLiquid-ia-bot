import { useContext } from "react";
// The context will be created in a separate file.
// For now, let's assume it exists and is imported.
import { WebSocketContext } from "../context/WebSocketContext";
import type { UseWebSocketReturn } from "../types/trading";

// The hook is now just a simple consumer of the context.
export const useWebSocket = (): UseWebSocketReturn => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return context;
};
