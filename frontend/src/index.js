import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';          // usa App.js, no App.jsx
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  // En dev, StrictMode duplica efectos (no es error)
  <React.StrictMode>
    <App />                       {/* ⛔️ SIN BrowserRouter aquí */}
  </React.StrictMode>
);

reportWebVitals();
