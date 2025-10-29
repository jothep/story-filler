// src/main.jsx
// The main entry point for the React application.
// It initializes the React root, wraps the App component with `BrowserRouter`
// to enable routing, and imports global styles (NES.css) and fonts.

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom'; 
import App from './App';

import 'nes.css/css/nes.min.css';

import '@fontsource/press-start-2p';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
