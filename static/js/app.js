// ==========================================================
// GLOBAL MARKETPULSE JAVASCRIPT
// Framework mapping: base.html loads this for small shared browser behaviours.
// ==========================================================
document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('[data-uppercase-symbol]').forEach(el=>el.addEventListener('input',()=>el.value=el.value.toUpperCase())));
