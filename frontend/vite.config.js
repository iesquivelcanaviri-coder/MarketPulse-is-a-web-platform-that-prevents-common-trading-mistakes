// ==========================================================
// VITE CONFIG: React dev server; Django CORS allows localhost:5173.
// ==========================================================
// 1. IMPORT CONFIGURATION TOOLS
// ==========================================================
import { defineConfig } from 'vite'; // I import Vite's named configuration helper.
import react from '@vitejs/plugin-react'; // I import the React plugin's default export.
// ==========================================================
// 2. EXPORT THE VITE CONFIGURATION
// ==========================================================
export default defineConfig({ // I pass a configuration object to the helper and export it as this module's default.
    // ======================================================
    // 2.1 ENABLE THE REACT PLUGIN
    // ======================================================
    plugins: [react()], // I call the React plugin factory and place its result in the plugins array.
    // ======================================================
    // 2.2 DEVELOPMENT SERVER SETTINGS
    // ======================================================
    server: { // I begin a nested object containing development-server options.
        port: 5173 // I request port 5173 for the development server.
    } // I finish the server options object.
}); // I finish the configuration object, function call and export statement.