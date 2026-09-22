function [pScore, level] = compute_pscore(ma, he, ex, se)
% COMPUTE_PSCORE NetraAI P-score V2
%
% Inputs:
%   ma - microaneurysm evidence [0,100]
%   he - hemorrhage evidence [0,100]
%   ex - exudate evidence [0,100]
%   se - severe-exudate evidence [0,100]
%
% Output:
%   pScore - weighted evidence score [0,100]
%   level  - evidence category

pScore = ...
    0.30 * ma + ...
    0.30 * he + ...
    0.25 * ex + ...
    0.15 * se;

if pScore >= 80
    level = 'HIGH';
elseif pScore >= 60
    level = 'MODERATE';
else
    level = 'LOW';
end

end