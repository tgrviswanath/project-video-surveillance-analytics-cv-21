import React from "react";
import { AppBar, Toolbar, Typography } from "@mui/material";
import VideocamIcon from "@mui/icons-material/Videocam";

export default function Header() {
  return (
    <AppBar position="static" color="primary">
      <Toolbar>
        <VideocamIcon sx={{ mr: 1 }} />
        <Typography variant="h6" fontWeight="bold">
          Video Surveillance Analytics
        </Typography>
      </Toolbar>
    </AppBar>
  );
}
