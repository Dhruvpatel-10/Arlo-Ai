import { io } from "socket.io-client";

class SocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
  }

  connect() {
    if (!this.socket) {
      this.socket = io("http://localhost:5000", {
        transports: ["websocket"],
        reconnection: true,
        reconnectionAttempts: 5,
      });

      this.socket.on("connect", () => {
        console.log("Connected to server");
        this.isConnected = true;
      });

      this.socket.on("disconnect", () => {
        console.log("Disconnected from server");
        this.isConnected = false;
      });

      this.socket.on("error", (error) => {
        console.error("Socket error:", error);
      });
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
    }
  }

  sendMessage(message) {
    if (this.isConnected) {
      this.socket.emit("message", message);
    }
  }

  onMessage(callback) {
    if (this.socket) {
      this.socket.on("message", callback);
    }
  }

  onWakeWordDetected(callback) {
    if (this.socket) {
      this.socket.on("wake_word_detected", callback);
    }
  }

  onAudioData(callback) {
    if (this.socket) {
      this.socket.on("audio_data", callback);
    }
  }
}

export default new SocketService();
