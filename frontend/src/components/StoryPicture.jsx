// src/components/StoryPicture.jsx
// Displays the story's main picture within a dark container, pulling
// the image URL from the `useStoryPlayback` context.
import { useStoryPlayback } from '../context/StoryPlaybackContext';

const imageStyle = {
  width: '100%',  
  height: '100%', 
  objectFit: 'cover', 
};

function StoryPicture() {
  const { story } = useStoryPlayback();
  return (
    <div
      className="nes-container is-dark"
      style={{
        height: '100%',
        boxSizing: 'border-box',
        
        padding: 0,
        backgroundColor: '#111',
      }}
    >
      {story && story.picture_url ? (
        <img
          src={story.picture_url} 
          alt={story.title || 'Story picture'}
          style={imageStyle}
        />
      ) : (
        <p style={{ padding: '1rem' }}>Story picture</p>
      )}
    </div>
  );
}

export default StoryPicture;