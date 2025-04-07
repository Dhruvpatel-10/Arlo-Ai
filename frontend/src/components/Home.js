import React, { useState, useEffect } from "react";
import { Box, Paper, Typography, Alert, Snackbar } from "@mui/material";
import { useApp } from "../context/AppContext";

const Home = () => {
  const { messages, isListening, isConnected } = useApp();
  const [showError, setShowError] = useState(false);

  useEffect(() => {
    // Show error when disconnected
    if (!isConnected) {
      setShowError(true);
    } else {
      setShowError(false);
    }
  }, [isConnected]);

  return (
    <>
      <Paper
        sx={{
          height: "calc(100vh - 120px)",
          backgroundColor: "#242424",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          border: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        {/* Connection status */}
        {!isConnected && (
          <Box
            sx={{
              backgroundColor: "rgba(255, 0, 0, 0.1)",
              p: 1,
              textAlign: "center",
              borderBottom: "1px solid rgba(255, 0, 0, 0.2)",
            }}
          >
            <Typography color="error">
              Connecting to server... Please wait.
            </Typography>
          </Box>
        )}

        {/* Wake Word Instructions */}
        <Box
          sx={{
            backgroundColor: "rgba(0, 255, 157, 0.1)",
            p: 2,
            textAlign: "center",
            borderBottom: "1px solid rgba(0, 255, 157, 0.2)",
          }}
        >
          <Typography>
            Say "Hey Arlo" to start, "Stop Arlo" to stop, "Arlo pause" to pause,
            or "Arlo continue" to resume
          </Typography>
          {isListening && (
            <Typography color="primary" sx={{ mt: 1 }}>
              Listening...
            </Typography>
          )}
        </Box>

        {/* Messages area */}
        <Box sx={{ flexGrow: 1, overflow: "auto", p: 2 }}>
          {messages.map((message, index) => (
            <Box
              key={index}
              sx={{
                display: "flex",
                justifyContent: message.isUser ? "flex-end" : "flex-start",
                mb: 2,
              }}
            >
              <Paper
                sx={{
                  p: 2,
                  maxWidth: "70%",
                  backgroundColor: message.isUser
                    ? "rgba(0, 255, 157, 0.1)"
                    : "#1a1a1a",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: 2,
                }}
              >
                <Typography color="text.primary">{message.text}</Typography>
              </Paper>
            </Box>
          ))}
        </Box>
      </Paper>

      {/* Error Snackbar */}
      <Snackbar
        open={showError}
        autoHideDuration={6000}
        onClose={() => setShowError(false)}
      >
        <Alert severity="error" sx={{ width: "100%" }}>
          Not connected to server. Please wait or refresh the page.
        </Alert>
      </Snackbar>
    </>
  );
};

export default Home;
