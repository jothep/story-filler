// src/pages/Congratulations.jsx
// Renders a simple congratulatory page displayed when a user finishes a story.
// Provides a "Back to Menu" link to navigate back to the root route.
import { Link } from 'react-router-dom';

function Congratulations() {
  return (
    <div style={{ padding: '4rem', textAlign: 'center' }}>
      <div className="nes-container with-title is-centered">
        <p className="title">Story Complete!</p>
        <h1 style={{ marginBottom: '2rem' }}>Congratulations!</h1>
        <i className="nes-icon is-large star"></i>
        <i className="nes-icon is-large star"></i>
        <i className="nes-icon is-large star"></i>
        <p style={{ marginTop: '2rem' }}>You have successfully completed the story.</p>
        <Link
          to="/"
          className="nes-btn is-primary"
          style={{ marginTop: '3rem' }}
        >
          Back to Menu
        </Link>
      </div>
    </div>
  );
}

export default Congratulations;