import { useEffect, useRef, useState } from "react";

import { WS_URL } from "../lib/config";
import { useAuthStore } from "../stores/auth";

export interface WSEvent {
    event_id: string;
    type: string;
    occurred_at: string;
    org_id: string;
    actor_id: string | null;
    aggregate_type: string;
    aggregate_id: string;
    version: number;
    payload: Record<string, unknown>;
}

export function useWebSocket(topics: string[] = ["delivery", "driver", "dispatcher", "notification"]) {
    const token = useAuthStore((s) => s.accessToken);
    const [events, setEvents] = useState<WSEvent[]>([]);
    const [connected, setConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        if (!token) return;
        const url = `${WS_URL}?token=${token}&topics=${topics.join(",")}`;
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => setConnected(true);
        ws.onclose = () => setConnected(false);
        ws.onerror = () => setConnected(false);
        ws.onmessage = (msg) => {
            try {
                const parsed: WSEvent = JSON.parse(msg.data);
                setEvents((prev) => [parsed, ...prev].slice(0, 100));
            } catch {
                /* ignore */
            }
        };

        const ping = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) ws.send("ping");
        }, 20000);

        return () => {
            clearInterval(ping);
            ws.close();
        };
    }, [token, topics.join(",")]);

    return { events, connected };
}