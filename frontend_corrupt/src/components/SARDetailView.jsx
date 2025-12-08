import React from "react";
import {
  Box,
  Typography,
  Paper,
  Divider,
  Chip,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

export default function SARDetailView({ report }) {
  if (!report) return null;

  const { context, narrative, quality_score, ready_for_filing } = report;
  const { risk_intelligence, investigation_details } = context;

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

  return (
    <Box>
      {/* Header Section */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="h6">{report.sar_id}</Typography>
            <Typography variant="body2" color="text.secondary">
              Customer: {context.customer_name} ({context.customer_id})
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Account: {context.account_number}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", justifyContent: "flex-end" }}>
              <Chip
                label={context.filing_status.toUpperCase()}
                color={getStatusColor(context.filing_status)}
              />
              <Chip label={`Priority: ${context.priority_level}`} />
              {ready_for_filing ? (
                <Chip label="Ready for Filing" color="success" />
              ) : (
                <Chip label="Needs Review" color="warning" />
              )}
              <Chip label={`Quality: ${(quality_score * 100).toFixed(0)}%`} variant="outlined" />
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Risk Intelligence Section */}
      {risk_intelligence && (
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">Risk Intelligence Analysis</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, textAlign: "center", bgcolor: "background.default" }}>
                  <Typography variant="h3" color={getRiskLevelColor(risk_intelligence.risk_level)}>
                    {(risk_intelligence.overall_risk_score * 100).toFixed(0)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Risk Score
                  </Typography>
                  <Chip
                    label={risk_intelligence.risk_level}
                    color={getRiskLevelColor(risk_intelligence.risk_level)}
                    sx={{ mt: 1 }}
                  />
                </Paper>
              </Grid>
              <Grid item xs={12} md={8}>
                <Typography variant="subtitle2" gutterBottom>
                  Pattern Analysis
                </Typography>
                <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 2 }}>
                  {Object.entries(risk_intelligence.pattern_analysis).map(([key, value]) => (
                    <Chip
                      key={key}
                      label={`${key.replace(/_/g, " ")}: ${
                        typeof value === "number" ? value.toFixed(2) : value
                      }`}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                </Box>

                {risk_intelligence.behavioral_anomalies.length > 0 && (
                  <>
                    <Typography variant="subtitle2" gutterBottom>
                      Behavioral Anomalies
                    </Typography>
                    <ul style={{ marginTop: 0 }}>
                      {risk_intelligence.behavioral_anomalies.map((anomaly, idx) => (
                        <li key={idx}>
                          <Typography variant="body2">{anomaly}</Typography>
                        </li>
                      ))}
                    </ul>
                  </>
                )}

                {risk_intelligence.geographic_risks.length > 0 && (
                  <>
                    <Typography variant="subtitle2" gutterBottom>
                      Geographic Risks
                    </Typography>
                    <ul style={{ marginTop: 0 }}>
                      {risk_intelligence.geographic_risks.map((risk, idx) => (
                        <li key={idx}>
                          <Typography variant="body2">{risk}</Typography>
                        </li>
                      ))}
                    </ul>
                  </>
                )}

                {risk_intelligence.similarity_to_known_schemes.length > 0 && (
                  <>
                    <Typography variant="subtitle2" gutterBottom sx={{ mt: 1 }}>
                      Similar Known Schemes
                    </Typography>
                    {risk_intelligence.similarity_to_known_schemes.map((scheme, idx) => (
                      <Paper key={idx} sx={{ p: 1, mb: 1, bgcolor: "background.default" }}>
                        <Typography variant="body2" fontWeight="bold">
                          {scheme.name} ({(scheme.similarity_score * 100).toFixed(0)}% match)
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {scheme.description}
                        </Typography>
                      </Paper>
                    ))}
                  </>
                )}
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Suspicious Activity Summary */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Suspicious Activity Summary</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2">
                <strong>Activity Type:</strong> {context.suspicious_activity}
              </Typography>
              <Typography variant="body2">
                <strong>Pattern:</strong> {context.pattern}
              </Typography>
              <Typography variant="body2">
                <strong>Period:</strong> {context.start_date} to {context.end_date}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2">
                <strong>Transaction Count:</strong> {context.count}
              </Typography>
              <Typography variant="body2">
                <strong>Total Amount:</strong> ${context.amount.toLocaleString()}
              </Typography>
              <Typography variant="body2">
                <strong>Occupation:</strong> {context.occupation}
              </Typography>
            </Grid>
          </Grid>

          <Divider sx={{ my: 2 }} />

          <Typography variant="subtitle2" gutterBottom>
            Red Flags
          </Typography>
          <ul style={{ marginTop: 0 }}>
            {context.red_flags.map((flag, idx) => (
              <li key={idx}>
                <Typography variant="body2">{flag}</Typography>
              </li>
            ))}
          </ul>
        </AccordionDetails>
      </Accordion>

      {/* Transaction Details */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Transaction Details ({context.transactions.length})</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Transaction ID</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell align="right">Amount</TableCell>
                  <TableCell>Destination</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {context.transactions.map((tx) => (
                  <TableRow key={tx.transaction_id}>
                    <TableCell>{tx.transaction_id}</TableCell>
                    <TableCell>{tx.date}</TableCell>
                    <TableCell>{tx.type}</TableCell>
                    <TableCell align="right">
                      ${tx.amount.toLocaleString()} {tx.currency}
                    </TableCell>
                    <TableCell>{tx.destination || "-"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>

      {/* Investigation Details */}
      {investigation_details && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">Investigation Details</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2">
              <strong>Investigation ID:</strong> {investigation_details.investigation_id}
            </Typography>
            <Typography variant="body2">
              <strong>Investigator:</strong> {investigation_details.investigator_name},{" "}
              {investigation_details.investigator_title}
            </Typography>
            <Typography variant="body2">
              <strong>Start Date:</strong> {investigation_details.investigation_start_date}
            </Typography>
            <Typography variant="body2">
              <strong>Customer Contacted:</strong>{" "}
              {investigation_details.customer_contacted ? "Yes" : "No"}
            </Typography>
            {investigation_details.customer_response && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                <strong>Customer Response:</strong> {investigation_details.customer_response}
              </Typography>
            )}
          </AccordionDetails>
        </Accordion>
      )}

      {/* Full Narrative */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Full SAR Narrative</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Paper sx={{ p: 2, bgcolor: "background.default" }}>
            <Typography
              variant="body2"
              component="pre"
              sx={{
                whiteSpace: "pre-wrap",
                fontFamily: "monospace",
                fontSize: "0.875rem"
              }}
            >
              {narrative}
            </Typography>
          </Paper>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
}
