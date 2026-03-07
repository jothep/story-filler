// src/components/LoadingSpinner.jsx
// Reusable loading spinner component with NES.css styling

function LoadingSpinner({ message = "Loading..." }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '50vh',
      padding: '2rem'
    }}>
      <div className="nes-container is-rounded" style={{ textAlign: 'center', maxWidth: '400px' }}>
        <p style={{ marginBottom: '1rem' }}>{message}</p>
        <div style={{
          display: 'inline-block',
          width: '40px',
          height: '40px',
          border: '4px solid #209cee',
          borderTopColor: 'transparent',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
      </div>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default LoadingSpinner;
