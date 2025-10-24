// src/App.jsx
//import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Menu from './Menu'; 
import StoryPlayer from './StoryPlayer'; 

function App() {
  return (
    <Routes>
      <Route path="/" element={<Menu />} />
      
      <Route path="/story/:storyId" element={<StoryPlayer />} />
    </Routes>
  );
}

export default App;