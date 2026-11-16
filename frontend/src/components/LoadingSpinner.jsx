import PropTypes from 'prop-types';

export const COLD_START_NOTE =
  'Waking up the free server. First load can take up to 30s.';

/** @param {{message?: string}} props */
function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '50vh',
        padding: '2rem',
      }}
    >
      <div
        className="nes-container is-rounded"
        style={{ textAlign: 'center', maxWidth: '400px' }}
      >
        <p style={{ marginBottom: '1rem' }}>{message}</p>
        <div
          style={{
            display: 'inline-block',
            width: '40px',
            height: '40px',
            border: '4px solid #209cee',
            borderTopColor: 'transparent',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }}
        />
        <p
          style={{
            marginTop: '1rem',
            marginBottom: 0,
            fontSize: '0.7rem',
            lineHeight: 1.6,
          }}
        >
          {COLD_START_NOTE}
        </p>
      </div>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

LoadingSpinner.propTypes = {
  message: PropTypes.string,
};

export default LoadingSpinner;
