import React, { useState } from 'react';

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [formData, setFormData] = useState({
    transaction_id: 'TXN-001',
    customer_id: 'CUST-123',
    amount_usd: 15000
  });

  const testAuthentication = async () => {
    setLoading(true);
    setResult(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/authenticate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          channel: 'wire_transfer',
          has_consent: true
        })
      });
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error('Auth failed:', err);
      setResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Sonotheia Unified Platform</h1>
      <p>Forensic Audio Authentication System</p>
      
      <div style={{ border: '1px solid #ccc', padding: '20px', marginTop: '20px' }}>
        <h2>Test Authentication</h2>
        
        <div style={{ marginBottom: '10px' }}>
          <label>Transaction ID: </label>
          <input
            type="text"
            value={formData.transaction_id}
            onChange={(e) => setFormData({...formData, transaction_id: e.target.value})}
          />
        </div>
        
        <div style={{ marginBottom: '10px' }}>
          <label>Customer ID: </label>
          <input
            type="text"
            value={formData.customer_id}
            onChange={(e) => setFormData({...formData, customer_id: e.target.value})}
          />
        </div>
        
        <div style={{ marginBottom: '10px' }}>
          <label>Amount (USD): </label>
          <input
            type="number"
            value={formData.amount_usd}
            onChange={(e) => setFormData({...formData, amount_usd: parseFloat(e.target.value)})}
          />
        </div>
        
        <button onClick={testAuthentication} disabled={loading}>
          {loading ? 'Processing...' : 'Authenticate Transaction'}
        </button>
        
        {result && (
          <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f0f0f0' }}>
            <h3>Result:</h3>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
