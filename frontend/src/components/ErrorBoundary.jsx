import { Component } from 'react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary" role="alert" aria-live="assertive">
          <div className="section-container">
            <h2 className="section-title">Something went wrong</h2>
            <p className="section-text">
              We encountered an unexpected error. Please try refreshing the page.
            </p>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="error-details">
                <summary>Error details (development only)</summary>
                <pre className="error-stack">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
            <div className="cta-buttons">
              <button 
                className="tactical-button" 
                onClick={this.handleReset}
                aria-label="Try to recover from error"
              >
                [ TRY AGAIN ]
              </button>
              <button 
                className="tactical-button secondary" 
                onClick={() => window.location.reload()}
                aria-label="Reload the page"
              >
                [ RELOAD PAGE ]
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

