// src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom'; // 1. 导入
import App from './App';

// 导入 NES.css (全局生效)
import 'nes.css/css/nes.min.css';

// 导入 Google Font (NES.css 推荐)
import '@fontsource/press-start-2p';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
