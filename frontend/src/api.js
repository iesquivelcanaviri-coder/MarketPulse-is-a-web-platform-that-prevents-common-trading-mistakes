// ========================================================== API CLIENT: React components → Django REST Framework. ==========================================================
export const API=import.meta.env.VITE_API_BASE||'http://127.0.0.1:8000/api';
export async function get(path){const r=await fetch(`${API}${path}`,{credentials:'include'});if(!r.ok)throw new Error(`API ${r.status}`);return r.json()}
export async function post(path,data){const r=await fetch(`${API}${path}`,{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify(data)});const b=await r.json();if(!r.ok)throw new Error(b.error||`API ${r.status}`);return b}
