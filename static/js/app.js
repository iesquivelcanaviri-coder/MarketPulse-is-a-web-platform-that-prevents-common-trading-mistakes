// ==========================================================
// GLOBAL MARKETPULSE JAVASCRIPT
// Framework mapping: base.html loads this for small shared browser behaviours.
// ==========================================================
document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('[data-uppercase-symbol]').forEach(el=>el.addEventListener('input',()=>el.value=el.value.toUpperCase())));
// ==========================================================
// GLOBAL MARKETPULSE JAVASCRIPT
// Framework mapping: base.html loads this for small shared browser behaviours.
// ==========================================================

// ==========================================================
// 1. WAIT FOR THE PAGE HTML TO FINISH PARSING
// ==========================================================
document.addEventListener( // Method call: I register an event listener on the document.
    'DOMContentLoaded', // String argument: I wait until the page's HTML has been parsed.
    () => document.querySelectorAll( // Arrow-function callback and DOM query: I find every matching element.
        '[data-uppercase-symbol]' // Attribute selector: I select elements carrying this HTML attribute.
    ).forEach( // Method chaining and iteration: I process each matching element.
        el => el.addEventListener( // Arrow function and parameter: el represents the current element.

            // --------------------------------------------------
            // 2. RESPOND WHEN THE INPUT VALUE CHANGES
            // --------------------------------------------------
            'input', // Event name: I respond to user input, including typing and pasting.
            () => el.value = el.value.toUpperCase() // Callback and assignment: I replace the element's value with its uppercase version.
        ) // Closing parenthesis: I finish registering this element's input listener.
    ) // Closing parenthesis: I finish processing the matching elements.
); // Closing parenthesis and semicolon: I finish registering the document listener.