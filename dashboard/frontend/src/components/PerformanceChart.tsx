import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { apiService } from "../services/api";

interface ChartData {
  date: string;
  pnl: number;
  cumulative_pnl: number;
}

const PerformanceChart: React.FC = () => {
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeframe, setTimeframe] = useState<number>(30);

  useEffect(() => {
    loadChartData();
  }, [timeframe]);

  const loadChartData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiService.getDailyPnL(timeframe);
      if (response.success) {
        const formattedData = response.data.dates.map((date, index) => ({
          date: new Date(date).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          }),
          pnl: response.data.pnl_values[index],
          cumulative_pnl: response.data.cumulative_pnl[index],
        }));
        setChartData(formattedData);
      } else {
        setError(response.error || "Failed to load chart data");
      }
    } catch (err) {
      const errorMessage = apiService.handleApiError(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div
              key={index}
              className="flex items-center justify-between space-x-4"
            >
              <div className="flex items-center">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-gray-600">{entry.name}:</span>
              </div>
              <span className="text-sm font-medium text-gray-900">
                {formatCurrency(entry.value)}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner w-8 h-8 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading chart data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">{error}</p>
          <button onClick={loadChartData} className="btn-primary">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (chartData.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center">
        <p className="text-gray-600">No performance data available</p>
      </div>
    );
  }

  return (
    <div>
      {/* Timeframe Selector */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex space-x-2">
          {[7, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setTimeframe(days)}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                timeframe === days
                  ? "bg-primary-100 text-primary-700"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {days}d
            </button>
          ))}
        </div>

        <div className="text-sm text-gray-500">Last {timeframe} days</div>
      </div>

      {/* Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12, fill: "#6b7280" }}
              tickLine={{ stroke: "#e5e7eb" }}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#6b7280" }}
              tickLine={{ stroke: "#e5e7eb" }}
              tickFormatter={formatCurrency}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{
                fontSize: "12px",
                color: "#6b7280",
              }}
            />
            <Line
              type="monotone"
              dataKey="pnl"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: "#3b82f6", strokeWidth: 2, r: 3 }}
              activeDot={{ r: 5, stroke: "#3b82f6", strokeWidth: 2 }}
              name="Daily P&L"
            />
            <Line
              type="monotone"
              dataKey="cumulative_pnl"
              stroke="#10b981"
              strokeWidth={2}
              dot={{ fill: "#10b981", strokeWidth: 2, r: 3 }}
              activeDot={{ r: 5, stroke: "#10b981", strokeWidth: 2 }}
              name="Cumulative P&L"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Chart Summary */}
      <div className="mt-4 grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <p className="text-xs text-gray-500">Total P&L</p>
          <p
            className={`text-lg font-semibold ${
              chartData[chartData.length - 1]?.cumulative_pnl >= 0
                ? "text-success-600"
                : "text-danger-600"
            }`}
          >
            {formatCurrency(
              chartData[chartData.length - 1]?.cumulative_pnl || 0
            )}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">Best Day</p>
          <p className="text-lg font-semibold text-success-600">
            {formatCurrency(Math.max(...chartData.map((d) => d.pnl)))}
          </p>
        </div>
      </div>
    </div>
  );
};

export default PerformanceChart;
