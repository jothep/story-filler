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

  /** @param {import('react').KeyboardEvent<HTMLDivElement>} e */
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

        <div style={sectionStyles}>
          {CREDITS_CONTENT.about.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </div>

        <div style={sectionStyles}>
          <h3 style={sectionTitleStyles}>Author</h3>
          <p>
            Created and maintained by{' '}
            <strong>{CREDITS_CONTENT.author.name}</strong>.
          </p>
          <p>
            Explore the architecture, engineering decisions and verification
            results in the{' '}
            <a
              href={CREDITS_CONTENT.author.portfolioUrl}
              style={linkStyles}
              target="_blank"
              rel="noopener noreferrer"
            >
              project portfolio
            </a>
            .
          </p>
          <p>
            <a
              href={CREDITS_CONTENT.author.linkedinUrl}
              style={linkStyles}
              target="_blank"
              rel="noopener noreferrer"
            >
              Connect on LinkedIn
            </a>
          </p>
        </div>

        <div style={sectionStyles}>
          <h3 style={sectionTitleStyles}>Acknowledgements</h3>
          <p>{CREDITS_CONTENT.acknowledgements}</p>
        </div>

        <div style={sectionStyles}>
          <h3 style={sectionTitleStyles}>Credits</h3>
          <ul>
            {CREDITS_CONTENT.materials.map((item) => (
              <li key={item.label}>
                <strong>{item.label}:</strong>{' '}
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
              </li>
            ))}
          </ul>
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
