% ==========================================================
% MATLAB STATISTICAL ANALYSIS: series → mean return/annualised volatility.
% ==========================================================
% PURPOSE: Calculate mean return, volatility and observation count.
% FRAMEWORK: MATLAB bridge → This function → Output structure → JSON.
% LECTURE: Functions, parameters, variables, array indexing,
% element-wise operators, function calls and structure fields.
% ==========================================================
% 1. FUNCTION DEFINITION
% ==========================================================
function output=analysis_functions(input) % I define a function that receives input data and returns an output structure.
% ==========================================================
% 2. PREPARE THE VALUE VECTOR
% ==========================================================
v=input.values(:); % I read the values field and reshape all its elements into one column vector.
% ==========================================================
% 3. CALCULATE SIMPLE RETURNS
% ==========================================================
r=diff(v)./v(1:end-1); % I divide each adjacent value change by its previous value; ./ performs element-wise division.
% ==========================================================
% 4. STORE THE AVERAGE RETURN
% ==========================================================
output.mean_return=mean(r); % I store the arithmetic average of the returns as a decimal, without annualising it.
% ==========================================================
% 5. STORE ANNUALISED VOLATILITY
% ==========================================================
output.volatility=std(r)*sqrt(252); % I multiply sample return standard deviation by the square root of 252, assuming daily returns.
% ==========================================================
% 6. STORE THE INPUT OBSERVATION COUNT
% ==========================================================
output.observations=numel(v); % I count the original input values; there is normally one fewer return than input values.
% ==========================================================
% 7. IDENTIFY THE CALCULATION ENGINE
% ==========================================================
output.engine='MATLAB'; % I store a character-vector label identifying the calculation engine.
end % I finish the function and return the output variable.