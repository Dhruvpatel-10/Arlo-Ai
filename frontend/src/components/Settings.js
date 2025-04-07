import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Grid,
  Typography,
} from "@mui/material";

const Settings = ({ open, onClose }) => {
  const [settings, setSettings] = useState({
    wakeWord: "Arlo",
    language: "en-US",
    voiceEnabled: true,
    notifications: true,
    darkMode: false,
  });

  const handleChange = (field) => (event) => {
    setSettings({
      ...settings,
      [field]:
        event.target.type === "checkbox"
          ? event.target.checked
          : event.target.value,
    });
  };

  const handleSave = () => {
    // Here you would implement the logic to save settings to the backend
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Settings</DialogTitle>
      <DialogContent>
        <Grid container spacing={3} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Wake Word"
              value={settings.wakeWord}
              onChange={handleChange("wakeWord")}
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Language"
              value={settings.language}
              onChange={handleChange("language")}
              variant="outlined"
              select
              SelectProps={{
                native: true,
              }}
            >
              <option value="en-US">English (US)</option>
              <option value="es-ES">Spanish</option>
              <option value="fr-FR">French</option>
              <option value="de-DE">German</option>
            </TextField>
          </Grid>
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.voiceEnabled}
                  onChange={handleChange("voiceEnabled")}
                  color="primary"
                />
              }
              label="Voice Input/Output"
            />
          </Grid>
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.notifications}
                  onChange={handleChange("notifications")}
                  color="primary"
                />
              }
              label="Notifications"
            />
          </Grid>
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.darkMode}
                  onChange={handleChange("darkMode")}
                  color="primary"
                />
              }
              label="Dark Mode"
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave} color="primary" variant="contained">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default Settings;
