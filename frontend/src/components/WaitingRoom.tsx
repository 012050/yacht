import { useState } from "react";
import api from "../utils/api";

interface Props {
  onGameCreated: (gameId: string) => void;
}

export default function WaitingRoom({ onGameCreated }: Props) {
  const [joinCode, setJoinCode] = useState("");
  const [gameId, setGameId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [isHost, setIsHost] = useState(false);
  const [joinCodeDisplay, setJoinCodeDisplay] = useState("");

  const handleCreate = async () => {
    try {
      const { data } = await api.post("/games/create", { timeout_duration: 60 });
      setGameId(data.id);
      setIsHost(true);
      setJoinCodeDisplay(data.join_code);
      setMessage("게임이 생성되었습니다. 친구에게 코드를 알려주세요!");
    } catch (err: any) {
      setMessage(err.response?.data?.detail || "생성 실패");
    }
  };

  const handleJoin = async () => {
    try {
      const { data } = await api.post("/games/join", { join_code: joinCode });
      setGameId(data.game_id);
      setMessage("게임에 성공적으로 참가했습니다!");
    } catch (err: any) {
      setMessage(err.response?.data?.detail || "참가 실패");
    }
  };

  const handleStart = async () => {
    if (!gameId) return;
    try {
      await api.post(`/games/${gameId}/start`);
      onGameCreated(gameId);
    } catch (err: any) {
      setMessage(err.response?.data?.detail || "시작 실패");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h1 className="text-3xl font-bold mb-8 text-center text-slate-800">대기방</h1>
        {message && <p className="text-sm mb-6 p-4 bg-blue-50 text-blue-700 rounded-lg text-center border border-blue-100">{message}</p>}
        {joinCodeDisplay && (
          <div className="mb-6 p-4 bg-purple-50 rounded-lg text-center border border-purple-100">
            <p className="text-sm text-purple-600 mb-1">참여 코드</p>
            <p className="text-3xl font-bold text-purple-800 tracking-widest">{joinCodeDisplay}</p>
          </div>
        )}
        <div className="space-y-4">
          <button onClick={handleCreate} className="w-full bg-emerald-600 text-white p-3 rounded-lg font-semibold hover:bg-emerald-700 transition-colors">
            새 게임 생성
          </button>
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-slate-500">또는</span>
            </div>
          </div>
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="참여 코드"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              className="flex-1 p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none uppercase"
              maxLength={6}
            />
            <button onClick={handleJoin} className="bg-blue-600 text-white px-6 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
              참가
            </button>
          </div>
          {isHost && gameId && (
            <button onClick={handleStart} className="w-full bg-purple-600 text-white p-3 rounded-lg font-semibold hover:bg-purple-700 transition-colors mt-4">
              게임 시작
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
