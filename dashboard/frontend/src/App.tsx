import Dashboard from "./components/Dashboard";
import { ThemeProvider } from "./components/ThemeProvider";
import ErrorBoundary from "./components/ErrorBoundary";
import { WebSocketProvider } from "./context/WebSocketContext";

function App() {
  return (
    <ErrorBoundary>
      <WebSocketProvider>
        <ThemeProvider>
          <Dashboard />
        </ThemeProvider>
      </WebSocketProvider>
    </ErrorBoundary>
  );
}

export default App;
