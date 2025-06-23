import React, { useState } from "react";
import {
  Play,
  Square,
  RotateCcw,
  AlertTriangle,
  CheckCircle,
  Clock,
} from "lucide-react";
import { apiService } from "../services/api";
import type { BotStatus as BotStatusType } from "../types/trading";

interface BotStatusProps {
  botStatus: BotStatusType | null;
}

const BotStatus: React.FC<BotStatusProps> = ({ botStatus }) => {
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleBotAction = async (action: "start" | "stop" | "restart") => {
    try {
      setActionLoading(action);
      setError(null);

      let response;
      switch (action) {
        case "start":
          response = await apiService.startBot();
          break;
        case "stop":
          response = await apiService.stopBot();
          break;
        case "restart":
          response = await apiService.restartBot();
          break;
      }

      if (!response.success) {
        setError(response.error || `Failed to ${action} bot`);
      }
    } catch (err) {
      const errorMessage = apiService.handleApiError(err);
      setError(errorMessage);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusIcon = () => {
    switch (botStatus?.status) {
      case "running":
        return <CheckCircle className="w-5 h-5 text-success-500" />;
      case "stopped":
        return <Square className="w-5 h-5 text-gray-500" />;
      case "error":
        return <AlertTriangle className="w-5 h-5 text-danger-500" />;
      case "starting":
      case "stopping":
        return <Clock className="w-5 h-5 text-yellow-500 animate-pulse" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (botStatus?.status) {
      case "running":
        return "text-success-600 bg-success-50 border-success-200";
      case "stopped":
        return "text-gray-600 bg-gray-50 border-gray-200";
      case "error":
        return "text-danger-600 bg-danger-50 border-danger-200";
      case "starting":
      case "stopping":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const isActionDisabled = (action: string) => {
    if (actionLoading) return true;

    switch (action) {
      case "start":
        return (
          botStatus?.status === "running" || botStatus?.status === "starting"
        );
      case "stop":
        return (
          botStatus?.status === "stopped" || botStatus?.status === "stopping"
        );
      case "restart":
        return (
          botStatus?.status === "starting" || botStatus?.status === "stopping"
        );
      default:
        return false;
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center">
          {getStatusIcon()}
          <h2 className="text-xl font-semibold text-gray-900 ml-2">
            Bot Control
          </h2>
        </div>
        <div
          className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor()}`}
        >
          {botStatus?.status?.toUpperCase() || "UNKNOWN"}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-danger-50 border border-danger-200 rounded-md">
          <div className="flex items-center">
            <AlertTriangle className="w-4 h-4 text-danger-500 mr-2" />
            <span className="text-sm text-danger-700">{error}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Bot Controls */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">Controls</h3>
          <div className="flex space-x-2">
            <button
              onClick={() => handleBotAction("start")}
              disabled={isActionDisabled("start")}
              className="btn-success flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {actionLoading === "start" ? (
                <div className="spinner w-4 h-4 mr-2" />
              ) : (
                <Play className="w-4 h-4 mr-2" />
              )}
              Start
            </button>

            <button
              onClick={() => handleBotAction("stop")}
              disabled={isActionDisabled("stop")}
              className="btn-danger flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {actionLoading === "stop" ? (
                <div className="spinner w-4 h-4 mr-2" />
              ) : (
                <Square className="w-4 h-4 mr-2" />
              )}
              Stop
            </button>

            <button
              onClick={() => handleBotAction("restart")}
              disabled={isActionDisabled("restart")}
              className="btn-secondary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {actionLoading === "restart" ? (
                <div className="spinner w-4 h-4 mr-2" />
              ) : (
                <RotateCcw className="w-4 h-4 mr-2" />
              )}
              Restart
            </button>
          </div>
        </div>

        {/* Bot Statistics */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">Statistics</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500">Uptime</p>
              <p className="text-sm font-medium text-gray-900">
                {botStatus?.uptime
                  ? `${Math.floor(botStatus.uptime / 3600)}h ${Math.floor(
                      (botStatus.uptime % 3600) / 60
                    )}m`
                  : "N/A"}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Trades</p>
              <p className="text-sm font-medium text-gray-900">
                {botStatus?.total_trades || 0}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Active Positions</p>
              <p className="text-sm font-medium text-gray-900">
                {botStatus?.active_positions || 0}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Balance</p>
              <p className="text-sm font-medium text-gray-900">
                ${(botStatus?.balance || 0).toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* System Resources */}
      {botStatus?.system_resources && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            System Resources
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-xs text-gray-500">CPU Usage</p>
              <div className="flex items-center mt-1">
                <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full"
                    style={{
                      width: `${botStatus.system_resources.cpu_percent}%`,
                    }}
                  />
                </div>
                <span className="text-xs text-gray-600">
                  {botStatus.system_resources.cpu_percent.toFixed(1)}%
                </span>
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-500">Memory Usage</p>
              <div className="flex items-center mt-1">
                <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full"
                    style={{
                      width: `${botStatus.system_resources.memory_percent}%`,
                    }}
                  />
                </div>
                <span className="text-xs text-gray-600">
                  {botStatus.system_resources.memory_percent.toFixed(1)}%
                </span>
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-500">Disk Usage</p>
              <div className="flex items-center mt-1">
                <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full"
                    style={{
                      width: `${botStatus.system_resources.disk_usage}%`,
                    }}
                  />
                </div>
                <span className="text-xs text-gray-600">
                  {botStatus.system_resources.disk_usage.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Last Trade */}
      {botStatus?.last_trade && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">Last Trade</p>
          <p className="text-sm text-gray-900">
            {new Date(botStatus.last_trade).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
};

export default BotStatus;
