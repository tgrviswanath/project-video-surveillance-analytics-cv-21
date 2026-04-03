import React, { useState, useRef } from "react";
import {
  Box, CircularProgress, Alert, Typography, Paper,
  Chip, Grid, Divider, Table, TableBody, TableCell,
  TableHead, TableRow,
} from "@mui/material";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { analyzeVideo } from "../services/surveillanceApi";

export default function SurveillancePage() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef();

  const handleFile = async (file) => {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const r = await analyzeVideo(fd);
      setResult(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Paper
        variant="outlined"
        onClick={() => fileRef.current.click()}
        onDrop={(e) => { e.preventDefault(); handleFile(e.dataTransfer.files[0]); }}
        onDragOver={(e) => e.preventDefault()}
        sx={{
          p: 3, mb: 2, textAlign: "center", cursor: "pointer", borderStyle: "dashed",
          "&:hover": { bgcolor: "action.hover" },
        }}
      >
        <input ref={fileRef} type="file" hidden accept=".mp4,.avi,.mov,.mkv,.webm"
          onChange={(e) => handleFile(e.target.files[0])} />
        {loading
          ? <Box>
              <CircularProgress size={28} sx={{ mb: 1 }} />
              <Typography color="text.secondary">Analyzing video… this may take a moment</Typography>
            </Box>
          : <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 1 }}>
              <UploadFileIcon color="action" />
              <Typography color="text.secondary">
                Drag & drop or click — MP4 / AVI / MOV / MKV
              </Typography>
            </Box>
        }
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Box>
          {/* Summary chips */}
          <Box sx={{ display: "flex", gap: 1, mb: 2, flexWrap: "wrap" }}>
            <Chip label={`${result.duration_sec}s video`} variant="outlined" size="small" />
            <Chip label={`${result.analyzed_frames} frames analyzed`} variant="outlined" size="small" />
            <Chip label={`Max ${result.max_people_in_frame} people`} color="primary" size="small" />
            <Chip label={`Avg ${result.avg_people_per_frame} people/frame`} variant="outlined" size="small" />
            {result.alert_count > 0 && (
              <Chip
                icon={<WarningAmberIcon />}
                label={`${result.alert_count} crowd alert${result.alert_count > 1 ? "s" : ""}`}
                color="error"
                size="small"
              />
            )}
          </Box>

          <Grid container spacing={2} sx={{ mb: 2 }}>
            {/* Thumbnail */}
            {result.thumbnail && (
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Peak Frame (Most People)</Typography>
                <Paper variant="outlined" sx={{ p: 1, textAlign: "center" }}>
                  <img
                    src={`data:image/jpeg;base64,${result.thumbnail}`}
                    alt="peak frame"
                    style={{ maxWidth: "100%", maxHeight: 300, borderRadius: 4 }}
                  />
                </Paper>
              </Grid>
            )}

            {/* Total detections */}
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>Total Detections</Typography>
              <Paper variant="outlined" sx={{ p: 1.5 }}>
                {Object.entries(result.total_detections).length === 0
                  ? <Typography color="text.secondary">No objects detected</Typography>
                  : Object.entries(result.total_detections)
                      .sort((a, b) => b[1] - a[1])
                      .map(([cls, count]) => (
                        <Box key={cls} sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                          <Typography variant="body2">{cls}</Typography>
                          <Chip label={count} size="small" />
                        </Box>
                      ))
                }
              </Paper>
            </Grid>
          </Grid>

          {/* Alerts */}
          {result.alerts.length > 0 && (
            <>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="subtitle2" gutterBottom>
                <WarningAmberIcon fontSize="small" sx={{ mr: 0.5, verticalAlign: "middle", color: "error.main" }} />
                Crowd Alerts
              </Typography>
              <Paper variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: "grey.50" }}>
                      <TableCell>Time</TableCell>
                      <TableCell>Frame</TableCell>
                      <TableCell>Detail</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {result.alerts.map((a, i) => (
                      <TableRow key={i} hover>
                        <TableCell>{a.time_sec}s</TableCell>
                        <TableCell>{a.frame}</TableCell>
                        <TableCell>{a.detail}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Paper>
            </>
          )}
        </Box>
      )}
    </Box>
  );
}
