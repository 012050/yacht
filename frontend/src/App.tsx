import { useState, useEffect } from "react";
import LoginPage from "./components/LoginPage";
import WaitingRoom from "./components/WaitingRoom";
import DiceRoller from "./components/DiceRoller";
import Scoreboard from "./components/Scoreboard";
import CategorySelector from "./components/CategorySelector";
import ResultScreen from "./components/ResultScreen";
import { useWebSocket } from "./hooks/useWebSocket";

type Page = "login" | "waiting" | "game" | "result";

function App() {
  const [page, setPage] = useState<Page>(() => {
    return localStorage.getItem("access_token") ? "waiting" : "login";
  });
  const [gameId, setGameId] = useState<string | null>(null);
  useWebSocket(gameId);

  const handleGameCreated = (id: string) => {
    setGameId(id);
    setPage("game");
  };

  const handleReplay = () => {
    setGameId(null);
    setPage("waiting");
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setPage("login");
  };

  const handleLoginSuccess = () => {
    setPage("waiting");
  };

  if (page === "login") return <LoginPage onLoginSuccess={handleLoginSuccess} />;

  if (page === "waiting") return <WaitingRoom onGameCreated={handleGameCreated} />;

  if (page === "result" && gameId) return <ResultScreen gameId={gameId} onReplay={handleReplay} />;

  return (
    <div className="min-h-screen bg-slate-100 p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-slate-800">?? ??? ??</h1>
        <button onClick={handleLogout} className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600">????</button>
      </div>
      <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-4">
        <DiceRoller />
        <CategorySelector />
        <div className="md:col-span-2">
          <Scoreboard />
        </div>
      </div>
    </div>
  );
}

export default App;
