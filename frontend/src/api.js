// ==========================================================
// API CLIENT: React components → Django REST Framework.
// ==========================================================
// 1. API BASE ADDRESS
// ==========================================================
export const API = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api'; // I use Vite's API address, or the local address if it is falsy.
// ==========================================================
// 2. GET HELPER — REQUEST DATA
// ==========================================================
export async function get(path) { // I export an asynchronous function that receives an endpoint path.
    const r = await fetch(`${API}${path}`, { // I join the base address and path, then wait for the response; GET is the default method.
        credentials: 'include' // I allow eligible cookies to accompany the request, subject to browser and server rules.
    }); // I finish the request options and store the response in r.
    if (!r.ok) throw new Error(`API ${r.status}`); // If the HTTP status is unsuccessful, I throw an error containing its status code.
    return r.json(); // I return the JSON-parsing promise; the caller receives the parsed value when it succeeds.
} // I finish the GET helper.
// ==========================================================
// 3. POST HELPER — SEND JSON DATA
// ==========================================================
export async function post(path, data) { // I export an asynchronous function that receives an endpoint path and data.
    const r = await fetch(`${API}${path}`, { // I build the endpoint address and wait for the server's response.
        method: 'POST', // I select POST to send data to the endpoint.
        headers: { // I start an object containing request headers.
            'Content-Type': 'application/json' // I tell the server that the request body contains JSON.
        }, // I finish the headers object.
        credentials: 'include', // I allow eligible cookies to accompany this request too.
        body: JSON.stringify(data) // I convert the supplied JavaScript data into JSON text.
    }); // I finish the request and store its response in r.
    const b = await r.json(); // I parse the response body before checking whether the HTTP status succeeded.
    if (!r.ok) throw new Error(b.error || `API ${r.status}`); // I use a truthy server error message, or fall back to the HTTP status.
    return b; // I return the parsed response data when the request succeeds.
} // I finish the POST helper.