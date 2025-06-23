import React from "react";
import type { LucideIcon } from "lucide-react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface LiveMetricsProps {
  title: string;
  value: number;
  format: "currency" | "number" | "percentage";
  icon: LucideIcon;
  change?: number;
  showChangeColor?: boolean;
  loading?: boolean;
}

const LiveMetrics: React.FC<LiveMetricsProps> = ({
  title,
  value,
  format,
  icon: Icon,
  change,
  showChangeColor = false,
  loading = false,
}) => {
  const formatValue = (val: number, fmt: string): string => {
    switch (fmt) {
      case "currency":
        return new Intl.NumberFormat("en-US", {
          style: "currency",
          currency: "USD",
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }).format(val);
      case "percentage":
        return `${val.toFixed(2)}%`;
      case "number":
        return new Intl.NumberFormat("en-US").format(val);
      default:
        return val.toString();
    }
  };

  const getChangeColor = (changeValue: number): string => {
    if (!showChangeColor) return "text-gray-600";
    return changeValue >= 0 ? "text-success-600" : "text-danger-600";
  };

  const getChangeIcon = (changeValue: number) => {
    if (!showChangeColor || changeValue === 0) return null;
    return changeValue >= 0 ? (
      <TrendingUp className="w-3 h-3" />
    ) : (
      <TrendingDown className="w-3 h-3" />
    );
  };

  return (
    <div className="metric-card animate-fade-in relative">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className="p-2 bg-primary-100 rounded-lg">
            <Icon className="w-5 h-5 text-primary-600" />
          </div>
        </div>
        {loading && <div className="spinner w-4 h-4" />}
      </div>

      <div className="mt-4">
        <div className="flex items-baseline justify-between">
          <div>
            <p className="metric-value">
              {loading ? (
                <div className="animate-pulse bg-gray-200 h-8 w-24 rounded-sm"></div>
              ) : (
                formatValue(value, format)
              )}
            </p>
            <p className="metric-label mt-1">{title}</p>
          </div>

          {change !== undefined && !loading && (
            <div
              className={`flex items-center metric-change ${getChangeColor(
                change
              )}`}
            >
              {getChangeIcon(change)}
              <span className="ml-1">
                {change >= 0 ? "+" : ""}
                {change.toFixed(2)}%
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Optional pulse animation for live updates */}
      <div className="absolute inset-0 rounded-lg border-2 border-transparent animate-pulse-slow opacity-0 hover:opacity-20 hover:border-primary-300 transition-opacity duration-300"></div>
    </div>
  );
};

export default LiveMetrics;
