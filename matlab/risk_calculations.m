% ========================================================== MATLAB RISK CALCULATIONS: JSON input → position size/stop. ==========================================================
function output=risk_calculations(input)
riskAmount=input.account_balance*input.risk_percentage; riskPerShare=input.entry_price*input.stop_loss_pct; output.position_size=riskAmount/riskPerShare; output.stop_loss_price=input.entry_price*(1-input.stop_loss_pct); output.engine='MATLAB';
end
