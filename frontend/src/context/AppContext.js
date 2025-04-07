import React, {
  createContext,
  useState,
  useContext,
  useEffect,
  useCallback,
  useRef,
} from "react";

const AppContext = createContext();

// Update WebSocket URL to use the correct protocol and host
const WEBSOCKET_URL = "ws://127.0.0.1:8000/ws";
const MAX_RETRIES = 5;
const RETRY_DELAY = 3000; // 3 seconds

export const AppProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [wakeWordActive, setWakeWordActive] = useState(false);

  // Use refs for values that shouldn't trigger re-renders
  const socketRef = useRef(null);
  const retryCountRef = useRef(0);
  const reconnectTimeoutRef = useRef(null);
  const mountedRef = useRef(true);

  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    retryCountRef.current = 0;
  }, []);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;

    cleanup();

    try {
      console.log("Connecting to WebSocket at:", WEBSOCKET_URL);
      const ws = new WebSocket(WEBSOCKET_URL);

      ws.onopen = () => {
        if (!mountedRef.current) {
          ws.close();
          return;
        }
        console.log("Connected to server");
        setIsConnected(true);
        retryCountRef.current = 0;
        setConnectionError(null);
        setWakeWordActive(true);
      };

      ws.onclose = (event) => {
        if (!mountedRef.current) return;

        console.log("Disconnected from server", event);
        setIsConnected(false);
        setConnectionError(
          `Disconnected: ${event.code} ${event.reason || "No reason provided"}`
        );

        if (retryCountRef.current < MAX_RETRIES && mountedRef.current) {
          const nextRetry = retryCountRef.current + 1;
          console.log(
            `Attempting to reconnect (${nextRetry}/${MAX_RETRIES})...`
          );
          retryCountRef.current = nextRetry;
          reconnectTimeoutRef.current = setTimeout(connect, RETRY_DELAY);
        } else {
          console.error("Max reconnection attempts reached");
          setConnectionError(
            "Max reconnection attempts reached. Please refresh the page."
          );
          setIsListening(false);
          setWakeWordActive(false);
        }
      };

      ws.onerror = (error) => {
        if (!mountedRef.current) return;

        console.error("WebSocket error:", error);
        setIsConnected(false);
        setConnectionError(
          "Connection error occurred. Please check if the server is running."
        );
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const data = JSON.parse(event.data);
          console.log("Received message:", data);

          switch (data.type) {
            case "connection_established":
              console.log("Connection established with server");
              setIsConnected(true);
              setConnectionError(null);
              break;

            case "transcription":
              if (data.text && data.text.trim()) {
                console.log("Adding transcription:", data.text);
                setMessages((prev) => {
                  if (
                    prev.length > 0 &&
                    prev[prev.length - 1].text === data.text &&
                    prev[prev.length - 1].isUser
                  ) {
                    return prev;
                  }
                  return [...prev, { text: data.text, isUser: true }];
                });
              }
              break;

            case "assistant_response":
              if (data.text && data.text.trim()) {
                console.log("Adding response:", data.text);
                setMessages((prev) => {
                  if (
                    prev.length > 0 &&
                    prev[prev.length - 1].text === data.text &&
                    !prev[prev.length - 1].isUser
                  ) {
                    return prev;
                  }
                  return [...prev, { text: data.text, isUser: false }];
                });
              }
              break;

            case "status":
              console.log("Status update:", data.message);
              if (data.message === "Started listening") {
                setIsListening(true);
              } else if (data.message === "Stopped listening") {
                setIsListening(false);
              } else if (data.message.includes("Wake word detection started")) {
                setWakeWordActive(true);
                console.log("Wake word detection is now active");
              }
              break;

            case "error":
              console.error("Server error:", data.message);
              setIsListening(false);
              setConnectionError(data.message);
              break;

            default:
              console.log("Unhandled message type:", data.type);
          }
        } catch (error) {
          console.error("Error parsing message:", error);
          setConnectionError("Error parsing server message");
        }
      };

      socketRef.current = ws;
    } catch (error) {
      if (!mountedRef.current) return;

      console.error("Connection error:", error);
      setConnectionError(
        "Failed to create WebSocket connection. Please check if the server is running."
      );
      if (retryCountRef.current < MAX_RETRIES && mountedRef.current) {
        const nextRetry = retryCountRef.current + 1;
        console.log(`Attempting to reconnect (${nextRetry}/${MAX_RETRIES})...`);
        retryCountRef.current = nextRetry;
        reconnectTimeoutRef.current = setTimeout(connect, RETRY_DELAY);
      }
    }
  }, [cleanup]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      cleanup();
    };
  }, [connect, cleanup]);

  const value = {
    messages,
    isListening,
    isConnected,
    connectionError,
    wakeWordActive,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
};
