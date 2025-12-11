import React, { useState, useEffect } from "react";
import {
  Box,
  Paper,
  Tabs,
  Tab,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert
} from "@mui/material";
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon
} from "@mui/icons-material";
import SARDetailView from "./SARDetailView";
import SARGenerationForm from "./SARGenerationForm";
import SARAnalyticsDashboard from "./SARAnalyticsDashboard";

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function SARReportsTab() {
  const [tabValue, setTabValue] = useState(0);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    loadReports();
  }, [statusFilter]);

  const loadReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = statusFilter
        ? `http://localhost:8000/api/sar/reports?status=${statusFilter}`
        : "http://localhost:8000/api/sar/reports";
      const response = await fetch(url);
      if (!response.ok) throw new Error("Failed to load reports");
      const data = await response.json();
      setReports(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleViewReport = (report) => {
    setSelectedReport(report);
    setDetailDialogOpen(true);
  };

  const handleExportReport = async (sarId, format = "txt") => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/sar/reports/${sarId}/export?format=${format}`
      );
      if (!response.ok) throw new Error("Failed to export report");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${sarId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleReportCreated = (newReport) => {
    setReports([newReport, ...reports]);
    setCreateDialogOpen(false);
  };

  const getStatusColor = (status) => {
    const colors = {
      draft: "default",
      pending_review: "warning",
      approved: "info",
      filed: "success",
      rejected: "error"
    };
    return colors[status] || "default";
  };

  const getRiskLevelColor = (level) => {
    const colors = {
      LOW: "success",
      MEDIUM: "warning",
      HIGH: "error",
      CRITICAL: "error"
    };
    return colors[level] || "default";
  };

  const filteredReports = reports.filter((report) => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      report.sar_id.toLowerCase().includes(searchLower) ||
      report.context.customer_name.toLowerCase().includes(searchLower) ||
      report.context.customer_id.toLowerCase().includes(searchLower)
    );
  });

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 2 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Reports List" />
          <Tab label="Analytics" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        {/* Header with search and filters */}
        <Box sx={{ mb: 3, display: "flex", gap: 2, alignItems: "center" }}>
          <TextField
            placeholder="Search by ID, customer name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            size="small"
            sx={{ flexGrow: 1 }}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: "action.active" }} />
            }}
          />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="draft">Draft</MenuItem>
              <MenuItem value="pending_review">Pending Review</MenuItem>
              <MenuItem value="approved">Approved</MenuItem>
              <MenuItem value="filed">Filed</MenuItem>
              <MenuItem value="rejected">Rejected</MenuItem>
            </Select>
          </FormControl>
          <IconButton onClick={loadReports} color="primary">
            <RefreshIcon />
          </IconButton>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create New SAR
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
            <CircularProgress />
          </Box>
        ) : filteredReports.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: "center" }}>
            <Typography variant="h6" color="text.secondary">
              No SAR reports found
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
              sx={{ mt: 2 }}
            >
              Create First SAR Report
            </Button>
          </Paper>
        ) : (
          <Grid container spacing={2}>
            {filteredReports.map((report) => (
              <Grid item xs={12} sm={6} md={4} key={report.sar_id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                      <Typography variant="h6" sx={{ fontSize: "1rem" }}>
                        {report.sar_id}
                      </Typography>
                      <Chip
                        label={report.context.filing_status.toUpperCase()}
                        color={getStatusColor(report.context.filing_status)}
                        size="small"
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {report.context.customer_name} ({report.context.customer_id})
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      Amount: ${report.context.amount.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      Transactions: {report.context.count}
                    </Typography>
                    {report.context.risk_intelligence && (
                      <Box sx={{ mt: 1 }}>
                        <Chip
                          label={`Risk: ${report.context.risk_intelligence.risk_level}`}
                          color={getRiskLevelColor(report.context.risk_intelligence.risk_level)}
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        <Chip
                          label={`Score: ${(
                            report.context.risk_intelligence.overall_risk_score * 100
                          ).toFixed(0)}%`}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    )}
                    <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 1 }}>
                      Generated: {new Date(report.generated_at).toLocaleDateString()}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button
                      size="small"
                      startIcon={<ViewIcon />}
                      onClick={() => handleViewReport(report)}
                    >
                      View
                    </Button>
                    <Button
                      size="small"
                      startIcon={<DownloadIcon />}
                      onClick={() => handleExportReport(report.sar_id, "txt")}
                    >
                      Export
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <SARAnalyticsDashboard reports={reports} />
      </TabPanel>

      {/* Detail View Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>SAR Report Details</DialogTitle>
        <DialogContent>
          {selectedReport && <SARDetailView report={selectedReport} />}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => handleExportReport(selectedReport?.sar_id, "txt")}>
            Export TXT
          </Button>
          <Button onClick={() => handleExportReport(selectedReport?.sar_id, "json")}>
            Export JSON
          </Button>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Create New SAR Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New SAR Report</DialogTitle>
        <DialogContent>
          <SARGenerationForm
            onReportCreated={handleReportCreated}
            onCancel={() => setCreateDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
}
