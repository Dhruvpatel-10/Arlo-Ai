import React from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Divider,
} from "@mui/material";

const About = ({ open, onClose }) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>About Arlo AI Assistant</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Version 1.0.0
          </Typography>
          <Typography variant="body1" paragraph>
            Arlo AI Assistant is an intelligent voice and text-based assistant
            that helps you with various tasks. It uses advanced natural language
            processing and machine learning to understand and respond to your
            requests.
          </Typography>
        </Box>
        <Divider sx={{ my: 2 }} />
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Features
          </Typography>
          <Typography variant="body1" component="div">
            <ul>
              <li>Voice and text-based interaction</li>
              <li>Wake word detection</li>
              <li>Natural language understanding</li>
              <li>Multi-language support</li>
              <li>Customizable settings</li>
            </ul>
          </Typography>
        </Box>
        <Divider sx={{ my: 2 }} />
        <Box>
          <Typography variant="h6" gutterBottom>
            Contact & Support
          </Typography>
          <Typography variant="body1" paragraph>
            For support or inquiries, please contact us at:
            <br />
            support@arloai.com
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default About;
