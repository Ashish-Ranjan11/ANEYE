function [action, priority, reason, routeCode] = trace_route( ...
    qualityStatus, concordanceStatus, stabilityLevel, ...
    trustLevel, referableDR)
% TRACE_ROUTE
% MATLAB R2014a port of NetraAI V2 routing precedence.
%
% routeCode is numeric for later Simulink/SimEvents integration:
%
%   1 = ROUTINE_SCREENING
%   2 = REFER_OPHTHALMOLOGY
%   3 = HUMAN_REVIEW
%   4 = REVIEW_OR_RECAPTURE
%   5 = RECAPTURE
%
% IMPORTANT:
% Decision order is safety-critical. Do not reorder conditions.

% ============================================================
% 1. QUALITY FAILURE
% ============================================================
if strcmp(qualityStatus,'UNGRADEABLE')

    action = 'RECAPTURE';
    priority = 'HIGH';

    reason = ...
        'Image quality is insufficient for automated screening.';

    routeCode = 5;
    return;
end

% ============================================================
% 2. EVIDENCE DISCORDANCE
% ============================================================
if strcmp(concordanceStatus,'LOW')

    action = 'HUMAN_REVIEW';
    priority = 'HIGH';

    reason = ...
        'Global prediction and independent retinal evidence are discordant.';

    routeCode = 3;
    return;
end

% ============================================================
% 3. INSTABILITY
% ============================================================
if strcmp(stabilityLevel,'LOW')

    action = 'HUMAN_REVIEW';
    priority = 'HIGH';

    reason = ...
        'Prediction or explanation is unstable under benign image perturbations.';

    routeCode = 3;
    return;
end

% ============================================================
% 4. LOW OVERALL TRUST
% ============================================================
if strcmp(trustLevel,'LOW')

    action = 'HUMAN_REVIEW';
    priority = 'HIGH';

    reason = ...
        'Overall case-level trust is low.';

    routeCode = 3;
    return;
end

% ============================================================
% 5. REFERABLE DR
% ============================================================
if referableDR

    action = 'REFER_OPHTHALMOLOGY';
    priority = 'HIGH';

    reason = ...
        'Calibrated referable-DR screening decision exceeds the locked operating threshold.';

    routeCode = 2;
    return;
end

% ============================================================
% 6. BORDERLINE IMAGE
% ============================================================
if strcmp(qualityStatus,'BORDERLINE')

    action = 'REVIEW_OR_RECAPTURE';
    priority = 'MODERATE';

    reason = ...
        'Image remains borderline quality.';

    routeCode = 4;
    return;
end

% ============================================================
% 7. ROUTINE
% ============================================================
action = 'ROUTINE_SCREENING';
priority = 'LOW';

reason = ...
    'No referable DR identified with sufficient system reliability.';

routeCode = 1;

end