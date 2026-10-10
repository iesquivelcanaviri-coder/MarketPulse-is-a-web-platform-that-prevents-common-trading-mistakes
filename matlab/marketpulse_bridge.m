% ==========================================================
% MATLAB JSON BRIDGE
% Framework mapping: core/matlab_bridge.py → this dispatcher → specialist MATLAB function → JSON output.
% ==========================================================
% PURPOSE: Read JSON input, select a calculation and save JSON output.
% LECTURE: Functions, parameters, variables, assignment,
% nested calls, selection, errors, data conversion and file I/O.
% ==========================================================
% 1. FUNCTION DEFINITION
% ==========================================================
function marketpulse_bridge(inputPath,outputPath,operation) % I define a function with three input parameters and no declared return value.
% ==========================================================
% 2. READ AND DECODE THE INPUT FILE
% ==========================================================
input=jsondecode(fileread(inputPath)); % I read the file as text, decode its JSON and store the resulting MATLAB data.
% ==========================================================
% 3. SELECT THE REQUESTED CALCULATION
% ==========================================================
switch operation % I select a branch using the operation parameter.
    case 'risk' % I match the risk operation.
        output=risk_calculations(input); % I pass the decoded input to the risk function and store its result.
    case 'analysis' % I match the analysis operation.
        output=analysis_functions(input); % I pass the input to the analysis function and store its result.
    case 'regime' % I match the market-regime operation.
        output=market_algorithms(input); % I pass the input to the market algorithm function and store its result.
    otherwise % I handle an operation that matches none of the cases.
        error('Unknown operation'); % I raise an error, stopping execution before the output file is written.
end % I finish the switch statement.
% ==========================================================
% 4. ENCODE AND WRITE THE OUTPUT FILE
% ==========================================================
fid=fopen(outputPath,'w'); % I open the output file for writing, creating it or replacing its existing contents, and store its file identifier.
fwrite(fid,jsonencode(output),'char'); % I encode the result as JSON text and write it using character precision.
fclose(fid); % I close the output file.
end % I finish the bridge function.