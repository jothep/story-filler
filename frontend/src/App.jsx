import { Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Menu from './pages/Menu';
import StoryPlayer from './pages/StoryPlayer';
import Congratulations from './pages/Congratulations';

function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<Menu />} />
        <Route path="/story/:storyId" element={<StoryPlayer />} />
        <Route path="/story/:storyId/complete" element={<Congratulations />} />
      </Routes>
    </ErrorBoundary>
  );
}

export default App;
