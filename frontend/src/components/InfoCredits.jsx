// src/components/InfoCredits.jsx
// Info & Credits modal component with pixel art style
import { useState } from 'react';

const buttonStyles = {
  position: 'relative',
  zIndex: 10,
  padding: '0.5rem 1rem',
  fontSize: '0.75rem',
  cursor: 'pointer',
  background: '#8B4513',
  border: '3px solid #654321',
  color: '#FFE4B5',
  textShadow: '1px 1px #000',
  fontFamily: '"Press Start 2P", cursive',
  letterSpacing: '1px',
};

const modalOverlayStyles = {
  position: 'fixed',
  top: 0,
  left: 0,
  width: '100%',
  height: '100%',
  backgroundColor: 'rgba(0, 0, 0, 0.7)',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 99999,
};

const modalContentStyles = {
  position: 'relative',
  maxWidth: '600px',
  width: '90%',
  maxHeight: '80vh',
  overflowY: 'auto',
  padding: '2rem',
  background: '#D2B48C',
  border: '4px solid #654321',
  boxShadow: '0 0 0 2px #8B4513, 4px 4px 0 4px #000',
  zIndex: 100000,
};

const closeButtonStyles = {
  position: 'absolute',
  top: '0.5rem',
  right: '0.5rem',
  width: '32px',
  height: '32px',
  background: '#D2691E',
  border: '2px solid #654321',
  color: '#000',
  fontSize: '1rem',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontFamily: 'monospace',
  fontWeight: 'bold',
};

const titleStyles = {
  textAlign: 'center',
  fontSize: '1.2rem',
  marginBottom: '1.5rem',
  color: '#654321',
  textShadow: '2px 2px #FFE4B5',
};

const sectionStyles = {
  marginBottom: '1.5rem',
  lineHeight: '1.8',
  fontSize: '0.9rem',
  color: '#333',
};

const sectionTitleStyles = {
  fontSize: '1rem',
  fontWeight: 'bold',
  marginBottom: '0.5rem',
  color: '#8B4513',
};

const linkStyles = {
  color: '#4169E1',
  textDecoration: 'underline',
};

function InfoCredits() {
  const [isOpen, setIsOpen] = useState(false);

  const openModal = () => setIsOpen(true);
  const closeModal = () => setIsOpen(false);

  return (
    <>
      <button
        onClick={openModal}
        style={buttonStyles}
        onMouseOver={(e) => {
          e.currentTarget.style.background = '#A0522D';
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.background = '#8B4513';
        }}
      >
        INFO / CREDITS
      </button>

      {isOpen && (
        <div style={modalOverlayStyles} onClick={closeModal}>
          <div style={modalContentStyles} onClick={(e) => e.stopPropagation()}>
            <button
              onClick={closeModal}
              style={closeButtonStyles}
              onMouseOver={(e) => {
                e.currentTarget.style.background = '#CD853F';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = '#D2691E';
              }}
            >
              ✕
            </button>

            <h2 style={titleStyles}>About &amp; Credits</h2>

            <div style={sectionStyles}>
              <div style={sectionTitleStyles}>Author</div>
              <p>Xiang Zhu</p>
            </div>

            <div style={sectionStyles}>
              <div style={sectionTitleStyles}>Material Credits</div>

              <div style={{ marginBottom: '1rem' }}>
                <strong>Background Music:</strong>
                <br />
                <span>Dvořák - Humoresque Op.101 No.7</span>
              </div>

              <div>
                <strong>Graphics &amp; UI Assets:</strong>
                <br />
                <span>• Background animations: itch.io</span>
                <br />
                <span>• Logo design: Gemini</span>
                <br />
                <span>• UI framework: <a href="https://nostalgic-css.github.io/NES.css/" style={linkStyles} target="_blank" rel="noopener noreferrer">NES.css</a></span>
              </div>
            </div>

            <div style={sectionStyles}>
              <div style={sectionTitleStyles}>Disclaimer</div>
              <p style={{ fontSize: '0.8rem', lineHeight: '1.6' }}>
                This application is strictly for personal coding practice and demonstration.
                If you are the copyright owner of any materials and wish for them to be removed,
                please contact me via email at{' '}
                <a href="mailto:shelldry325@gmail.com" style={linkStyles}>
                  shelldry325@gmail.com
                </a>.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default InfoCredits;
