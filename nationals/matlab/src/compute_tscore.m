function [score, level, components] = compute_tscore( ...
    imageReliability, calibratedConfidence, concordance, ...
    xaiIntegrity, stability)
% COMPUTE_TSCORE
% MATLAB R2014a port of NetraAI T_SCORE_V2.
%
% All inputs MUST be normalized to 0..1.
%
% Weights:
%   Image reliability      25%
%   Calibrated confidence  25%
%   Concordance            30%
%   XAI integrity          15%
%   Measured stability      5%
%
% Engineering trust index -- NOT a clinical probability.

imageReliability = clip01(imageReliability);
calibratedConfidence = clip01(calibratedConfidence);
concordance = clip01(concordance);
xaiIntegrity = clip01(xaiIntegrity);
stability = clip01(stability);

value = ...
      0.25 * imageReliability ...
    + 0.25 * calibratedConfidence ...
    + 0.30 * concordance ...
    + 0.15 * xaiIntegrity ...
    + 0.05 * stability;

value = clip01(value);

% Match Python rounding to one decimal place
score = round(value * 1000) / 10;

if score >= 80
    level = 'HIGH';
elseif score >= 60
    level = 'MODERATE';
else
    level = 'LOW';
end

components.imageReliability = ...
    round(imageReliability * 1000) / 10;

components.calibratedConfidence = ...
    round(calibratedConfidence * 1000) / 10;

components.concordance = ...
    round(concordance * 1000) / 10;

components.xaiIntegrity = ...
    round(xaiIntegrity * 1000) / 10;

components.stability = ...
    round(stability * 1000) / 10;

end


function x = clip01(x)

x = double(x);

if x < 0
    x = 0;
elseif x > 1
    x = 1;
end

end