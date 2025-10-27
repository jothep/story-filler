// src/App.jsx
//import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Menu from './pages/Menu';
import StoryPlayer from './pages/StoryPlayer';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Menu />} />

      <Route path="/story/:storyId" element={<StoryPlayer />} />
    </Routes>
  );
}

export default App;
