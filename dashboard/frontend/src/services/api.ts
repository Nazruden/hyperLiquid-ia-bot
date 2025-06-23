import axios from "axios";
import type { AxiosInstance, AxiosResponse } from "axios";
import type {
  ApiResponse,
  PaginatedResponse,
  Trade,
  Position,
  BotStatus,
  BotModeStatus,
  PerformanceMetrics,
  DashboardMetrics,
  SearchParams,
  CryptoConfig,
  CryptoStatus,
  CryptoBatchUpdate,
  CryptoCompatibility,
} from "../types/trading";

class ApiService {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(
          `API Request: ${config.method?.toUpperCase()} ${config.url}`
        );
        return config;
      },
      (error) => {
        console.error("API Request Error:", error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error(
          "API Response Error:",
          error.response?.data || error.message
        );
        return Promise.reject(error);
      }
    );
  }

  // Health Check
  async healthCheck(): Promise<
    ApiResponse<{ status: string; timestamp: string }>
  > {
    const response = await this.client.get("/health");
    return response.data;
  }

  // Bot Control Endpoints
  async getBotStatus(): Promise<ApiResponse<BotStatus>> {
    const response = await this.client.get("/api/bot/status");
    return response.data;
  }

  async startBot(): Promise<ApiResponse<{ message: string }>> {
    const response = await this.client.post("/api/bot/start");
    return response.data;
  }

  async stopBot(): Promise<ApiResponse<{ message: string }>> {
    const response = await this.client.post("/api/bot/stop");
    return response.data;
  }

  async restartBot(): Promise<ApiResponse<{ message: string }>> {
    const response = await this.client.post("/api/bot-control/restart");
    return response.data;
  }

  async getBotLogs(
    lines: number = 100
  ): Promise<ApiResponse<{ logs: string[] }>> {
    const response = await this.client.get(`/api/bot/logs?lines=${lines}`);
    return response.data;
  }

  async getSystemResources(): Promise<
    ApiResponse<{
      cpu_percent: number;
      memory_percent: number;
      disk_usage: number;
    }>
  > {
    const response = await this.client.get("/api/bot/resources");
    return response.data;
  }

  // Analytics Endpoints
  async getAnalyticsSummary(): Promise<ApiResponse<PerformanceMetrics>> {
    const response = await this.client.get("/api/analytics/summary");
    return response.data;
  }

  async getDailyPnL(days: number = 30): Promise<
    ApiResponse<{
      dates: string[];
      pnl_values: number[];
      cumulative_pnl: number[];
    }>
  > {
    const response = await this.client.get(
      `/api/analytics/daily-pnl?days=${days}`
    );
    return response.data;
  }

  async getPerformanceMetrics(): Promise<
    ApiResponse<{
      win_rate: number;
      profit_factor: number;
      sharpe_ratio: number;
      max_drawdown: number;
      avg_trade_duration: number;
    }>
  > {
    const response = await this.client.get("/api/analytics/performance");
    return response.data;
  }

  async getDashboardMetrics(): Promise<ApiResponse<DashboardMetrics>> {
    const response = await this.client.get("/api/analytics/dashboard-metrics");
    return response.data;
  }

  // Trades Endpoints
  async getTrades(
    params?: SearchParams
  ): Promise<ApiResponse<PaginatedResponse<Trade>>> {
    const queryString = new URLSearchParams();

    if (params?.page) queryString.append("page", params.page.toString());
    if (params?.limit) queryString.append("limit", params.limit.toString());
    if (params?.query) queryString.append("search", params.query);
    if (params?.sort_by) queryString.append("sort_by", params.sort_by);
    if (params?.sort_order) queryString.append("sort_order", params.sort_order);

    // Add filters
    if (params?.filters?.symbol)
      queryString.append("symbol", params.filters.symbol);
    if (params?.filters?.side) queryString.append("side", params.filters.side);
    if (params?.filters?.date_from)
      queryString.append("date_from", params.filters.date_from);
    if (params?.filters?.date_to)
      queryString.append("date_to", params.filters.date_to);
    if (params?.filters?.strategy)
      queryString.append("strategy", params.filters.strategy);

    const url = `/api/trades${
      queryString.toString() ? `?${queryString.toString()}` : ""
    }`;
    const response = await this.client.get(url);
    return response.data;
  }

  async getPositions(): Promise<ApiResponse<Position[]>> {
    const response = await this.client.get("/api/trades/positions");
    return response.data;
  }

  async getTradeStatistics(): Promise<
    ApiResponse<{
      total_trades: number;
      winning_trades: number;
      losing_trades: number;
      total_volume: number;
      avg_trade_size: number;
      largest_win: number;
      largest_loss: number;
    }>
  > {
    const response = await this.client.get("/api/trades/statistics");
    return response.data;
  }

  // Crypto Configuration Endpoints
  async getCryptoStatus(): Promise<ApiResponse<CryptoStatus>> {
    const response = await this.client.get("/api/crypto/status");
    return response.data;
  }

  async getAvailableCryptos(): Promise<
    ApiResponse<{
      total_count: number;
      cryptos: CryptoConfig[];
      last_updated: string;
    }>
  > {
    const response = await this.client.get("/api/crypto/available");
    return response.data;
  }

  async getActiveCryptos(): Promise<
    ApiResponse<{
      total_count: number;
      active_cryptos: Record<string, number>;
    }>
  > {
    const response = await this.client.get("/api/crypto/active");
    return response.data;
  }

  async activateCrypto(symbol: string): Promise<
    ApiResponse<{
      symbol: string;
      topic_id?: number;
      is_active: boolean;
    }>
  > {
    const response = await this.client.post("/api/crypto/activate", {
      symbol,
      topic_id: 0, // Will be determined by backend
    });
    return response.data;
  }

  async deactivateCrypto(symbol: string): Promise<
    ApiResponse<{
      symbol: string;
      is_active: boolean;
    }>
  > {
    const response = await this.client.post("/api/crypto/deactivate", {
      symbol,
    });
    return response.data;
  }

  async batchUpdateCryptos(
    updates: Record<string, boolean>
  ): Promise<ApiResponse<CryptoBatchUpdate>> {
    const response = await this.client.put("/api/crypto/batch-update", {
      updates,
    });
    return response.data;
  }

  async activatePopularCryptos(
    setName: string = "recommended_starter"
  ): Promise<
    ApiResponse<{
      activated: string[];
      errors: string[];
      total_activated: number;
    }>
  > {
    const response = await this.client.post(
      `/api/crypto/quick-actions/activate-popular?set_name=${setName}`
    );
    return response.data;
  }

  async clearAllCryptos(): Promise<
    ApiResponse<{
      deactivated: string[];
      total_deactivated: number;
    }>
  > {
    const response = await this.client.post(
      "/api/crypto/quick-actions/clear-all"
    );
    return response.data;
  }

  async searchCryptos(params: {
    query?: string;
    availability?: string;
    active_only?: boolean;
  }): Promise<
    ApiResponse<{
      total_count: number;
      cryptos: CryptoConfig[];
      filtered_count: number;
    }>
  > {
    const queryString = new URLSearchParams();
    if (params.query) queryString.append("query", params.query);
    if (params.availability)
      queryString.append("availability", params.availability);
    if (params.active_only)
      queryString.append("active_only", params.active_only.toString());

    const url = `/api/crypto/search${
      queryString.toString() ? `?${queryString.toString()}` : ""
    }`;
    const response = await this.client.get(url);
    return response.data;
  }

  async getCompatibilityCheck(): Promise<ApiResponse<CryptoCompatibility>> {
    const response = await this.client.get("/api/crypto/compatibility");
    return response.data;
  }

  // Bot Mode Control Methods (STANDBY/ACTIVE)
  async startMonitoring(): Promise<
    ApiResponse<{ message: string; status: BotModeStatus }>
  > {
    const response = await this.client.post(
      "/api/bot-control/start-monitoring"
    );
    return response.data;
  }

  async setStandbyMode(): Promise<
    ApiResponse<{ message: string; status: BotModeStatus }>
  > {
    const response = await this.client.post("/api/bot-control/set-standby");
    return response.data;
  }

  async getBotModeStatus(): Promise<ApiResponse<BotModeStatus>> {
    const response = await this.client.get("/api/bot-control/mode-status");
    return response.data;
  }

  // Utility Methods
  async testConnection(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch (error) {
      console.error("Connection test failed:", error);
      return false;
    }
  }

  getWebSocketUrl(): string {
    const wsProtocol = this.baseURL.startsWith("https") ? "wss" : "ws";
    const wsUrl = this.baseURL.replace(/^https?/, wsProtocol);
    return `${wsUrl}/ws`;
  }

  // Error handling helper
  handleApiError(error: unknown): string {
    if (axios.isAxiosError(error)) {
      if (error.response?.data?.message) {
        return error.response.data.message;
      }
      if (error.response?.data?.error) {
        return error.response.data.error;
      }
      if (error.response?.status === 404) {
        return "Resource not found";
      }
      if (error.response?.status === 500) {
        return "Internal server error";
      }
      if (error.code === "ECONNREFUSED") {
        return "Cannot connect to server. Please ensure the backend is running.";
      }
    }
    return "An unexpected error occurred";
  }
}

// Create and export a singleton instance
export const apiService = new ApiService();
export default apiService;
