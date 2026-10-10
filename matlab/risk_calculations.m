% ==========================================================
% MATLAB RISK CALCULATIONS: JSON input → position size/stop.
% ==========================================================
% PURPOSE: Calculate position size and a long-position stop.
% INPUT: Field values supplied by the caller; no JSON parsing here.
% OUTPUT: A structure containing the results and engine label.
% LECTURE: Functions, parameters, variables, assignment,
% arithmetic operators, structure fields and text values.
% ==========================================================
% 1. FUNCTION DEFINITION
% ==========================================================
function output=risk_calculations(input) % I define a function with one input parameter and one returned output.
% ==========================================================
% 2. MAXIMUM RISK AMOUNT
% ==========================================================
riskAmount=input.account_balance*input.risk_percentage; % I multiply account balance by the risk fraction; 0.01 means 1%.
% ==========================================================
% 3. RISK PER SHARE
% ==========================================================
riskPerShare=input.entry_price*input.stop_loss_pct; % I multiply entry price by the stop-distance fraction; 0.05 means 5%.
% ==========================================================
% 4. POSITION SIZE
% ==========================================================
output.position_size=riskAmount/riskPerShare; % I divide the risk budget by risk per share and store the unrounded quantity.
% ==========================================================
% 5. LONG-POSITION STOP PRICE
% ==========================================================
output.stop_loss_price=input.entry_price*(1-input.stop_loss_pct); % I calculate a stop below entry; an entry of 100 with 0.05 gives 95.
% ==========================================================
% 6. CALCULATION ENGINE LABEL
% ==========================================================
output.engine='MATLAB'; % I store a character-vector label identifying the calculation engine.
end % I finish the function; MATLAB returns the output variable.