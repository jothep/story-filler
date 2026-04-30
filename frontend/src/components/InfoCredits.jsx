// src/components/InfoCredits.jsx
// Info & Credits modal component with pixel art style
import { useState } from 'react';
import { createPortal } from 'react-dom';
import { CREDITS_CONTENT } from '../constants/credits';
import {
  buttonStyles,
  buttonHoverStyles,
  modalOverlayStyles,
  modalContentStyles,
  closeButtonStyles,
  closeButtonHoverStyles,
  titleStyles,
  sectionStyles,
  sectionTitleStyles,
  linkStyles,
} from './InfoCredits.styles';

function InfoCredits() {
  const [isOpen, setIsOpen] = useState(false);
  const [isButtonHovered, setIsButtonHovered] = useState(false);
  const [isCloseHovered, setIsCloseHovered] = useState(false);

  const openModal = () => setIsOpen(true);
  const closeModal = () => setIsOpen(false);

  // Close on Escape key
  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      closeModal();
    }
  };

  const modalContent = isOpen && (
    <div
      style={modalOverlayStyles}
      onClick={closeModal}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      tabIndex={-1}
    >
      <div style={modalContentStyles} onClick={(e) => e.stopPropagation()}>
        <button
          onClick={closeModal}
          style={{
            ...closeButtonStyles,
            ...(isCloseHovered ? closeButtonHoverStyles : {}),
          }}
          onMouseEnter={() => setIsCloseHovered(true)}
          onMouseLeave={() => setIsCloseHovered(false)}
          aria-label="Close modal"
        >
          ✕
        </button>

        <h2 id="modal-title" style={titleStyles}>
          About &amp; Credits
        </h2>

        {/* Author Section */}
        <div style={sectionStyles}>
          <div style={sectionTitleStyles}>Author</div>
          <p>{CREDITS_CONTENT.author.name}</p>
        </div>

        {/* Material Credits Section */}
        <div style={sectionStyles}>
          <div style={sectionTitleStyles}>Material Credits</div>

          <div style={{ marginBottom: '1rem' }}>
            <strong>{CREDITS_CONTENT.materials.bgm.label}</strong>
            <br />
            <span>{CREDITS_CONTENT.materials.bgm.credit}</span>
          </div>

          <div>
            <strong>{CREDITS_CONTENT.materials.graphics.label}</strong>
            <br />
            {CREDITS_CONTENT.materials.graphics.items.map((item, index) => (
              <span key={index}>
                • {item.label}:{' '}
                {item.url ? (
                  <a
                    href={item.url}
                    style={linkStyles}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {item.credit}
                  </a>
                ) : (
                  item.credit
                )}
                <br />
              </span>
            ))}
          </div>
        </div>

        {/* Disclaimer Section */}
        <div style={sectionStyles}>
          <div style={sectionTitleStyles}>Disclaimer</div>
          <p style={{ fontSize: '0.8rem', lineHeight: '1.6' }}>
            {CREDITS_CONTENT.disclaimer.text}{' '}
            <a href={`mailto:${CREDITS_CONTENT.disclaimer.email}`} style={linkStyles}>
              {CREDITS_CONTENT.disclaimer.email}
            </a>.
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <button
        onClick={openModal}
        style={{
          ...buttonStyles,
          ...(isButtonHovered ? buttonHoverStyles : {}),
        }}
        onMouseEnter={() => setIsButtonHovered(true)}
        onMouseLeave={() => setIsButtonHovered(false)}
        aria-label="Open credits information"
      >
        INFO / CREDITS
      </button>

      {modalContent && createPortal(modalContent, document.body)}
    </>
  );
}

export default InfoCredits;
