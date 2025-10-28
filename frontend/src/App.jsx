// src/App.jsx
import { Routes, Route } from 'react-router-dom';
import Menu from './pages/Menu';
import StoryPlayer from './pages/StoryPlayer';
import Congratulations from './pages/Congratulations';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Menu />} />
      <Route path="/story/:storyId" element={<StoryPlayer />} />
      <Route path="story/:storyId/complete" element={<Congratulations />} />
    </Routes>
  );
}

export default App;
