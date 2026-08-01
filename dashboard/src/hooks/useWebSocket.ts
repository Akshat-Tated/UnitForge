import { useEffect, useRef } from "react";
import { Client } from "@stomp/stompjs";
import SockJS from "sockjs-client/dist/sockjs";

interface UseWebSocketOptions {
  topics: string[];
  onMessage: (topic: string, data: unknown) => void;
  enabled?: boolean;
}

export function useWebSocket({
  topics,
  onMessage,
  enabled = true,
}: UseWebSocketOptions) {
  const clientRef = useRef<Client | null>(null);

  useEffect(() => {
    if (!enabled) return;

    const wsBase = import.meta.env.VITE_WS_URL || "http://localhost:8080";
    const client = new Client({
      webSocketFactory: () => new SockJS(`${wsBase}/ws`),
      reconnectDelay: 5000,
      onConnect: () => {
        topics.forEach((topic) => {
          client.subscribe(topic, (message) => {
            try {
              const data = JSON.parse(message.body);
              onMessage(topic, data);
            } catch {
              console.error("Failed to parse WebSocket message:", message.body);
            }
          });
        });
      },
      onDisconnect: () => {
        console.log("WebSocket disconnected");
      },
    });

    client.activate();
    clientRef.current = client;

    return () => {
      client.deactivate();
    };
  }, [enabled]);
}
