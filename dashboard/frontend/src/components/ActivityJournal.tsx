import React, { useState, useEffect, useRef } from "react";
import {
  Activity,
  Brain,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  Trash2,
  Pause,
  Play,
  Download,
  Search,
  Bot,
  Zap,
  Target,
} from "lucide-react";
import { useWebSocket } from "../hooks/useWebSocket";

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

interface ActivityJournalProps {
  isMonitoring?: boolean;
  maxItems?: number;
}

const ActivityJournal: React.FC<ActivityJournalProps> = ({
  isMonitoring = false,
  maxItems = 100,
}) => {
  const [localActivities, setLocalActivities] = useState<ActivityItem[]>([]);
  const [filteredActivities, setFilteredActivities] = useState<ActivityItem[]>(
    []
  );
  const [isPaused, setIsPaused] = useState(false);
  const [selectedSeverity, setSelectedSeverity] = useState<string>("all");
  const [selectedType, setSelectedType] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [isAutoScroll, setIsAutoScroll] = useState(true);

  const scrollRef = useRef<HTMLDivElement>(null);
  const { activityStream, isConnected, botModeState, clearActivityStream } =
    useWebSocket();

  // Sync WebSocket activity stream with local state
  useEffect(() => {
    if (!isPaused && activityStream.length > 0) {
      setLocalActivities((prev) => {
        const newActivities = [...prev, ...activityStream.slice(prev.length)];
        // Keep only maxItems most recent
        return newActivities.slice(-maxItems);
      });
    }
  }, [activityStream, isPaused, maxItems]);

  // Filter activities based on criteria
  useEffect(() => {
    let filtered = [...localActivities];

    // Filter by severity
    if (selectedSeverity !== "all") {
      filtered = filtered.filter(
        (activity) => activity.severity === selectedSeverity
      );
    }

    // Filter by type
    if (selectedType !== "all") {
      filtered = filtered.filter(
        (activity) => activity.activity_type === selectedType
      );
    }

    // Filter by search term
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (activity) =>
          activity.title.toLowerCase().includes(searchLower) ||
          activity.description.toLowerCase().includes(searchLower) ||
          (activity.token && activity.token.toLowerCase().includes(searchLower))
      );
    }

    setFilteredActivities(filtered);
  }, [localActivities, selectedSeverity, selectedType, searchTerm]);

  // Auto-scroll to bottom when new activities arrive
  useEffect(() => {
    if (isAutoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [filteredActivities, isAutoScroll]);

  const getActivityIcon = (activityType: string) => {
    switch (activityType) {
      case "AI_DECISION":
        return <Brain className="w-4 h-4" />;
      case "ALLORA_PREDICTION":
        return <Target className="w-4 h-4" />;
      case "TRADING_SIGNAL":
        return <TrendingUp className="w-4 h-4" />;
      case "BOT_PROCESS":
        return <Bot className="w-4 h-4" />;
      case "MODE_CHANGE":
        return <Zap className="w-4 h-4" />;
      case "VALIDATION":
        return <CheckCircle className="w-4 h-4" />;
      case "ERROR":
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "SUCCESS":
        return "text-green-600 bg-green-50 border-green-200";
      case "INFO":
        return "text-blue-600 bg-blue-50 border-blue-200";
      case "WARNING":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "ERROR":
        return "text-red-600 bg-red-50 border-red-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getTypeColor = (activityType: string) => {
    switch (activityType) {
      case "AI_DECISION":
        return "text-purple-600 bg-purple-50";
      case "ALLORA_PREDICTION":
        return "text-indigo-600 bg-indigo-50";
      case "TRADING_SIGNAL":
        return "text-green-600 bg-green-50";
      case "BOT_PROCESS":
        return "text-blue-600 bg-blue-50";
      case "MODE_CHANGE":
        return "text-orange-600 bg-orange-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("fr-FR", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const getUniqueTypes = () => {
    const types = new Set(
      localActivities.map((activity) => activity.activity_type)
    );
    return Array.from(types).sort();
  };

  const handleClearActivities = () => {
    setLocalActivities([]);
    clearActivityStream();
  };

  const handleExportActivities = () => {
    const dataStr = JSON.stringify(filteredActivities, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `activity-journal-${
      new Date().toISOString().split("T")[0]
    }.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const ActivityItem: React.FC<{ activity: ActivityItem }> = ({ activity }) => (
    <div className="flex items-start space-x-3 p-3 border-b border-gray-100 hover:bg-gray-50 transition-colors">
      {/* Icon & Type */}
      <div className="flex-shrink-0 mt-1">
        <div
          className={`p-2 rounded-full ${getTypeColor(activity.activity_type)}`}
        >
          {getActivityIcon(activity.activity_type)}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h4 className="text-sm font-medium text-gray-900 truncate">
              {activity.title}
            </h4>
            {activity.token && (
              <span className="inline-flex px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                {activity.token}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <span
              className={`inline-flex px-2 py-1 text-xs font-medium rounded border ${getSeverityColor(
                activity.severity
              )}`}
            >
              {activity.severity}
            </span>
            <span className="text-xs text-gray-500">
              {formatTimestamp(activity.timestamp)}
            </span>
          </div>
        </div>

        <p className="mt-1 text-sm text-gray-600">{activity.description}</p>

        {/* Additional Data */}
        {activity.data && Object.keys(activity.data).length > 0 && (
          <div className="mt-2">
            <details className="text-xs">
              <summary className="text-gray-500 cursor-pointer hover:text-gray-700">
                Détails techniques
              </summary>
              <pre className="mt-1 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
                {JSON.stringify(activity.data, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </div>
  );

  if (!isMonitoring && botModeState?.mode !== "ACTIVE") {
    return (
      <div className="card">
        <div className="card-header">
          <div className="flex items-center">
            <Activity className="w-5 h-5 text-gray-400 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">
              Journal d'Activités
            </h2>
          </div>
        </div>

        <div className="p-8 text-center">
          <Activity className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Journal Inactif
          </h3>
          <p className="text-gray-600 mb-4">
            Le journal d'activités n'est disponible que pendant le monitoring
            actif.
          </p>
          <p className="text-sm text-gray-500">
            Activez le monitoring pour voir le flux temps réel des décisions IA,
            prédictions Allora et actions du bot.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Activity className="w-5 h-5 text-green-500 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">
              Journal d'Activités
            </h2>
            <div className="ml-3 flex items-center">
              {isConnected ? (
                <div className="flex items-center text-green-600">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2" />
                  <span className="text-sm">Live</span>
                </div>
              ) : (
                <div className="flex items-center text-red-600">
                  <div className="w-2 h-2 bg-red-500 rounded-full mr-2" />
                  <span className="text-sm">Offline</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">
              {filteredActivities.length} / {localActivities.length} activités
            </span>

            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`p-2 rounded-md ${
                isPaused
                  ? "text-green-600 hover:bg-green-50"
                  : "text-yellow-600 hover:bg-yellow-50"
              }`}
              title={isPaused ? "Reprendre" : "Pause"}
            >
              {isPaused ? (
                <Play className="w-4 h-4" />
              ) : (
                <Pause className="w-4 h-4" />
              )}
            </button>

            <button
              onClick={handleExportActivities}
              className="p-2 text-blue-600 hover:bg-blue-50 rounded-md"
              title="Exporter"
              disabled={filteredActivities.length === 0}
            >
              <Download className="w-4 h-4" />
            </button>

            <button
              onClick={handleClearActivities}
              className="p-2 text-red-600 hover:bg-red-50 rounded-md"
              title="Vider le journal"
              disabled={localActivities.length === 0}
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Severity Filter */}
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="all">Toutes les sévérités</option>
            <option value="SUCCESS">Succès</option>
            <option value="INFO">Information</option>
            <option value="WARNING">Avertissement</option>
            <option value="ERROR">Erreur</option>
          </select>

          {/* Type Filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="all">Tous les types</option>
            {getUniqueTypes().map((type) => (
              <option key={type} value={type}>
                {type.replace("_", " ")}
              </option>
            ))}
          </select>

          {/* Auto-scroll Toggle */}
          <div className="flex items-center">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={isAutoScroll}
                onChange={(e) => setIsAutoScroll(e.target.checked)}
                className="form-checkbox h-4 w-4 text-primary-600"
              />
              <span className="ml-2 text-sm text-gray-700">Auto-scroll</span>
            </label>
          </div>
        </div>
      </div>

      {/* Status Messages */}
      {isPaused && (
        <div className="px-6 py-3 bg-yellow-50 border-b border-yellow-200">
          <div className="flex items-center">
            <Pause className="w-4 h-4 text-yellow-600 mr-2" />
            <span className="text-sm text-yellow-700">
              Journal en pause - Les nouvelles activités ne s'affichent pas
            </span>
          </div>
        </div>
      )}

      {!isConnected && (
        <div className="px-6 py-3 bg-red-50 border-b border-red-200">
          <div className="flex items-center">
            <AlertCircle className="w-4 h-4 text-red-600 mr-2" />
            <span className="text-sm text-red-700">
              Connexion perdue - Le journal peut ne pas être à jour
            </span>
          </div>
        </div>
      )}

      {/* Activity Stream */}
      <div ref={scrollRef} className="max-h-96 overflow-y-auto">
        {filteredActivities.length === 0 ? (
          <div className="p-8 text-center">
            <Clock className="w-8 h-8 text-gray-300 mx-auto mb-3" />
            {localActivities.length === 0 ? (
              <>
                <h3 className="text-sm font-medium text-gray-900 mb-1">
                  En attente d'activités...
                </h3>
                <p className="text-xs text-gray-500">
                  Les décisions IA et actions du bot s'afficheront ici en temps
                  réel
                </p>
              </>
            ) : (
              <>
                <h3 className="text-sm font-medium text-gray-900 mb-1">
                  Aucune activité trouvée
                </h3>
                <p className="text-xs text-gray-500">
                  Ajustez les filtres pour voir plus d'activités
                </p>
              </>
            )}
          </div>
        ) : (
          <div>
            {filteredActivities.map((activity, index) => (
              <ActivityItem
                key={`${activity.id}-${index}`}
                activity={activity}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ActivityJournal;
