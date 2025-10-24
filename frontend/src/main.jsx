// src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

// 导入 NES.css (全局生效)
import 'nes.css/css/nes.min.css'; 

// 导入 Google Font (NES.css 推荐)
// 你也可以在 index.html 中导入
import "@fontsource/press-start-2p";

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)