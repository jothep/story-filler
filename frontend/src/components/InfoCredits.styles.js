/**
 * InfoCredits Component Styles
 * Separated for better maintainability
 */
import { COLORS, SPACING, Z_INDEX } from '../constants/theme';

/** @type {import('react').CSSProperties} */

export const buttonStyles = {
  position: 'relative',
  zIndex: Z_INDEX.CONTENT,
  padding: `${SPACING.SMALL} ${SPACING.MEDIUM}`,
  fontSize: '0.75rem',
  cursor: 'pointer',
  background: COLORS.WOOD_PRIMARY,
  border: `3px solid ${COLORS.WOOD_DARK}`,
  color: COLORS.TEXT_LIGHT,
  textShadow: '1px 1px #000',
  fontFamily: '"Press Start 2P", cursive',
  letterSpacing: '1px',
};

/** @type {import('react').CSSProperties} */

export const buttonHoverStyles = {
  background: COLORS.WOOD_LIGHT,
};

/** @type {import('react').CSSProperties} */

export const modalOverlayStyles = {
  position: 'fixed',
  top: 0,
  left: 0,
  width: '100%',
  height: '100%',
  backgroundColor: COLORS.MODAL_OVERLAY_BG,
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: Z_INDEX.MODAL_OVERLAY,
};

/** @type {import('react').CSSProperties} */

export const modalContentStyles = {
  position: 'relative',
  maxWidth: '600px',
  width: '90%',
  maxHeight: '80vh',
  overflowY: 'auto',
  padding: SPACING.XLARGE,
  background: COLORS.WOOD_BACKGROUND,
  border: `4px solid ${COLORS.WOOD_DARK}`,
  boxShadow: `0 0 0 2px ${COLORS.WOOD_PRIMARY}, 4px 4px 0 4px #000`,
  zIndex: Z_INDEX.MODAL_CONTENT,
};

/** @type {import('react').CSSProperties} */

export const closeButtonStyles = {
  position: 'absolute',
  top: SPACING.SMALL,
  right: SPACING.SMALL,
  width: '32px',
  height: '32px',
  background: COLORS.WOOD_ACCENT,
  border: `2px solid ${COLORS.WOOD_DARK}`,
  color: '#000',
  fontSize: '1rem',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontFamily: 'monospace',
  fontWeight: 'bold',
};

/** @type {import('react').CSSProperties} */

export const closeButtonHoverStyles = {
  background: COLORS.WOOD_LIGHTER,
};

/** @type {import('react').CSSProperties} */

export const titleStyles = {
  textAlign: 'center',
  fontSize: '1.2rem',
  marginBottom: SPACING.LARGE,
  color: COLORS.WOOD_DARK,
  textShadow: `2px 2px ${COLORS.TEXT_LIGHT}`,
};

/** @type {import('react').CSSProperties} */

export const sectionStyles = {
  marginBottom: SPACING.LARGE,
  lineHeight: '1.8',
  fontSize: '0.9rem',
  color: COLORS.TEXT_PRIMARY,
};

/** @type {import('react').CSSProperties} */

export const sectionTitleStyles = {
  fontSize: '1rem',
  fontWeight: 'bold',
  marginBottom: SPACING.SMALL,
  color: COLORS.WOOD_PRIMARY,
};

/** @type {import('react').CSSProperties} */

export const linkStyles = {
  color: COLORS.LINK,
  textDecoration: 'underline',
};
