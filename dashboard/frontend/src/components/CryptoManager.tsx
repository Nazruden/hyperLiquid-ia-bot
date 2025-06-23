import React, { useState, useEffect } from "react";
import {
  Search,
  Filter,
  Settings,
  CheckCircle,
  Circle,
  Loader,
  AlertCircle,
  TrendingUp,
} from "lucide-react";
import { apiService } from "../services/api";

interface CryptoConfig {
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

interface CryptoManagerProps {
  onCryptoUpdate?: (activeCryptos: string[]) => void;
}

const CryptoManager: React.FC<CryptoManagerProps> = ({ onCryptoUpdate }) => {
  const [availableCryptos, setAvailableCryptos] = useState<CryptoConfig[]>([]);
  const [filteredCryptos, setFilteredCryptos] = useState<CryptoConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterBy, setFilterBy] = useState<
    "all" | "both" | "hyperliquid" | "allora" | "active"
  >("all");
  const [updatingCrypto, setUpdatingCrypto] = useState<string | null>(null);

  // Load available cryptocurrencies
  const loadCryptos = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiService.getCryptoStatus();
      if (response.success) {
        const cryptos = response.data.cryptos || [];
        setAvailableCryptos(cryptos);
        setFilteredCryptos(cryptos);

        // Notify parent of active cryptos
        const activeCryptos = cryptos
          .filter((c: CryptoConfig) => c.is_active)
          .map((c: CryptoConfig) => c.symbol);
        onCryptoUpdate?.(activeCryptos);
      } else {
        setError(response.error || "Failed to load cryptocurrencies");
      }
    } catch (err) {
      setError("Error loading cryptocurrencies");
      console.error("Error loading cryptos:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCryptos();
  }, []);

  // Filter and search cryptos
  useEffect(() => {
    let filtered = availableCryptos;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter((crypto) =>
        crypto.symbol.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply availability filter
    if (filterBy !== "all") {
      if (filterBy === "active") {
        filtered = filtered.filter((crypto) => crypto.is_active);
      } else {
        filtered = filtered.filter(
          (crypto) => crypto.availability === filterBy
        );
      }
    }

    // Sort by active first, then alphabetically
    filtered.sort((a, b) => {
      if (a.is_active !== b.is_active) {
        return a.is_active ? -1 : 1;
      }
      return a.symbol.localeCompare(b.symbol);
    });

    setFilteredCryptos(filtered);
  }, [availableCryptos, searchTerm, filterBy]);

  // Toggle crypto activation
  const handleToggleCrypto = async (symbol: string, activate: boolean) => {
    try {
      setUpdatingCrypto(symbol);

      const response = activate
        ? await apiService.activateCrypto(symbol)
        : await apiService.deactivateCrypto(symbol);

      if (response.success) {
        // Update local state
        setAvailableCryptos((prev) =>
          prev.map((crypto) =>
            crypto.symbol === symbol
              ? { ...crypto, is_active: activate }
              : crypto
          )
        );

        // Update parent component
        const updatedActiveCryptos = availableCryptos
          .map((crypto) =>
            crypto.symbol === symbol
              ? { ...crypto, is_active: activate }
              : crypto
          )
          .filter((crypto) => crypto.is_active)
          .map((crypto) => crypto.symbol);
        onCryptoUpdate?.(updatedActiveCryptos);

        console.log(
          `${symbol} ${activate ? "activated" : "deactivated"} successfully`
        );
      } else {
        setError(
          response.error ||
            `Failed to ${activate ? "activate" : "deactivate"} ${symbol}`
        );
      }
    } catch (err) {
      setError(`Error ${activate ? "activating" : "deactivating"} ${symbol}`);
      console.error("Toggle error:", err);
    } finally {
      setUpdatingCrypto(null);
    }
  };

  // Quick actions
  const handleActivatePopular = async () => {
    try {
      setLoading(true);
      const response = await apiService.activatePopularCryptos(
        "recommended_starter"
      );
      if (response.success) {
        await loadCryptos(); // Reload to get updated state
      } else {
        setError(
          response.error || "Failed to activate popular cryptocurrencies"
        );
      }
    } catch (err) {
      setError("Error activating popular cryptocurrencies");
      console.error("Activate popular error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearAll = async () => {
    try {
      setLoading(true);
      const response = await apiService.clearAllCryptos();
      if (response.success) {
        await loadCryptos(); // Reload to get updated state
      } else {
        setError(response.error || "Failed to clear all cryptocurrencies");
      }
    } catch (err) {
      setError("Error clearing all cryptocurrencies");
      console.error("Clear all error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Get availability badge
  const getAvailabilityBadge = (availability: string) => {
    const badges = {
      both: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
      hyperliquid:
        "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
      allora:
        "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
    };

    const labels = {
      both: "Both",
      hyperliquid: "HyperLiquid",
      allora: "Allora",
    };

    return (
      <span
        className={`px-2 py-1 rounded text-xs font-medium ${
          badges[availability as keyof typeof badges]
        }`}
      >
        {labels[availability as keyof typeof labels]}
      </span>
    );
  };

  // Format price
  const formatPrice = (price?: number) => {
    if (!price) return "N/A";
    return `$${price.toLocaleString()}`;
  };

  // Format volume
  const formatVolume = (volume?: number) => {
    if (!volume) return "N/A";
    if (volume >= 1e9) return `$${(volume / 1e9).toFixed(1)}B`;
    if (volume >= 1e6) return `$${(volume / 1e6).toFixed(1)}M`;
    if (volume >= 1e3) return `$${(volume / 1e3).toFixed(1)}K`;
    return `$${volume.toFixed(0)}`;
  };

  const activeCryptos = availableCryptos.filter((crypto) => crypto.is_active);

  if (loading && availableCryptos.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <Loader className="w-8 h-8 animate-spin mx-auto mb-4 text-primary-600" />
          <p className="text-secondary">Loading cryptocurrencies...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-primary mb-2">
            Crypto Configuration
          </h2>
          <p className="text-secondary">
            Manage which cryptocurrencies to monitor for trading signals
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <span className="text-sm text-secondary">
            Active: {activeCryptos.length} / {availableCryptos.length}
          </span>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/50 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex">
            <AlertCircle className="w-5 h-5 text-red-400 mr-3 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                Error
              </h3>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                {error}
              </p>
              <button
                onClick={loadCryptos}
                className="text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 mt-2"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search cryptocurrencies..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-white dark:bg-dark-surface text-primary placeholder-gray-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <div className="relative">
          <select
            value={filterBy}
            onChange={(e) =>
              setFilterBy(
                e.target.value as
                  | "all"
                  | "both"
                  | "hyperliquid"
                  | "allora"
                  | "active"
              )
            }
            className="pl-4 pr-10 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-white dark:bg-dark-surface text-primary focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option value="all">All Platforms</option>
            <option value="both">Both Platforms</option>
            <option value="hyperliquid">HyperLiquid Only</option>
            <option value="allora">Allora Only</option>
            <option value="active">Active Only</option>
          </select>
          <Filter className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none" />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex flex-wrap gap-3">
        <button
          onClick={handleActivatePopular}
          disabled={loading}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <TrendingUp className="w-4 h-4 mr-2" />
          Activate Popular
        </button>
        <button
          onClick={handleClearAll}
          disabled={loading}
          className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Settings className="w-4 h-4 mr-2" />
          Clear All
        </button>
      </div>

      {/* Crypto Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredCryptos.map((crypto) => (
          <div
            key={crypto.symbol}
            className={`card transition-all duration-200 ${
              crypto.is_active
                ? "ring-2 ring-primary-500 bg-primary-50 dark:bg-primary-900/20"
                : "hover:shadow-md"
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center">
                <div className="text-lg font-bold text-primary">
                  {crypto.symbol}
                </div>
                {crypto.topic_id && (
                  <span className="ml-2 text-xs text-secondary">
                    #{crypto.topic_id}
                  </span>
                )}
              </div>
              {getAvailabilityBadge(crypto.availability)}
            </div>

            <div className="space-y-2 mb-4">
              {crypto.last_price && (
                <div className="flex justify-between text-sm">
                  <span className="text-secondary">Price:</span>
                  <span className="font-medium">
                    {formatPrice(crypto.last_price)}
                  </span>
                </div>
              )}
              {crypto.volume_24h && (
                <div className="flex justify-between text-sm">
                  <span className="text-secondary">Volume:</span>
                  <span className="font-medium">
                    {formatVolume(crypto.volume_24h)}
                  </span>
                </div>
              )}
            </div>

            <button
              onClick={() =>
                handleToggleCrypto(crypto.symbol, !crypto.is_active)
              }
              disabled={updatingCrypto === crypto.symbol || loading}
              className={`w-full flex items-center justify-center px-4 py-2 rounded-lg font-medium transition-colors ${
                crypto.is_active
                  ? "bg-red-600 text-white hover:bg-red-700"
                  : "bg-green-600 text-white hover:bg-green-700"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {updatingCrypto === crypto.symbol ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : crypto.is_active ? (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Deactivate
                </>
              ) : (
                <>
                  <Circle className="w-4 h-4 mr-2" />
                  Activate
                </>
              )}
            </button>
          </div>
        ))}
      </div>

      {filteredCryptos.length === 0 && !loading && (
        <div className="text-center py-8">
          <div className="text-gray-400 mb-2">No cryptocurrencies found</div>
          <div className="text-sm text-secondary">
            Try adjusting your search or filter criteria
          </div>
        </div>
      )}
    </div>
  );
};

export default CryptoManager;
