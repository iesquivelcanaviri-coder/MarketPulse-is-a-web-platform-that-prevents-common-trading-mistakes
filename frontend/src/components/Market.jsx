// ==========================================================
// MARKET CHART: stored PostgreSQL market data → DRF → Chart.js.
// ==========================================================
// 1. IMPORTS
// ==========================================================
import { useState } from 'react'; // I import the hook that stores component state.
import { Line } from 'react-chartjs-2'; // I import the React component that displays a Chart.js line chart.
import { // I start importing the Chart.js features used below.
    Chart as ChartJS, // I give Chart the local alias ChartJS.
    CategoryScale, // I import the scale used for category labels, such as the supplied dates.
    LinearScale, // I import the numeric scale used for prices.
    PointElement, // I import the element that draws individual data points.
    LineElement, // I import the element that draws the connecting line.
    Tooltip, // I import the plugin that displays information when hovering over points.
    Legend // I import the plugin that displays dataset labels.
} from 'chart.js'; // I finish the imports from Chart.js.
import { get } from '../api.js'; // I import the shared GET request helper.
// ==========================================================
// 2. REGISTER CHART FEATURES
// ==========================================================
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend); // I register these features so Chart.js can use them.
// ==========================================================
// 3. COMPONENT AND STATE
// ==========================================================
export default function Market() { // I define and export the Market component.
    const [symbol, setSymbol] = useState('AAPL'), // I start with AAPL as the symbol and keep a setter for updates.
        [rows, setRows] = useState([]), // I start with an empty array of market records.
        [error, setError] = useState(''); // I start with an empty error message.
    // ======================================================
    // 4. LOAD MARKET DATA
    // ======================================================
    async function load(e) { // I define an asynchronous handler that receives the form event.
        e.preventDefault(); // I prevent normal form submission from navigating away from the page.
        try { // I attempt the request and handle failures in catch.
            setError(''); // I clear the previous error message.
            setRows(await get(`/market/latest/?symbol=${symbol}&limit=90`)); // I request up to 90 rows for the symbol and store the returned data.
        } catch (x) { // I receive any error thrown during the request or response processing.
            setError(x.message); // I store the error message for display.
        } // I finish the error-handling block.
    } // I finish the load function.
    // ======================================================
    // 5. PREPARE CHART DATA
    // ======================================================
    const data = { // I create the configuration object passed to the chart.
        labels: rows.map(x => x.date), // I create an array of date labels in the order returned by the API.
        datasets: [ // I start the array of chart datasets.
            { // I define one dataset containing closing prices.
                label: `${symbol} close`, // I build its label using the current symbol.
                data: rows.map(x => Number(x.close_price)), // I extract closing prices and convert them into numbers.
                tension: .2 // I set the line's curve tension to 0.2.
            } // I finish the closing-price dataset.
        ] // I finish the datasets array.
    }; // I finish the chart configuration.
    // ======================================================
    // 6. FORM, ERROR MESSAGE AND CHART
    // ======================================================
    return ( // I return JSX describing the interface.
        <div className="card shadow-sm"> {/* I create a Bootstrap card with a small shadow. */}
            <div className="card-body"> {/* I create the card's content area. */}
                <h4>Market Data</h4> {/* I display the heading. */}
                <form className="input-group mb-3" onSubmit={load}> {/* I group the input and button and connect submission to load. */}
                    <input // I start the input element; these comments are inside its opening tag.
                        className="form-control" // I apply Bootstrap's input styling.
                        value={symbol} // I make the input display the symbol stored in state.
                        onChange={e => setSymbol(e.target.value.toUpperCase())} // I convert typed text to uppercase and update the symbol.
                    /> {/* I finish the input element. */}
                    <button className="btn btn-primary">Load</button> {/* I add the button that submits the form. */}
                </form> {/* I finish the form. */}
                {error && <div className="alert alert-danger">{error}</div>} {/* I display an error alert when the error string is truthy. */}
                {rows.length ? <Line data={data} /> : <p>Import data in Django first.</p>} {/* I show the chart when rows exist; otherwise, I show the message. */}
            </div> {/* I finish the card body. */}
        </div> // I finish the outer card element.
    ); // I finish the return statement.
} // I finish the Market component.