% ========================================================== MATLAB REGIME HEURISTIC: price series → bull/bear/sideways. ==========================================================
function output=market_algorithms(input)
p=input.prices(:); sw=min(20,numel(p)); lw=min(60,numel(p)); s=mean(p(end-sw+1:end)); l=mean(p(end-lw+1:end)); if s>l*1.01, reg='bull'; elseif s<l*.99, reg='bear'; else, reg='sideways'; end; output.regime=reg; output.short_ma=s; output.long_ma=l; output.engine='MATLAB';
end
