// ==========================================================
// REACT APP: composes DRF status, market chart and risk calculator.
// ==========================================================
// 1. IMPORT CHILD COMPONENTS
// ==========================================================
import Status from './components/Status.jsx'; // I import the component displayed in the navigation bar.
import Market from './components/Market.jsx'; // I import the market component displayed in the wider column.
import Risk from './components/Risk.jsx'; // I import the risk component displayed in the narrower column.
// ==========================================================
// 2. DEFINE AND EXPORT THE MAIN COMPONENT
// ==========================================================
export default function App() { // I define App as a function component and this module's default export.
    return ( // I return the JSX that describes the page; parentheses allow readable multiline formatting.
        <> {/* I begin a fragment that groups the navigation and main content without an extra HTML wrapper. */}
            {/* ================================================== */}
            {/* 3. NAVIGATION BAR */}
            {/* ================================================== */}
            <nav className="navbar navbar-dark bg-primary"> {/* I create a Bootstrap navigation bar with a primary background. */}
                <div className="container"> {/* I place navigation content inside a Bootstrap container. */}
                    <span className="navbar-brand fw-bold">MarketPulse React</span> {/* I display the bold application brand. */}
                    <Status /> {/* I include the Status component using a self-closing JSX tag. */}
                </div> {/* I finish the navigation container. */}
            </nav> {/* I finish the navigation bar. */}
            {/* ================================================== */}
            {/* 4. MAIN PAGE CONTENT */}
            {/* ================================================== */}
            <main className="container py-4"> {/* I create the main content region with a container and vertical padding. */}
                <h1>Interactive MarketPulse Client</h1> {/* I display the page's main heading. */}
                <p className="text-muted">React handles interactive presentation; Django REST Framework handles data and business logic.</p> {/* I display the frontend and backend responsibility explanation. */}
                {/* ============================================== */}
                {/* 4.1 MARKET AND RISK COMPONENT LAYOUT */}
                {/* ============================================== */}
                <div className="row g-4"> {/* I create a Bootstrap grid row with gutters between columns. */}
                    <div className="col-lg-7"> {/* I allocate seven of twelve grid columns at large screen sizes and above. */}
                        <Market /> {/* I include the Market component in this column. */}
                    </div> {/* I finish the market column. */}
                    <div className="col-lg-5"> {/* I allocate the remaining five grid columns at large screen sizes and above. */}
                        <Risk /> {/* I include the Risk component in this column. */}
                    </div> {/* I finish the risk column. */}
                </div> {/* I finish the grid row. */}
            </main> {/* I finish the main content region. */}
        </> // I finish the fragment containing the page.
    ); // I finish the return statement.
} // I finish the App function.