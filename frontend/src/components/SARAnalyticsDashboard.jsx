import React from "react";
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent
} from "@mui/material";
import {
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  Assessment as AssessmentIcon,
  CheckCircle as CheckCircleIcon
} from "@mui/icons-material";

export default function SARAnalyticsDashboard({ reports }) {
  if (!reports || reports.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: "center" }}>
        <Typography variant="h6" color="text.secondary">
          No data available for analytics
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Create some SAR reports to see analytics here.
        </Typography>
      </Paper>
    );
  }

  // Calculate statistics
  const totalReports = reports.length;
  const filedReports = reports.filter((r) => r.context.filing_status === "filed").length;
  const draftReports = reports.filter((r) => r.context.filing_status === "draft").length;
  const pendingReports = reports.filter(
    (r) => r.context.filing_status === "pending_review"
  ).length;

  const totalAmount = reports.reduce((sum, r) => sum + r.context.amount, 0);
  const totalTransactions = reports.reduce((sum, r) => sum + r.context.count, 0);

  const highRiskReports = reports.filter(
    (r) =>
      r.context.risk_intelligence &&
      (r.context.risk_intelligence.risk_level === "HIGH" ||
        r.context.risk_intelligence.risk_level === "CRITICAL")
  ).length;

  const avgRiskScore =
    reports.reduce((sum, r) => {
      return sum + (r.context.risk_intelligence?.overall_risk_score || 0);
    }, 0) / reports.length;

  // Group by risk level
  const riskLevelCounts = reports.reduce((acc, r) => {
    const level = r.context.risk_intelligence?.risk_level || "UNKNOWN";
    acc[level] = (acc[level] || 0) + 1;
    return acc;
  }, {});

  // Top red flags
  const redFlagCounts = {};
  reports.forEach((r) => {
    r.context.red_flags.forEach((flag) => {
      redFlagCounts[flag] = (redFlagCounts[flag] || 0) + 1;
    });
  });
  const topRedFlags = Object.entries(redFlagCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        SAR Analytics Dashboard
      </Typography>

      {/* Key Metrics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <Box>
                  <Typography variant="h4">{totalReports}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Reports
                  </Typography>
                </Box>
                <AssessmentIcon sx={{ fontSize: 40, color: "primary.main" }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <Box>
                  <Typography variant="h4">{highRiskReports}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    High Risk
                  </Typography>
                </Box>
                <WarningIcon sx={{ fontSize: 40, color: "error.main" }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <Box>
                  <Typography variant="h4">${(totalAmount / 1000).toFixed(0)}K</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Amount
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 40, color: "success.main" }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <Box>
                  <Typography variant="h4">{filedReports}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Filed Reports
                  </Typography>
                </Box>
                <CheckCircleIcon sx={{ fontSize: 40, color: "info.main" }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        {/* Filing Status */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Filing Status
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                <Typography variant="body2">Draft</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {draftReports}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                <Typography variant="body2">Pending Review</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {pendingReports}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                <Typography variant="body2">Filed</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {filedReports}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Risk Distribution */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Risk Level Distribution
            </Typography>
            <Box sx={{ mt: 2 }}>
              {Object.entries(riskLevelCounts).map(([level, count]) => (
                <Box key={level} sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                  <Typography variant="body2">{level}</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {count} ({((count / totalReports) * 100).toFixed(0)}%)
                  </Typography>
                </Box>
              ))}
            </Box>
            <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: "divider" }}>
              <Typography variant="body2" color="text.secondary">
                Average Risk Score: {(avgRiskScore * 100).toFixed(1)}%
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Top Red Flags */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Top Red Flags
            </Typography>
            <Box sx={{ mt: 2 }}>
              {topRedFlags.map(([flag, count], index) => (
                <Box
                  key={index}
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    mb: 1,
                    pb: 1,
                    borderBottom: index < topRedFlags.length - 1 ? 1 : 0,
                    borderColor: "divider"
                  }}
                >
                  <Typography variant="body2">{flag}</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {count} reports
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Transaction Summary */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Transaction Summary
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                <Typography variant="body2">Total Transactions</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {totalTransactions}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                <Typography variant="body2">Avg per Report</Typography>
                <Typography variant="body2" fontWeight="bold">
                  {(totalTransactions / totalReports).toFixed(1)}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                <Typography variant="body2">Total Value</Typography>
                <Typography variant="body2" fontWeight="bold">
                  ${totalAmount.toLocaleString()}
                </Typography>
              </Box>
              <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                <Typography variant="body2">Avg Value per Report</Typography>
                <Typography variant="body2" fontWeight="bold">
                  ${(totalAmount / totalReports).toLocaleString(undefined, {
                    maximumFractionDigits: 0
                  })}
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <Box sx={{ mt: 2 }}>
              {reports.slice(0, 5).map((report, index) => (
                <Box
                  key={index}
                  sx={{
                    mb: 1,
                    pb: 1,
                    borderBottom: index < 4 ? 1 : 0,
                    borderColor: "divider"
                  }}
                >
                  <Typography variant="body2" fontWeight="bold">
                    {report.sar_id}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {report.context.customer_name} - $
                    {report.context.amount.toLocaleString()}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
