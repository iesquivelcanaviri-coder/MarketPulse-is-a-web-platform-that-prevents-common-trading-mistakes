% ========================================================== MATLAB STATISTICAL ANALYSIS: series → mean return/annualised volatility. ==========================================================
function output=analysis_functions(input)
v=input.values(:); r=diff(v)./v(1:end-1); output.mean_return=mean(r); output.volatility=std(r)*sqrt(252); output.observations=numel(v); output.engine='MATLAB';
end
