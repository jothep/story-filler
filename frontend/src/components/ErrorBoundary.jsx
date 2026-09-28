// src/components/ErrorBoundary.jsx
// React Error Boundary to catch JavaScript errors in component tree

import { Component } from 'react';
import PropTypes from 'prop-types';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  // eslint-disable-next-line no-unused-vars
  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details to console
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    this.setState({
      error,
      errorInfo
    });

    // You can also log to an error reporting service here
    // logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    // Navigate to home or reset app state
    window.location.href = import.meta.env.BASE_URL;
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '2rem',
          backgroundColor: '#212529'
        }}>
          <div className="nes-container is-rounded is-dark" style={{ textAlign: 'center', maxWidth: '600px' }}>
            <h1 style={{ color: '#f7d51d', marginBottom: '1rem' }}>💥 Something went wrong</h1>
            <p style={{ marginBottom: '1rem', color: 'white' }}>
              The application encountered an unexpected error. This has been logged and we&apos;ll look into it.
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details style={{
                marginTop: '1.5rem',
                textAlign: 'left',
                backgroundColor: '#000',
                padding: '1rem',
                borderRadius: '4px',
                maxHeight: '200px',
                overflow: 'auto'
              }}>
                <summary style={{ cursor: 'pointer', color: '#f7d51d' }}>Error Details (Dev Mode)</summary>
                <pre style={{
                  margin: '1rem 0 0 0',
                  fontSize: '0.75rem',
                  color: '#ff6b6b',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}>
                  {this.state.error.toString()}
                  {this.state.errorInfo && this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}

            <div style={{ marginTop: '2rem' }}>
              <button
                type="button"
                className="nes-btn is-primary"
                onClick={this.handleReset}
              >
                Return to Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
};

export default ErrorBoundary;
