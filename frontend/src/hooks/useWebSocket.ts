import { useEffect, useRef, useCallback, useState } from 'react';
import { WSMessage } from '../types/game';

export function useWebSocket(gameId: string | null): {
  isConnected: boolean;
  sendMessage: (type: string, payload: unknown) => void;
  onMessage: (callback: (msg: WSMessage) => void) => void;
} {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const callbacksRef = useRef<Set<(msg: WSMessage) => void>>(new Set());
  const reconnectAttemptsRef = useRef(0);
  const maxReconnects = 3;

  // Normalize backend status to uppercase in WebSocket payloads.
  const normalizeMessage = (msg: WSMessage): WSMessage => {
    const payload = msg.payload as Record<string, unknown> | undefined;
    if (payload && typeof payload === 'object') {
      if (typeof payload.status === 'string') {
        payload.status = payload.status.toUpperCase();
      }
      if (payload.state && typeof payload.state === 'object') {
        const state = payload.state as Record<string, unknown>;
        if (typeof state.status === 'string') {
          state.status = state.status.toUpperCase();
        }
      }
    }
    return msg;
  };

  const createWebSocket = useCallback(() => {
    if (!gameId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Same-origin connection: the browser sends the access_token cookie
    // (HttpOnly) automatically on the WebSocket upgrade request.
    const url = `${protocol}//${window.location.host}/ws/${gameId}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      reconnectAttemptsRef.current = 0;
    };

    ws.onclose = () => {
      setIsConnected(false);
      if (reconnectAttemptsRef.current < maxReconnects) {
        reconnectAttemptsRef.current++;
        setTimeout(() => {
          createWebSocket();
        }, 2000);
      }
    };

    ws.onerror = () => {
      // onclose will fire after onerror, so we don't need to do anything here.
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        let msg: WSMessage = JSON.parse(event.data);
        msg = normalizeMessage(msg);
        callbacksRef.current.forEach((cb) => cb(msg));
      } catch {
        // ignore malformed messages
      }
    };
  }, [gameId]);

  useEffect(() => {
    createWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [createWebSocket]);

  const sendMessage = useCallback(
    (type: string, payload: unknown) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type, payload }));
      }
    },
    []
  );

  const onMessage = useCallback((callback: (msg: WSMessage) => void) => {
    callbacksRef.current.add(callback);
    return () => {
      callbacksRef.current.delete(callback);
    };
  }, []);

  return { isConnected, sendMessage, onMessage };
}
