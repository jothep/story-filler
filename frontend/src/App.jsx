// src/App.jsx
// Defines the main application routing structure using `react-router-dom`.
// It maps paths to the `Menu`, `StoryPlayer`, and `Congratulations` components.
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
