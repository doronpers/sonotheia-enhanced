import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Tabs,
  Tab,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Card,
  CardContent,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  Alert,
  TextField,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Save as SaveIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import axios from 'axios';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`dashboard-tabpanel-${index}`}
      aria-labelledby={`dashboard-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function Dashboard() {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [testResults, setTestResults] = useState([]);
  const [moduleParams, setModuleParams] = useState({});
  const [systemStatus, setSystemStatus] = useState({});
  const [error, setError] = useState(null);

  const apiBase = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, paramsRes, resultsRes] = await Promise.all([
        axios.get(`${apiBase}/api/dashboard/status`),
        axios.get(`${apiBase}/api/dashboard/module-params`),
        axios.get(`${apiBase}/api/dashboard/test-results`),
      ]);

      setSystemStatus(statusRes.data);
      setModuleParams(paramsRes.data);
      setTestResults(resultsRes.data);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleRunTests = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${apiBase}/api/dashboard/run-tests`);
      setTestResults(response.data.results);
      await loadDashboardData();
    } catch (err) {
      console.error('Failed to run tests:', err);
      setError(err.message || 'Failed to run tests');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveParams = async () => {
    setLoading(true);
    setError(null);
    try {
      await axios.post(`${apiBase}/api/dashboard/module-params`, moduleParams);
      alert('Parameters saved successfully!');
    } catch (err) {
      console.error('Failed to save parameters:', err);
      setError(err.message || 'Failed to save parameters');
    } finally {
      setLoading(false);
    }
  };

  const handleExportResults = () => {
    const dataStr = JSON.stringify(testResults, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `test-results-${new Date().toISOString()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleParamChange = (module, param, value) => {
    setModuleParams((prev) => ({
      ...prev,
      [module]: {
        ...prev[module],
        [param]: value,
      },
    }));
  };

  const getStatusColor = (status) => {
    const colors = {
      pass: 'success',
      fail: 'error',
      warn: 'warning',
      running: 'info',
      pending: 'default',
    };
    return colors[status?.toLowerCase()] || 'default';
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h3" gutterBottom>
            Test & Results Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Comprehensive view of module tests, parameters, and authentication results
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadDashboardData}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExportResults}
            disabled={testResults.length === 0}
          >
            Export
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* System Status Overview */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Tests
              </Typography>
              <Typography variant="h4">
                {systemStatus.totalTests || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Passed
              </Typography>
              <Typography variant="h4" color="success.main">
                {systemStatus.passedTests || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Failed
              </Typography>
              <Typography variant="h4" color="error.main">
                {systemStatus.failedTests || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Uptime
              </Typography>
              <Typography variant="h4" color="info.main">
                {systemStatus.uptime || '99.9%'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={(e, newValue) => setTabValue(newValue)}
          aria-label="dashboard tabs"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Test Results" icon={<PlayIcon />} iconPosition="start" />
          <Tab label="Module Parameters" icon={<SettingsIcon />} iconPosition="start" />
          <Tab label="Authentication History" />
          <Tab label="SAR Reports" />
        </Tabs>

        {/* Test Results Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="h6">Test Execution Results</Typography>
            <Button
              variant="contained"
              startIcon={<PlayIcon />}
              onClick={handleRunTests}
              disabled={loading}
            >
              {loading ? 'Running...' : 'Run All Tests'}
            </Button>
          </Box>

          {loading && tabValue === 0 ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Test Name</TableCell>
                    <TableCell>Module</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Duration</TableCell>
                    <TableCell>Score</TableCell>
                    <TableCell>Details</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {testResults.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        <Typography color="text.secondary">
                          No test results available. Click "Run All Tests" to start.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    testResults.map((test, idx) => (
                      <TableRow key={idx} hover>
                        <TableCell>{test.name}</TableCell>
                        <TableCell>{test.module}</TableCell>
                        <TableCell>
                          <Chip
                            label={test.status}
                            color={getStatusColor(test.status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{test.duration || 'N/A'}</TableCell>
                        <TableCell>
                          {test.score !== undefined ? test.score.toFixed(3) : 'N/A'}
                        </TableCell>
                        <TableCell>{test.details || '-'}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>

        {/* Module Parameters Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="h6">Module Configuration</Typography>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSaveParams}
              disabled={loading}
            >
              Save Parameters
            </Button>
          </Box>

          {loading && tabValue === 1 ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            Object.entries(moduleParams).map(([moduleName, params]) => (
              <Accordion key={moduleName} defaultExpanded={moduleName === 'voice'}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">{moduleName.toUpperCase()} Module</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    {Object.entries(params).map(([paramName, paramValue]) => (
                      <Grid item xs={12} md={6} key={paramName}>
                        <TextField
                          fullWidth
                          label={paramName.replace(/_/g, ' ').toUpperCase()}
                          value={paramValue}
                          onChange={(e) =>
                            handleParamChange(moduleName, paramName, e.target.value)
                          }
                          type={typeof paramValue === 'number' ? 'number' : 'text'}
                          variant="outlined"
                          helperText={`Current value: ${paramValue}`}
                        />
                      </Grid>
                    ))}
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))
          )}
        </TabPanel>

        {/* Authentication History Tab */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Recent Authentication Requests
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Transaction ID</TableCell>
                  <TableCell>Customer ID</TableCell>
                  <TableCell>Amount</TableCell>
                  <TableCell>Decision</TableCell>
                  <TableCell>Risk Level</TableCell>
                  <TableCell>Timestamp</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="text.secondary">
                      Authentication history will be displayed here
                    </Typography>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* SAR Reports Tab */}
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom>
            Suspicious Activity Reports
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Report ID</TableCell>
                  <TableCell>Customer</TableCell>
                  <TableCell>Activity Type</TableCell>
                  <TableCell>Amount</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="text.secondary">
                      SAR reports will be displayed here
                    </Typography>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
      </Paper>
    </Container>
  );
}
