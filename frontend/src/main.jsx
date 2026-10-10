// ==========================================================
// REACT ENTRY: imports Bootstrap/styles and mounts App.jsx.
// ==========================================================
// 1. IMPORT REACT AND ITS BROWSER RENDERER
// ==========================================================
import React from 'react'; // I import React, which provides the StrictMode component used below.
import ReactDOM from 'react-dom/client'; // I import React's client renderer, which provides createRoot.
// ==========================================================
// 2. IMPORT BOOTSTRAP AND CUSTOM STYLES
// ==========================================================
import 'bootstrap/dist/css/bootstrap.min.css'; // I load Bootstrap's CSS so its classes can style the interface.
import 'bootstrap/dist/js/bootstrap.bundle.min.js'; // I load Bootstrap's JavaScript bundle for interactive Bootstrap components.
import './styles.css'; // I load the custom stylesheet after Bootstrap's CSS.
// ==========================================================
// 3. IMPORT THE MAIN APPLICATION COMPONENT
// ==========================================================
import App from './App.jsx'; // I import the component that defines the main React interface.
// ==========================================================
// 4. CREATE THE ROOT AND RENDER THE APPLICATION
// ==========================================================
ReactDOM.createRoot(document.getElementById('root')).render( // I find the HTML container, create its React root and call render on that root.
    <React.StrictMode> // I wrap the application in React's additional development checks.
        <App /> // I include the App component using a self-closing JSX tag.
    </React.StrictMode> // I finish the StrictMode wrapper.
); // I finish the render call.