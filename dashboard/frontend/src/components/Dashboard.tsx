import React, { useState, useEffect } from "react";
import {
  Activity,
  TrendingUp,
  DollarSign,
  Bot,
  AlertCircle,
  Settings,
  BarChart3,
  History,
} from "lucide-react";
import { useWebSocket } from "../hooks/useWebSocket";
import { apiService } from "../services/api";
import type { DashboardMetrics } from "../types/trading";
import BotStatus from "./BotStatus";
import LiveMetrics from "./LiveMetrics";
import TradeHistory from "./TradeHistory";
import PerformanceChart from "./PerformanceChart";
import ThemeToggle from "./ThemeToggle";
import CryptoManager from "./CryptoManager";

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardMetrics | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<
    "overview" | "crypto" | "analytics"
  >("overview");
  const [activeCryptos, setActiveCryptos] = useState<string[]>([]);

  const { isConnected, connectionError, botStatus, liveMetrics } = useWebSocket(
    {
      url: "ws://localhost:8000/ws",
      autoConnect: true,
    }
  );

  // Load initial dashboard data
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await apiService.getDashboardMetrics();
        if (response.success) {
          setDashboardData(response.data);
        } else {
          setError(response.error || "Failed to load dashboard data");
        }
      } catch (err) {
        const errorMessage = apiService.handleApiError(err);
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-dark-bg flex items-center justify-center">
        <div className="text-center">
          <div className="spinner w-8 h-8 mx-auto mb-4"></div>
          <p className="text-secondary">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-dark-bg flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl heading mb-2">Error Loading Dashboard</h2>
          <p className="text-secondary mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg">
      {/* Header */}
      <header className="bg-white dark:bg-dark-surface shadow-xs border-b border-gray-200 dark:border-dark-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <Bot className="w-8 h-8 text-primary-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-primary">
                  HyperLiquid AI Trading Bot
                </h1>
                {activeCryptos.length > 0 && (
                  <p className="text-sm text-secondary">
                    Monitoring {activeCryptos.length} cryptocurrencies
                  </p>
                )}
              </div>
            </div>

            {/* Connection Status & Theme Toggle */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div
                  className={`status-dot ${
                    isConnected ? "online" : "offline"
                  } mr-2`}
                ></div>
                <span className="text-sm text-secondary">
                  {isConnected ? "Connected" : "Disconnected"}
                </span>
              </div>
              {connectionError && (
                <div className="text-sm text-red-600">{connectionError}</div>
              )}
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 dark:border-dark-border mb-8">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab("overview")}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === "overview"
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <BarChart3 className="w-4 h-4 inline mr-2" />
              Overview
            </button>
            <button
              onClick={() => setActiveTab("crypto")}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === "crypto"
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <Settings className="w-4 h-4 inline mr-2" />
              Crypto Configuration
            </button>
            <button
              onClick={() => setActiveTab("analytics")}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === "analytics"
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <History className="w-4 h-4 inline mr-2" />
              Analytics
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === "overview" && (
          <>
            {/* Bot Status Section */}
            <div className="mb-8">
              <BotStatus botStatus={botStatus} />
            </div>

            {/* Live Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <LiveMetrics
                title="Account Balance"
                value={liveMetrics?.balance || dashboardData?.balance || 0}
                format="currency"
                icon={DollarSign}
                change={dashboardData?.daily_pnl_percentage}
              />

              <LiveMetrics
                title="Active Positions"
                value={
                  liveMetrics?.positions || dashboardData?.positions_count || 0
                }
                format="number"
                icon={TrendingUp}
              />

              <LiveMetrics
                title="24h P&L"
                value={liveMetrics?.pnl_24h || dashboardData?.daily_pnl || 0}
                format="currency"
                icon={Activity}
                change={dashboardData?.daily_pnl_percentage}
                showChangeColor={true}
              />

              <LiveMetrics
                title="AI Accuracy"
                value={
                  liveMetrics?.accuracy ||
                  dashboardData?.prediction_accuracy ||
                  0
                }
                format="percentage"
                icon={Bot}
              />
            </div>

            {/* Charts and Tables Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Performance Chart */}
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg heading">Performance Chart</h3>
                </div>
                <PerformanceChart />
              </div>

              {/* Recent Trades */}
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg heading">Recent Trades</h3>
                </div>
                <TradeHistory limit={10} />
              </div>
            </div>

            {/* AI Insights Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* System Status */}
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg heading">System Status</h3>
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm label">Bot Status</span>
                    <span
                      className={`text-sm font-medium ${
                        botStatus?.status === "running"
                          ? "text-success-600"
                          : "text-danger-600"
                      }`}
                    >
                      {botStatus?.status || "Unknown"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm label">Uptime</span>
                    <span className="text-sm font-medium text-primary">
                      {botStatus?.uptime
                        ? `${Math.floor(botStatus.uptime / 3600)}h ${Math.floor(
                            (botStatus.uptime % 3600) / 60
                          )}m`
                        : "N/A"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-dark-text-secondary">
                      Total Trades
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                      {botStatus?.total_trades || 0}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-dark-text-secondary">
                      System Health
                    </span>
                    <span
                      className={`text-sm font-medium ${
                        liveMetrics?.system_status === "healthy"
                          ? "text-success-600"
                          : liveMetrics?.system_status === "warning"
                          ? "text-yellow-600"
                          : "text-danger-600"
                      }`}
                    >
                      {liveMetrics?.system_status || "Unknown"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Performance Summary */}
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text-primary">
                    Today's Summary
                  </h3>
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-dark-text-secondary">
                      Trades Today
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-dark-text-primary">
                      {dashboardData?.total_trades_today || 0}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-dark-text-secondary">
                      P&L Today
                    </span>
                    <span
                      className={`text-sm font-medium ${
                        (dashboardData?.daily_pnl || 0) >= 0
                          ? "text-success-600"
                          : "text-danger-600"
                      }`}
                    >
                      ${(dashboardData?.daily_pnl || 0).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">
                      Active Strategies
                    </span>
                    <span className="text-sm font-medium text-gray-900">
                      {dashboardData?.active_strategies?.length || 0}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Last Update</span>
                    <span className="text-sm text-gray-500">
                      {dashboardData?.last_update
                        ? new Date(
                            dashboardData.last_update
                          ).toLocaleTimeString()
                        : "N/A"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text-primary">
                    Quick Actions
                  </h3>
                </div>
                <div className="space-y-3">
                  <button className="w-full btn-primary">
                    View Full Trade History
                  </button>
                  <button className="w-full btn-secondary">
                    Download Performance Report
                  </button>
                  <button className="w-full btn-secondary">
                    Configure Strategies
                  </button>
                  <button className="w-full btn-secondary">
                    System Diagnostics
                  </button>
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === "crypto" && (
          <CryptoManager onCryptoUpdate={setActiveCryptos} />
        )}

        {activeTab === "analytics" && (
          <div className="space-y-8">
            <h2 className="text-2xl font-bold text-primary mb-4">
              Detailed Analytics
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg heading">
                    Advanced Performance Chart
                  </h3>
                </div>
                <PerformanceChart />
              </div>
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg heading">Complete Trade History</h3>
                </div>
                <TradeHistory />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
