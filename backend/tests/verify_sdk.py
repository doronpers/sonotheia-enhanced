import sys
import os
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.sdk.client import SonotheiaClient

def test_sdk_initialization():
    print("Testing SDK Initialization...")
    client = SonotheiaClient(base_url="http://test.com", api_key="test-key")
    assert client.base_url == "http://test.com"
    assert client.session.headers["X-API-Key"] == "test-key"
    print("SDK Initialization Passed.")

@patch('requests.Session.post')
def test_sdk_authentication(mock_post):
    print("Testing SDK Authentication...")
    client = SonotheiaClient(base_url="http://test.com", api_key="test-key")
    
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "success"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    result = client.authenticate(
        transaction_id="TX-123",
        customer_id="CUST-1",
        amount_usd=100.0
    )
    
    assert result["status"] == "success"
    mock_post.assert_called_once()
    print("SDK Authentication Passed.")

if __name__ == "__main__":
    try:
        test_sdk_initialization()
        test_sdk_authentication()
        print("\nAll SDK tests passed!")
    except Exception as e:
        print(f"\nSDK Verification Failed: {e}")
        sys.exit(1)
