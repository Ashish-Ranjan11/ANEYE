function C = netraai_trust_contract()
% NETRAAI_TRUST_CONTRACT
% Frozen interface between Python AI and MATLAB/Simulink.
%
% Values marked MEASURED originate from current prototype evaluation.
% Values marked CONFIG are frozen system parameters.
%
% This contract provides provenance. It is NOT clinical validation.

C.system.name = 'ANEYE / NetraAI';
C.system.pipeline = 'TRACE-DR';
C.system.contractVersion = 'TRUST_CONTRACT_V1';

% ------------------------------------------------------------
% GLOBAL MODEL
% ------------------------------------------------------------
C.globalModel.architecture = 'EfficientNet-B0 Dual Head';
C.globalModel.checkpoint = ...
    'checkpoints/sih_dr/grading/global_final.pth';

C.globalModel.inputSize = [384 384];
C.globalModel.gradeClasses = 5;

% ------------------------------------------------------------
% CALIBRATION
% ------------------------------------------------------------
C.calibration.version = 'RDR_CALIBRATION_V1';

C.calibration.rdrTemperature = ...
    1.2229175567626953;

C.calibration.rdrThreshold = 0.475;

C.calibration.thresholdSelection = ...
    'PS_CONSTRAINED_YOUDEN';

C.calibration.gradeCalibrationStatus = ...
    'EVALUATED_NOT_ADOPTED_FOR_TRUST_V1';

C.calibration.rdrCalibrationStatus = ...
    'ADOPTED_V1';

% ------------------------------------------------------------
% TRUST ENGINE VERSIONS
% ------------------------------------------------------------
C.trust.pscoreVersion = 'P_SCORE_V2';
C.trust.concordanceVersion = 'CONCORDANCE_V2';
C.trust.tscoreVersion = 'T_SCORE_V2';
C.trust.stabilityVersion = 'STABILITY_V1';
C.trust.routingVersion = 'TRACE_DR_V2';

% ------------------------------------------------------------
% ROUTE CODES
% ------------------------------------------------------------
C.routes.ROUTINE_SCREENING = 1;
C.routes.REFER_OPHTHALMOLOGY = 2;
C.routes.HUMAN_REVIEW = 3;
C.routes.REVIEW_OR_RECAPTURE = 4;
C.routes.RECAPTURE = 5;

% ------------------------------------------------------------
% CURRENT MEASURED REFERENCE TIMINGS
% One reference case only - engineering measurement.
% Do NOT interpret as population-wide latency.
% ------------------------------------------------------------
C.referenceTiming.total_ms = 8671.51;
C.referenceTiming.lesion_ms = 5444.68;
C.referenceTiming.anatomy_ms = 1114.00;
C.referenceTiming.stability_ms = 923.00;

C.referenceTiming.source = ...
    'MEASURED_SINGLE_REFERENCE_CASE';

% ------------------------------------------------------------
% CLAIM BOUNDARIES
% ------------------------------------------------------------
C.claims.clinicallyValidated = false;
C.claims.pScoreClinicalScore = false;
C.claims.tScoreClinicalProbability = false;

C.claims.description = ...
    'Research engineering prototype; not autonomous diagnosis.';

end