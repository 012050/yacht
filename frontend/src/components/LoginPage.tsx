import { useState } from "react";
import api from "../utils/api";

interface Props {
  onLoginSuccess: () => void;
}

export default function LoginPage({ onLoginSuccess }: Props) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      if (isLogin) {
        const { data } = await api.post("/auth/login", { username, password });
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        alert("??? ??! ????? ?????.");
        onLoginSuccess();
      } else {
        await api.post("/auth/register", { username, password, nickname });
        const { data } = await api.post("/auth/login", { username, password });
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        alert("???? ? ??? ??!");
        onLoginSuccess();
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || "?? ??";
      setError(msg);
      alert("?? ??: " + msg);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-xl shadow-lg w-96">
        <h1 className="text-3xl font-bold mb-8 text-center text-slate-800">
          {isLogin ? "???" : "????"}
        </h1>
        {error && <p className="text-red-500 mb-4 text-center bg-red-50 p-2 rounded">{error}</p>}
        <input
          type="text"
          placeholder="???"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full p-3 mb-4 border border-slate-300 rounded-lg"
          maxLength={20}
        />
        {!isLogin && <input type="text" placeholder="???" value={nickname} onChange={(e) => setNickname(e.target.value)} className="w-full p-3 mb-4 border border-slate-300 rounded-lg" maxLength={20} />}
        <input type="password" placeholder="????" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full p-3 mb-6 border border-slate-300 rounded-lg" maxLength={20} />
        <button type="submit" className="w-full bg-blue-600 text-white p-3 rounded-lg font-semibold hover:bg-blue-700">
          {isLogin ? "???" : "????"}
        </button>
        <p className="mt-6 text-center text-sm text-slate-600">
          {isLogin ? "??? ?????? " : "?? ??? ?????? "}
          <button type="button" onClick={() => { setIsLogin(!isLogin); setError(""); }} className="text-blue-600 font-medium hover:underline">
            {isLogin ? "????" : "???"}
          </button>
        </p>
      </form>
    </div>
  );
}
