import React, { useState } from "react";
import {
  Box,
  TextField,
  Button,
  Grid,
  Typography,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
  Paper
} from "@mui/material";
import { Add as AddIcon, Remove as RemoveIcon } from "@mui/icons-material";

export default function SARGenerationForm({ onReportCreated, onCancel }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const [formData, setFormData] = useState({
    customer_name: "",
    customer_id: "",
    account_number: "",
    account_opened: "",
    occupation: "",
    suspicious_activity: "",
    start_date: "",
    end_date: "",
    count: 0,
    amount: 0,
    pattern: "",
    doc_id: `DOC-${Date.now()}`
  });

  const [redFlags, setRedFlags] = useState([""]);
  const [transactions, setTransactions] = useState([
    {
      transaction_id: "",
      date: "",
      type: "",
      amount: 0,
      destination: ""
    }
  ]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }));
  };

  const handleRedFlagChange = (index, value) => {
    const newRedFlags = [...redFlags];
    newRedFlags[index] = value;
    setRedFlags(newRedFlags);
  };

  const addRedFlag = () => {
    setRedFlags([...redFlags, ""]);
  };

  const removeRedFlag = (index) => {
    setRedFlags(redFlags.filter((_, i) => i !== index));
  };

  const handleTransactionChange = (index, field, value) => {
    const newTransactions = [...transactions];
    newTransactions[index][field] = value;
    setTransactions(newTransactions);
  };

  const addTransaction = () => {
    setTransactions([
      ...transactions,
      {
        transaction_id: "",
        date: "",
        type: "",
        amount: 0,
        destination: ""
      }
    ]);
  };

  const removeTransaction = (index) => {
    setTransactions(transactions.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const payload = {
        ...formData,
        count: parseInt(formData.count) || 0,
        amount: parseFloat(formData.amount) || 0,
        red_flags: redFlags.filter((flag) => flag.trim() !== ""),
        transactions: transactions.filter((tx) => tx.transaction_id.trim() !== "")
      };

      const response = await fetch("http://localhost:8000/api/sar/reports", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create SAR report");
      }

      const newReport = await response.json();
      setSuccess(true);
      
      // Notify parent component
      if (onReportCreated) {
        onReportCreated(newReport);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <Box sx={{ textAlign: "center", p: 3 }}>
        <Alert severity="success" sx={{ mb: 2 }}>
          SAR report created successfully!
        </Alert>
        <Button variant="contained" onClick={onCancel}>
          Close
        </Button>
      </Box>
    );
  }

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ pt: 2 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Typography variant="h6" gutterBottom>
        Customer Information
      </Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Customer Name"
            name="customer_name"
            value={formData.customer_name}
            onChange={handleInputChange}
            required
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Customer ID"
            name="customer_id"
            value={formData.customer_id}
            onChange={handleInputChange}
            required
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Account Number"
            name="account_number"
            value={formData.account_number}
            onChange={handleInputChange}
            required
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Account Opened"
            name="account_opened"
            type="date"
            value={formData.account_opened}
            onChange={handleInputChange}
            InputLabelProps={{ shrink: true }}
            required
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Occupation"
            name="occupation"
            value={formData.occupation}
            onChange={handleInputChange}
            required
          />
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>
        Suspicious Activity Details
      </Typography>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Suspicious Activity Description"
            name="suspicious_activity"
            value={formData.suspicious_activity}
            onChange={handleInputChange}
            multiline
            rows={2}
            required
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Start Date"
            name="start_date"
            type="date"
            value={formData.start_date}
            onChange={handleInputChange}
            InputLabelProps={{ shrink: true }}
            required
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="End Date"
            name="end_date"
            type="date"
            value={formData.end_date}
            onChange={handleInputChange}
            InputLabelProps={{ shrink: true }}
            required
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="Transaction Count"
            name="count"
            type="number"
            value={formData.count}
            onChange={handleInputChange}
            required
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="Total Amount"
            name="amount"
            type="number"
            value={formData.amount}
            onChange={handleInputChange}
            required
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <TextField
            fullWidth
            label="Pattern"
            name="pattern"
            value={formData.pattern}
            onChange={handleInputChange}
            placeholder="e.g., structuring pattern"
            required
          />
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>
        Red Flags
      </Typography>
      <Box sx={{ mb: 3 }}>
        {redFlags.map((flag, index) => (
          <Box key={index} sx={{ display: "flex", gap: 1, mb: 1 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Enter red flag..."
              value={flag}
              onChange={(e) => handleRedFlagChange(index, e.target.value)}
            />
            <IconButton
              color="error"
              onClick={() => removeRedFlag(index)}
              disabled={redFlags.length === 1}
            >
              <RemoveIcon />
            </IconButton>
          </Box>
        ))}
        <Button startIcon={<AddIcon />} onClick={addRedFlag} size="small">
          Add Red Flag
        </Button>
      </Box>

      <Typography variant="h6" gutterBottom>
        Transactions
      </Typography>
      <Box sx={{ mb: 3 }}>
        {transactions.map((tx, index) => (
          <Paper key={index} sx={{ p: 2, mb: 2, bgcolor: "background.default" }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Transaction ID"
                  value={tx.transaction_id}
                  onChange={(e) =>
                    handleTransactionChange(index, "transaction_id", e.target.value)
                  }
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  size="small"
                  label="Date"
                  type="date"
                  value={tx.date}
                  onChange={(e) => handleTransactionChange(index, "date", e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  size="small"
                  label="Type"
                  value={tx.type}
                  onChange={(e) => handleTransactionChange(index, "type", e.target.value)}
                  placeholder="e.g., deposit, wire_transfer"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  size="small"
                  label="Amount"
                  type="number"
                  value={tx.amount}
                  onChange={(e) => handleTransactionChange(index, "amount", e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  size="small"
                  label="Destination"
                  value={tx.destination}
                  onChange={(e) =>
                    handleTransactionChange(index, "destination", e.target.value)
                  }
                />
              </Grid>
              <Grid item xs={12}>
                <Button
                  startIcon={<RemoveIcon />}
                  onClick={() => removeTransaction(index)}
                  size="small"
                  color="error"
                  disabled={transactions.length === 1}
                >
                  Remove Transaction
                </Button>
              </Grid>
            </Grid>
          </Paper>
        ))}
        <Button startIcon={<AddIcon />} onClick={addTransaction} size="small">
          Add Transaction
        </Button>
      </Box>

      <Box sx={{ display: "flex", gap: 2, justifyContent: "flex-end", mt: 3 }}>
        <Button onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? "Creating..." : "Create SAR Report"}
        </Button>
      </Box>
    </Box>
  );
}
