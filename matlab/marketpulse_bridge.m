% ==========================================================
% MATLAB JSON BRIDGE
% Framework mapping: core/matlab_bridge.py → this dispatcher → specialist MATLAB function → JSON output.
% ==========================================================
function marketpulse_bridge(inputPath,outputPath,operation)
input=jsondecode(fileread(inputPath));
switch operation
    case 'risk', output=risk_calculations(input);
    case 'analysis', output=analysis_functions(input);
    case 'regime', output=market_algorithms(input);
    otherwise, error('Unknown operation');
end
fid=fopen(outputPath,'w'); fwrite(fid,jsonencode(output),'char'); fclose(fid);
end
