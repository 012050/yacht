import { useEffect, useRef } from "react";
import { useGameStore } from "../store/gameStore";

export function useWebSocket(gameId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const setGameState = useGameStore((s) => s.setGameState);

  useEffect(() => {
    if (!gameId) return;

    const token = localStorage.getItem("access_token");
    if (!token) return;

    const ws = new WebSocket(
      `ws://localhost:8000/ws/games/${gameId}?token=${token}`
    );
    wsRef.current = ws;
    (window as any).__ws = ws;

    ws.onopen = () => {
      // ?? ?? ??
      ws.send(JSON.stringify({
        type: "SESSION_RECOVER",
        payload: { game_id: gameId }
      }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === "STATE_UPDATE" || msg.type === "SESSION_RECOVERED") {
        setGameState(msg.payload);
      } else if (msg.type === "GAME_FINISHED") {
        setGameState(msg.payload);
      } else if (msg.type === "ERROR") {
        console.error("WebSocket error:", msg.payload.message);
      }
    };

    ws.onclose = () => {
      // ?? ??? ?? (?? 3?)
      console.log("WebSocket disconnected, attempting reconnect...");
    };

    return () => {
      ws.close();
      wsRef.current = null;
      (window as any).__ws = null;
    };
  }, [gameId]);

  return wsRef;
}
