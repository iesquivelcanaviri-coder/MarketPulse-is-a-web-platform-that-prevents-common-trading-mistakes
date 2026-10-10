% ==========================================================
% MATLAB REGIME HEURISTIC: price series → bull/bear/sideways.
% ==========================================================
% PURPOSE: Classify prices by comparing two moving averages.
% FRAMEWORK: MATLAB bridge → This function → Output structure.
% LECTURE: Functions, variables, arrays, indexing, operators,
% conditions, character vectors and structure fields.
% ==========================================================
% 1. FUNCTION DEFINITION
% ==========================================================
function output=market_algorithms(input) % I define a function that receives input data and returns an output structure.
% ==========================================================
% 2. PREPARE THE PRICE VECTOR
% ==========================================================
p=input.prices(:); % I read the prices field and reshape its elements into one column vector.
% ==========================================================
% 3. CHOOSE THE MOVING-AVERAGE WINDOW SIZES
% ==========================================================
sw=min(20,numel(p)); % I choose 20 observations or the available number of prices, whichever is smaller.
lw=min(60,numel(p)); % I choose 60 observations or the available number of prices, whichever is smaller.
% ==========================================================
% 4. CALCULATE THE MOVING AVERAGES
% ==========================================================
s=mean(p(end-sw+1:end)); % I average the final sw prices; end means the last index and the colon selects the inclusive range.
l=mean(p(end-lw+1:end)); % I average the final lw prices using the same indexing pattern.
% ==========================================================
% 5. CLASSIFY THE MARKET REGIME
% ==========================================================
if s>l*1.01 % I check whether the short average is greater than 101% of the long average.
    reg='bull'; % I assign the bull label when the first condition is true.
elseif s<l*.99 % I otherwise check whether the short average is below 99% of the long average.
    reg='bear'; % I assign the bear label when the second condition is true.
else % I handle values that satisfy neither comparison, including equality at the thresholds.
    reg='sideways'; % I assign the sideways label.
end % I finish the conditional branching.
% ==========================================================
% 6. STORE THE RESULTS
% ==========================================================
output.regime=reg; % I store the selected regime in an output structure field.
output.short_ma=s; % I store the short moving average.
output.long_ma=l; % I store the long moving average.
output.engine='MATLAB'; % I store a character-vector label identifying the calculation engine.
end % I finish the function and return the output variable.