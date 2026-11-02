import { Link } from 'react-router-dom';
import Roll from '../components/Roll';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import InfoCredits from '../components/InfoCredits';
import '../components/Roll.css';
import '../components/BgmHint.css';
import { useStories } from '../hooks/useStories';
import { useBgmPlayer } from '../hooks/useBgmPlayer';
import logoImage from '../assets/story-filler-logo-single-line.png';
import { SPACING, DIMENSIONS, Z_INDEX, COLORS } from '../constants/theme';

/** @type {import('react').CSSProperties} */

const menuStyles = {
  position: 'relative',
  overflow: 'hidden',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: SPACING.XLARGE,
  minHeight: '100vh',
  boxSizing: 'border-box',
};

/** @type {import('react').CSSProperties} */

const titleContainerStyles = {
  width: '100%',
  maxWidth: DIMENSIONS.MAX_CONTENT_WIDTH,
  marginBottom: SPACING.SMALL,
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  position: 'relative',
  zIndex: Z_INDEX.CONTENT,
};

/** @type {import('react').CSSProperties} */

const toggleContainerStyles = {
  position: 'absolute',
  top: SPACING.LARGE,
  right: SPACING.LARGE,
  zIndex: Z_INDEX.BGM_CONTROLS,
  color: 'white',
  textShadow: '1px 1px #000',
};

/** @type {import('react').CSSProperties} */

const bgmHintStyles = {
  position: 'absolute',
  top: SPACING.HINT_TOP,
  right: SPACING.LARGE,
  zIndex: Z_INDEX.BGM_CONTROLS,
  background: COLORS.HINT_BG,
  color: COLORS.TEXT_LIGHT,
  padding: `${SPACING.SMALL} ${SPACING.MEDIUM}`,
  borderRadius: '4px',
  fontSize: '0.75rem',
  whiteSpace: 'nowrap',
  animation: 'fadeIn 0.3s ease-in',
};

/** @type {import('react').CSSProperties} */

const infoButtonContainerStyles = {
  width: '100%',
  display: 'flex',
  justifyContent: 'center',
  marginBottom: SPACING.MEDIUM,
  position: 'relative',
  zIndex: Z_INDEX.CONTENT,
};

/** @type {import('react').CSSProperties} */

const menuListStyles = {
  display: 'flex',
  flexDirection: 'column',
  width: '100%',
  maxWidth: DIMENSIONS.MAX_MENU_WIDTH,
  gap: SPACING.LARGE,
  marginTop: 'auto',
  marginBottom: DIMENSIONS.MENU_BOTTOM_MARGIN,
  position: 'relative',
  zIndex: Z_INDEX.CONTENT,
};

function Menu() {
  const { stories, loading, error, refetch } = useStories();
  const { isMusicPlaying, showHint, toggleMusic } = useBgmPlayer();

  if (loading) {
    return <LoadingSpinner message="Loading stories..." />;
  }

  if (error) {
    return <ErrorMessage error={error} onRetry={refetch} />;
  }

  return (
    <div style={menuStyles}>
      <Roll />

      <div style={toggleContainerStyles}>
        <label>
          <input
            type="checkbox"
            className="nes-checkbox is-dark"
            checked={isMusicPlaying}
            onChange={toggleMusic}
          />
          <span>BGM</span>
        </label>
      </div>

      {showHint && <div style={bgmHintStyles}>Click to start music ⇑</div>}

      <div style={titleContainerStyles}>
        <img
          src={logoImage}
          alt="Story Filler"
          style={{
            width: DIMENSIONS.LOGO_WIDTH,
            height: 'auto',
          }}
        />
      </div>

      <div style={infoButtonContainerStyles}>
        <InfoCredits />
      </div>

      {!stories || stories.length === 0 ? (
        <div
          className="nes-container is-rounded"
          style={{
            textAlign: 'center',
            maxWidth: '500px',
            position: 'relative',
            zIndex: Z_INDEX.CONTENT,
          }}
        >
          <h2>No Stories Available</h2>
          <p>
            There are currently no stories to display. Please check back later!
          </p>
        </div>
      ) : (
        <div style={menuListStyles}>
          {stories.map((story) => (
            <Link
              key={story.id}
              to={`/story/${story.id}`}
              className="nes-btn is-primary"
            >
              {story.title}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default Menu;
