import React from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { AppProvider } from "./context/AppContext";
import Home from "./components/Home";
import { Box } from "@mui/material";

const darkTheme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#00ff9d",
    },
    background: {
      default: "#1a1a1a",
      paper: "#242424",
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <AppProvider>
        <Box
          sx={{
            minHeight: "100vh",
            p: 3,
            backgroundColor: "background.default",
          }}
        >
          <Home />
        </Box>
      </AppProvider>
    </ThemeProvider>
  );
}

export default App;
