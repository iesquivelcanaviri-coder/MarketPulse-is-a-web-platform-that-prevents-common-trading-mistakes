// ==========================================================
// REACT RISK UI: posts values to Django's server-side risk calculator.
// ==========================================================
// 1. IMPORTS
// ==========================================================
import { useState } from 'react'; // I import the React hook that stores component state.
import { post } from '../api.js'; // I import the shared helper for sending JSON POST requests.
// ==========================================================
// 2. COMPONENT AND STATE
// ==========================================================
export default function Risk() { // I define the Risk component and export it for other files to use.
    const [f, setF] = useState({ // I store the form object in f and use setF to update it.
        account_balance: 10000, // I start with an account balance of 10,000.
        risk_percentage: .01, // I start with a decimal risk fraction of 0.01, meaning 1%.
        stop_loss_pct: .05, // I start with a decimal stop-loss fraction of 0.05, meaning 5%.
        entry_price: 100 // I start with an entry price of 100.
    }), // I finish the initial form object and continue the const declaration.
        [result, setResult] = useState(null), // I start without a calculation result.
        [error, setError] = useState(''); // I start with an empty error message.
    // ======================================================
    // 3. UPDATE A FORM FIELD
    // ======================================================
    function change(e) { // I receive the change event from an input.
        setF({ ...f, [e.target.name]: Number(e.target.value) }); // I copy the form and replace the named field with its numeric value.
    } // I finish the input-change handler.
    // ======================================================
    // 4. SUBMIT VALUES TO DJANGO
    // ======================================================
    async function submit(e) { // I define an asynchronous handler for submitting the form.
        e.preventDefault(); // I stop the browser's normal form submission and page navigation.
        try { // I attempt the request and handle failures in catch.
            setError(''); // I clear the previous error message.
            setResult(await post('/risk/position-size/', f)); // I send the form values, wait for the response and store the result.
        } catch (x) { // I receive an error if the request or response processing fails.
            setError(x.message); // I store its message so the interface can display it.
        } // I finish the error-handling block.
    } // I finish the submission handler.
    // ======================================================
    // 5. FORM AND RESULT DISPLAY
    // ======================================================
    return ( // I return the JSX describing the interface.
        <div className="card shadow-sm"> {/* I create a Bootstrap card with a small shadow. */}
            <div className="card-body"> {/* I create the card's inner content area. */}
                <h4>Risk Calculator</h4> {/* I display the calculator heading. */}
                <form onSubmit={submit}> {/* I connect form submission to the submit function. */}
                    {Object.entries(f).map(([k, v]) => ( // I loop through the form's key/value pairs and unpack each pair.
                        <div className="mb-2" key={k}> {/* I group each field and give React a stable list key. */}
                            <label className="form-label">{k.replaceAll('_', ' ')}</label> {/* I replace underscores with spaces to create the visible label. */}
                            <input // I start the numeric input element; these comments are inside its opening tag.
                                className="form-control" // I apply Bootstrap's input styling.
                                type="number" // I use a numeric input.
                                step="0.001" // I specify a step interval of 0.001.
                                name={k} // I identify which property the change handler should update.
                                value={v} // I make the displayed value follow React state.
                                onChange={change} // I call change when the user edits this input.
                            /> {/* I finish the input element. */}
                        </div> // I finish the JSX element returned by this map callback.
                    ))} {/* I finish the map callback, map call and JSX expression. */}
                    <button className="btn btn-primary w-100">Calculate via Django</button> {/* I add a full-width button that submits the form. */}
                </form> {/* I finish the form. */}
                {error && <div className="alert alert-danger mt-3">{error}</div>} {/* I display the error alert when the error string is truthy. */}
                {result && ( // I include the result alert when result is truthy.
                    <div className="alert alert-success mt-3"> {/* I style the result as a Bootstrap success alert. */}
                        Position: {Number(result.position_size).toFixed(2)} {/* I convert the position size to a number and display two decimal places. */}
                        <br /> {/* I put the stop price on a new line. */}
                        Stop: {Number(result.stop_loss_price).toFixed(2)} {/* I convert the stop price to a number and display two decimal places. */}
                    </div> // I finish the result alert.
                )} {/* I finish the conditional result expression. */}
            </div> {/* I finish the card body. */}
        </div> // I finish the outer card.
    ); // I finish the return statement.
} // I finish the Risk component.