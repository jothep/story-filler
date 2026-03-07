// src/components/ErrorMessage.jsx
// Reusable error message component with NES.css styling

import { useNavigate } from 'react-router-dom';

function ErrorMessage({ error, onRetry }) {
  const navigate = useNavigate();

  const errorMessage = typeof error === 'string' ? error : error?.message || 'An unexpected error occurred';

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '50vh',
      padding: '2rem'
    }}>
      <div className="nes-container is-rounded is-dark" style={{ textAlign: 'center', maxWidth: '500px' }}>
        <h2 style={{ color: '#f7d51d', marginBottom: '1rem' }}>⚠️ Oops!</h2>
        <p style={{ marginBottom: '1.5rem', color: 'white' }}>
          {errorMessage}
        </p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          {onRetry && (
            <button
              type="button"
              className="nes-btn is-primary"
              onClick={onRetry}
            >
              Try Again
            </button>
          )}
          <button
            type="button"
            className="nes-btn"
            onClick={() => navigate('/')}
          >
            Back to Menu
          </button>
        </div>
      </div>
    </div>
  );
}

export default ErrorMessage;
