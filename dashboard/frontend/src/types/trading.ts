// Trading Data Types
export interface Trade {
  id: string;
  symbol: string;
  side: "buy" | "sell";
  price: number;
  quantity: number;
  timestamp: string;
  pnl?: number;
  status: "pending" | "filled" | "cancelled";
  strategy?: string;
  ai_prediction?: number;
  confidence?: number;
}

export interface Position {
  symbol: string;
  side: "long" | "short";
  size: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  realized_pnl: number;
  timestamp: string;
}

export interface BotStatus {
  status: "running" | "stopped" | "error" | "starting" | "stopping";
  uptime: number;
  last_trade: string | null;
  total_trades: number;
  active_positions: number;
  balance: number;
  errors: string[];
  pid?: number;
  system_resources: {
    cpu_percent: number;
    memory_percent: number;
    disk_usage: number;
  };
}

export interface BotModeStatus {
  mode: "STANDBY" | "ACTIVE";
  monitoring_enabled: boolean;
  active_cryptos: Record<string, number>;
  status: string;
}

export interface PerformanceMetrics {
  total_pnl: number;
  daily_pnl: number;
  win_rate: number;
  total_trades: number;
  avg_trade_duration: number;
  sharpe_ratio: number;
  max_drawdown: number;
  prediction_accuracy: number;
}

export interface DashboardMetrics {
  balance: number;
  positions_count: number;
  daily_pnl: number;
  daily_pnl_percentage: number;
  prediction_accuracy: number;
  total_trades_today: number;
  active_strategies: string[];
  last_update: string;
}

export interface AIInsight {
  type: "prediction" | "analysis" | "recommendation";
  symbol: string;
  message: string;
  confidence: number;
  timestamp: string;
  source: "allora" | "hyperbolic" | "openrouter";
}

export interface Alert {
  id: string;
  type: "info" | "warning" | "error" | "success";
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type:
    | "bot_status"
    | "live_metrics"
    | "new_trade"
    | "position_update"
    | "ai_insight"
    | "alert";
  data: BotStatus | LiveMetrics | Trade | Position | AIInsight | Alert;
  timestamp: string;
}

export interface LiveMetrics {
  balance: number;
  positions: number;
  pnl_24h: number;
  accuracy: number;
  active_trades: number;
  system_status: "healthy" | "warning" | "error";
}

// Chart Data Types
export interface ChartDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

export interface PerformanceChartData {
  pnl: ChartDataPoint[];
  accuracy: ChartDataPoint[];
  trades: ChartDataPoint[];
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

// Filter and Search Types
export interface TradeFilters {
  symbol?: string;
  side?: "buy" | "sell";
  date_from?: string;
  date_to?: string;
  min_pnl?: number;
  max_pnl?: number;
  strategy?: string;
}

export interface SearchParams {
  query?: string;
  filters?: TradeFilters;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  page?: number;
  limit?: number;
}

// Configuration Types
export interface DashboardConfig {
  refresh_interval: number;
  chart_timeframe: "1h" | "4h" | "1d" | "1w";
  notifications_enabled: boolean;
  theme: "light" | "dark";
  auto_refresh: boolean;
}

// Crypto Configuration Types
export interface CryptoConfig {
  symbol: string;
  topic_id: number | null;
  is_active: boolean;
  availability: "both" | "hyperliquid" | "allora";
  hyperliquid_available: boolean;
  allora_available: boolean;
  last_price?: number;
  volume_24h?: number;
  updated_at?: string;
}

export interface CryptoStatus {
  total_available: number;
  total_active: number;
  availability_breakdown: {
    both: number;
    hyperliquid_only: number;
    allora_only: number;
  };
  cryptos: CryptoConfig[];
  last_updated: string;
}

export interface CryptoBatchUpdate {
  activated: string[];
  deactivated: string[];
  errors: string[];
  total_updated: number;
}

export interface CryptoCompatibility {
  hyperliquid_tokens: number;
  allora_topics: number;
  compatible_cryptos: number;
  compatibility_percentage: number;
}

// Error Types
export interface ErrorInfo {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
}
