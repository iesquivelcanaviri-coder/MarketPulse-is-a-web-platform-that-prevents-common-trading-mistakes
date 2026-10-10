// ==========================================================
// API STATUS: checks React ↔ Django connectivity through /api/health/.
// ==========================================================
// 1. IMPORTS
// ==========================================================
import { useEffect, useState } from 'react'; // I import hooks for running an effect and storing component state.
import { get } from '../api.js'; // I import the shared GET helper from the parent folder.
// ==========================================================
// 2. COMPONENT AND STATE
// ==========================================================
export default function Status() { // I define the Status component and make it the file's default export.
    const [ok, setOk] = useState(false); // I unpack the current Boolean state and its setter; initially, ok is false.
    // ======================================================
    // 3. API HEALTH REQUEST
    // ======================================================
    useEffect(() => { // I register an arrow function that React runs after the component mounts.
        get('/health/') // I request the health endpoint using the API base address defined in api.js.
            .then(() => setOk(true)) // If the request and JSON parsing succeed, I set the status to true.
            .catch(() => setOk(false)); // If the promise rejects, I set the status to false.
    }, []); // The empty dependency array prevents reruns caused by changing component state or props.
    // ======================================================
    // 4. STATUS BADGE
    // ======================================================
    return ( // I return JSX describing the badge to display.
        <span className={`badge ${ok ? 'bg-success' : 'bg-warning text-dark'}`}> {/* I choose green when ok is true, otherwise yellow with dark text. */}
            {ok ? 'Django API connected' : 'API offline'} {/* I choose the badge message using the conditional operator. */}
        </span> // I close the badge element.
    ); // I finish the return statement.
} // I finish the Status component.