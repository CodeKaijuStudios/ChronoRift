/**
 * ChronoRift Frontend Entry Point
 * React application initialization and root setup
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router } from 'react-router-dom';

// Application Components
import App from './App';

// Global Styles
import './styles/global.css';

/**
 * Initialize React application
 * - Set up routing context
 * - Mount to root DOM element
 * - Enable strict mode for development
 */
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <Router>
      <App />
    </Router>
  </React.StrictMode>
);

/**
 * Handle React errors globally
 */
if (import.meta.env.DEV) {
  // Development error boundary
  window.addEventListener('error', (event) => {
    console.error('React Error:', event.error);
  });
}

/**
 * Hot Module Replacement (HMR) setup for development
 */
if (import.meta.hot) {
  import.meta.hot.accept();
}
