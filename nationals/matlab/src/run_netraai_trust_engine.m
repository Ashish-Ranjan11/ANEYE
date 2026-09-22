function R = run_netraai_trust_engine(caseData)
% RUN_NETRAAI_TRUST_ENGINE
% Unified MATLAB trust/decision layer for ANEYE / NetraAI.
%
% caseData expects:
%   caseId
%   qualityStatus
%   imageReliability       0..1
%   grade                  0..4
%   calibratedRDR          0..1
%   ma, he, ex, se         0..1
%   nv                     [] if unavailable, otherwise 0..1
%   xaiIntegrity           0..1
%   stability              0..1
%
% Output R is the structured interface to Simulink/SimEvents.

C = netraai_trust_contract();

% ------------------------------------------------------------
% CALIBRATED RDR DECISION
% ------------------------------------------------------------
referableDR = ...
    caseData.calibratedRDR >= C.calibration.rdrThreshold;

if referableDR
    routeConfidence = caseData.calibratedRDR;
else
    routeConfidence = 1.0 - caseData.calibratedRDR;
end

% ------------------------------------------------------------
% P-SCORE
% compute_pscore currently accepts percentage evidence.
% ------------------------------------------------------------
[pScore,pLevel] = compute_pscore( ...
    caseData.ma * 100, ...
    caseData.he * 100, ...
    caseData.ex * 100, ...
    caseData.se * 100);

% ------------------------------------------------------------
% CONCORDANCE
% ------------------------------------------------------------
[cScore,cStatus,support,conflict,limitations] = ...
    compute_concordance( ...
        caseData.grade, ...
        caseData.ma, ...
        caseData.he, ...
        caseData.ex, ...
        caseData.se, ...
        caseData.nv);

% ------------------------------------------------------------
% T-SCORE
% ------------------------------------------------------------
[tScore,tLevel,tComponents] = ...
    compute_tscore( ...
        caseData.imageReliability, ...
        routeConfidence, ...
        cScore / 100.0, ...
        caseData.xaiIntegrity, ...
        caseData.stability);

% ------------------------------------------------------------
% TRACE ROUTING
% ------------------------------------------------------------
if caseData.stability >= 0.80
    stabilityLevel = 'HIGH';
elseif caseData.stability >= 0.60
    stabilityLevel = 'MODERATE';
else
    stabilityLevel = 'LOW';
end

[action,priority,reason,routeCode] = ...
    trace_route( ...
        caseData.qualityStatus, ...
        cStatus, ...
        stabilityLevel, ...
        tLevel, ...
        referableDR);

% ------------------------------------------------------------
% STRUCTURED RESULT
% ------------------------------------------------------------
R.caseId = caseData.caseId;

R.quality.status = caseData.qualityStatus;
R.quality.reliability = caseData.imageReliability;

R.global.grade = caseData.grade;
R.global.calibratedRDR = caseData.calibratedRDR;
R.global.rdrThreshold = C.calibration.rdrThreshold;
R.global.referableDR = referableDR;
R.global.routeConfidence = routeConfidence;

R.pathology.pScore = pScore;
R.pathology.level = pLevel;

R.concordance.score = cScore;
R.concordance.status = cStatus;
R.concordance.support = support;
R.concordance.conflict = conflict;
R.concordance.limitations = limitations;

R.trust.tScore = tScore;
R.trust.level = tLevel;
R.trust.components = tComponents;

R.stability.score = caseData.stability * 100;
R.stability.level = stabilityLevel;

R.xai.integrity = caseData.xaiIntegrity * 100;

R.recommendation.action = action;
R.recommendation.priority = priority;
R.recommendation.reason = reason;
R.recommendation.routeCode = routeCode;

% ------------------------------------------------------------
% PROVENANCE / TRUST CONTRACT
% ------------------------------------------------------------
R.provenance.contractVersion = C.system.contractVersion;
R.provenance.pscoreVersion = C.trust.pscoreVersion;
R.provenance.concordanceVersion = C.trust.concordanceVersion;
R.provenance.tscoreVersion = C.trust.tscoreVersion;
R.provenance.stabilityVersion = C.trust.stabilityVersion;
R.provenance.routingVersion = C.trust.routingVersion;
R.provenance.calibrationVersion = C.calibration.version;

end