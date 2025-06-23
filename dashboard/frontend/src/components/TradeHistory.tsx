import React, { useState, useEffect } from "react";
import { ArrowUpRight, ArrowDownRight, Clock, AlertCircle } from "lucide-react";
import { apiService } from "../services/api";
import type { Trade } from "../types/trading";

interface TradeHistoryProps {
  limit?: number;
  showPagination?: boolean;
}

const TradeHistory: React.FC<TradeHistoryProps> = ({
  limit = 10,
  showPagination = false,
}) => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    loadTrades();
  }, [currentPage, limit]);

  const loadTrades = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiService.getTrades({
        page: currentPage,
        limit,
        sort_by: "timestamp",
        sort_order: "desc",
      });

      if (response.success && response.data) {
        // Ensure we always have an array, even if response.data.data is undefined/null
        const tradesData = Array.isArray(response.data.data)
          ? response.data.data
          : [];
        setTrades(tradesData);
        setTotalPages(Math.ceil((response.data.total || 0) / limit));
      } else {
        // Set empty array on failure to prevent undefined errors
        setTrades([]);
        setError(response.error || "Failed to load trades");
      }
    } catch (err) {
      // Set empty array on exception to prevent undefined errors
      setTrades([]);
      const errorMessage = apiService.handleApiError(err);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getTradeIcon = (side: string) => {
    return side === "buy" ? (
      <ArrowUpRight className="w-4 h-4 text-success-500" />
    ) : (
      <ArrowDownRight className="w-4 h-4 text-danger-500" />
    );
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case "filled":
        return "text-success-600 bg-success-50";
      case "pending":
        return "text-yellow-600 bg-yellow-50";
      case "cancelled":
        return "text-gray-600 bg-gray-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getPnLColor = (pnl?: number): string => {
    if (pnl === undefined) return "text-gray-500";
    return pnl >= 0 ? "text-success-600" : "text-danger-600";
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: limit }).map((_, index) => (
          <div key={index} className="animate-pulse">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                <div>
                  <div className="w-20 h-4 bg-gray-200 rounded-sm mb-1"></div>
                  <div className="w-16 h-3 bg-gray-200 rounded-sm"></div>
                </div>
              </div>
              <div className="text-right">
                <div className="w-16 h-4 bg-gray-200 rounded-sm mb-1"></div>
                <div className="w-12 h-3 bg-gray-200 rounded-sm"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600 mb-4">{error}</p>
        <button onClick={loadTrades} className="btn-primary">
          Retry
        </button>
      </div>
    );
  }

  // Ensure trades is always an array
  const safeTrades = Array.isArray(trades) ? trades : [];

  if (safeTrades.length === 0) {
    return (
      <div className="text-center py-8">
        <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No trades found</p>
      </div>
    );
  }

  return (
    <div>
      <div className="space-y-2">
        {safeTrades.map((trade) => (
          <div
            key={trade.id}
            className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors duration-200"
          >
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-8 h-8 bg-white rounded-full shadow-xs">
                {getTradeIcon(trade.side)}
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-gray-900">
                    {trade.symbol}
                  </span>
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                      trade.status
                    )}`}
                  >
                    {trade.status}
                  </span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <span className="capitalize">{trade.side}</span>
                  <span>•</span>
                  <span>{formatTimestamp(trade.timestamp)}</span>
                  {trade.strategy && (
                    <>
                      <span>•</span>
                      <span>{trade.strategy}</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="text-right">
              <div className="font-medium text-gray-900">
                ${trade.price.toFixed(4)}
              </div>
              <div className="flex items-center space-x-2 text-sm">
                <span className="text-gray-500">
                  {trade.quantity.toFixed(4)}
                </span>
                {trade.pnl !== undefined && (
                  <span className={`font-medium ${getPnLColor(trade.pnl)}`}>
                    {trade.pnl >= 0 ? "+" : ""}${trade.pnl.toFixed(2)}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {showPagination && totalPages > 1 && (
        <div className="flex items-center justify-between mt-6">
          <div className="text-sm text-gray-500">
            Showing {safeTrades.length} of {totalPages * limit} trades
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="flex items-center px-3 py-2 text-sm text-gray-700">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() =>
                setCurrentPage((prev) => Math.min(prev + 1, totalPages))
              }
              disabled={currentPage === totalPages}
              className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TradeHistory;
