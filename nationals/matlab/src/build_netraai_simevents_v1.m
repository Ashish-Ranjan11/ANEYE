function modelFile = build_netraai_simevents_v1()
% BUILD_NETRAAI_SIMEVENTS_V1
%
% ANEYE / NetraAI
% R2014a + SimEvents 4.3.2
%
% V1 objective:
%   Prove that the MATLAB TRACE-DR trust engine can drive
%   an actual SimEvents routing network.
%
% IMPORTANT:
%   V1 uses ONE frozen reference-case route for all entities.
%   Dynamic population case-mix comes in V2.
%
% Provenance:
%   Arrival period  = ASSUMPTION
%   Capture time    = ASSUMPTION
%   AI service time = MEASURED SINGLE REFERENCE CASE
%   routeCode       = COMPUTED BY MATLAB TRACE-DR ENGINE

clc

fprintf('\n============================================\n');
fprintf(' ANEYE / NETRAAI SIMEVENTS DIGITAL TWIN V1\n');
fprintf('============================================\n');

% ------------------------------------------------------------
% Ensure source functions are available
% ------------------------------------------------------------
srcDir = fullfile(pwd,'nationals','matlab','src');
addpath(srcDir);

load_system('simeventslib');

% ------------------------------------------------------------
% 1. RUN THE ACTUAL MATLAB TRUST ENGINE
% ------------------------------------------------------------

caseData.caseId = 'APTOS_000c1434d8d7';

caseData.qualityStatus = 'GRADEABLE';
caseData.imageReliability = 0.6168;

caseData.grade = 2;
caseData.calibratedRDR = 0.982208;

caseData.ma = 0.839;
caseData.he = 0.921;
caseData.ex = 0.951;
caseData.se = 0.0;

caseData.nv = [];

caseData.xaiIntegrity = 0.509;
caseData.stability = 0.997;

R = run_netraai_trust_engine(caseData);

refRouteCode = R.recommendation.routeCode;

fprintf('\nTRACE reference result\n');
fprintf('Case      : %s\n',R.caseId);
fprintf('Action    : %s\n',R.recommendation.action);
fprintf('Priority  : %s\n',R.recommendation.priority);
fprintf('RouteCode : %d\n',refRouteCode);
fprintf('T-score   : %.1f %s\n', ...
    R.trust.tScore,R.trust.level);

if refRouteCode ~= 2
    error(['Reference-case regression detected. ' ...
           'Expected routeCode = 2.']);
end

% ------------------------------------------------------------
% 2. LOCATE LEGACY SIMEVENTS BLOCKS
% ------------------------------------------------------------

generatorLib = findLegacyBlock( ...
    'simeventslib', ...
    'Time-Based Entity Generator');

sinkLib = findLegacyBlock( ...
    'simeventslib', ...
    'Entity Sink');

queueLib = ...
    'simeventslib/Queues/FIFO Queue';

serverLib = ...
    'simeventslib/Servers/Single Server';

switchLib = ...
    'simeventslib/Routing/Output Switch';

setAttributeLib = ...
    'simeventslib/Attributes/Set Attribute';

fprintf('\nLegacy SimEvents blocks resolved.\n');

% ------------------------------------------------------------
% 3. CREATE MODEL
% ------------------------------------------------------------

mdl = 'NetraAI_DigitalTwin_V1';

modelDir = fullfile( ...
    pwd, ...
    'nationals', ...
    'simulink');

if ~exist(modelDir,'dir')
    mkdir(modelDir);
end

modelFile = fullfile( ...
    modelDir, ...
    [mdl '.mdl']);

% Close an old loaded copy if present.
try
    close_system(mdl,0);
catch
end

% Remove an old generated model.
if exist(modelFile,'file')
    delete(modelFile);
end

new_system(mdl);

set_param( ...
    mdl, ...
    'StopTime','300');

% ------------------------------------------------------------
% 4. ADD BLOCKS
% ------------------------------------------------------------

arrival = [mdl '/Patient Arrival'];
captureQueue = [mdl '/Capture Queue'];
captureServer = [mdl '/Fundus Capture'];
aiQueue = [mdl '/AI Queue'];
aiServer = [mdl '/TRACE AI Processing'];
setRoute = [mdl '/Set TRACE Route'];
router = [mdl '/TRACE Router'];

add_block( ...
    generatorLib, ...
    arrival, ...
    'Position',[30 220 150 270]);

add_block( ...
    queueLib, ...
    captureQueue, ...
    'Position',[190 220 290 270]);

add_block( ...
    serverLib, ...
    captureServer, ...
    'Position',[330 220 450 270]);

add_block( ...
    queueLib, ...
    aiQueue, ...
    'Position',[490 220 590 270]);

add_block( ...
    serverLib, ...
    aiServer, ...
    'Position',[630 220 770 270]);

add_block( ...
    setAttributeLib, ...
    setRoute, ...
    'Position',[810 220 940 270]);

add_block( ...
    switchLib, ...
    router, ...
    'Position',[990 145 1110 345]);

% ------------------------------------------------------------
% 5. CONFIGURE ARRIVAL
% ------------------------------------------------------------
%
% ASSUMPTION:
% One patient every 15 seconds.
%
% This is NOT a measured clinical arrival rate.

set_param( ...
    arrival, ...
    'GenerateEntitiesUpon', ...
    'Intergeneration time from dialog');

set_param( ...
    arrival, ...
    'Distribution','Constant');

set_param( ...
    arrival, ...
    'Period','15');

set_param( ...
    arrival, ...
    'GenerateEntityAtSimulationStart','on');

set_param( ...
    arrival, ...
    'ResponseWhenBlocked','Pause generation');

% ------------------------------------------------------------
% 6. CONFIGURE CAPTURE QUEUE
% ------------------------------------------------------------

set_param( ...
    captureQueue, ...
    'Capacity','100');

% ------------------------------------------------------------
% 7. CONFIGURE FUNDUS CAPTURE
% ------------------------------------------------------------
%
% ASSUMPTION:
% 12 seconds per capture for initial digital-twin plumbing.
%
% This will later become a scenario variable.

set_param( ...
    captureServer, ...
    'ServiceTimeFrom','Dialog');

set_param( ...
    captureServer, ...
    'ServiceTime','12');

% ------------------------------------------------------------
% 8. CONFIGURE AI QUEUE
% ------------------------------------------------------------

set_param( ...
    aiQueue, ...
    'Capacity','100');

% ------------------------------------------------------------
% 9. CONFIGURE AI SERVICE TIME
% ------------------------------------------------------------
%
% MEASURED:
% 8671.51 ms = 8.67151 seconds
%
% This is from ONE frozen reference case only.

set_param( ...
    aiServer, ...
    'ServiceTimeFrom','Dialog');

set_param( ...
    aiServer, ...
    'ServiceTime','8.67151');

% ------------------------------------------------------------
% 10. ATTACH TRACE routeCode
% ------------------------------------------------------------

set_param( ...
    setRoute, ...
    'AttributeName','routeCode');

set_param( ...
    setRoute, ...
    'AttributeFrom','Dialog');

set_param( ...
    setRoute, ...
    'AttributeValue', ...
    num2str(refRouteCode));

set_param( ...
    setRoute, ...
    'AttributeCreate','on');

% ------------------------------------------------------------
% 11. CONFIGURE 5-WAY TRACE ROUTER
% ------------------------------------------------------------

set_param( ...
    router, ...
    'NumberOutputPorts','5');

% R2014a should support attribute-based switching.
% If this installation rejects the value, fail rather
% than silently use another routing criterion.

try

    set_param( ...
        router, ...
        'SwitchingCriterion', ...
        'From attribute');

catch ME

    fprintf('\nERROR configuring TRACE Router.\n');
    fprintf('R2014a message:\n%s\n',ME.message);

    error(['Could not enable attribute-based routing. ' ...
           'Do not continue with fallback routing.']);
end

set_param( ...
    router, ...
    'AttributeName','routeCode');

% Attribute-based output routing uses the numeric attribute as
% the selected output port. We validate this by the V1 route test.

% ------------------------------------------------------------
% 12. CREATE DESTINATION SINKS
% ------------------------------------------------------------

routineSink = [mdl '/1 ROUTINE'];
referSink = [mdl '/2 OPHTHALMOLOGY'];
humanSink = [mdl '/3 HUMAN REVIEW'];
reviewSink = [mdl '/4 REVIEW RECAPTURE'];
recaptureSink = [mdl '/5 RECAPTURE'];

sinkNames = { ...
    routineSink, ...
    referSink, ...
    humanSink, ...
    reviewSink, ...
    recaptureSink};

sinkY = [ ...
    40, ...
    135, ...
    230, ...
    325, ...
    420];

for k = 1:5

    add_block( ...
        sinkLib, ...
        sinkNames{k}, ...
        'Position', ...
        [1220 sinkY(k) 1350 sinkY(k)+45]);

end

% ------------------------------------------------------------
% 13. CONNECT MAIN PIPELINE
% ------------------------------------------------------------

connectEntity( ...
    mdl,arrival,captureQueue,1);

connectEntity( ...
    mdl,captureQueue,captureServer,1);

connectEntity( ...
    mdl,captureServer,aiQueue,1);

connectEntity( ...
    mdl,aiQueue,aiServer,1);

connectEntity( ...
    mdl,aiServer,setRoute,1);

connectEntity( ...
    mdl,setRoute,router,1);

% ------------------------------------------------------------
% 14. CONNECT TRACE ROUTES 1..5
% ------------------------------------------------------------

for k = 1:5

    connectEntityOutput( ...
        mdl, ...
        router, ...
        sinkNames{k}, ...
        k);

end

% ------------------------------------------------------------
% 15. MODEL METADATA
% ------------------------------------------------------------

descriptionText = [ ...
    'ANEYE / NetraAI TRACE-DR Digital Twin V1. ' ...
    'Arrival period and fundus capture time are assumptions. ' ...
    'AI service time 8.67151 s is a measured single-reference-case ' ...
    'engineering value. TRACE routeCode is generated by the ' ...
    'MATLAB trust engine. This model is a research engineering ' ...
    'prototype and not clinical validation.'];

try
    set_param(mdl,'Description',descriptionText);
catch
end

% ------------------------------------------------------------
% 16. SAVE MODEL
% ------------------------------------------------------------

save_system( ...
    mdl, ...
    modelFile);

fprintf('\n============================================\n');
fprintf(' DIGITAL TWIN MODEL CREATED\n');
fprintf('============================================\n');
fprintf('Model : %s\n',mdl);
fprintf('File  : %s\n',modelFile);
fprintf('\n');
fprintf('ASSUMPTION arrival period : 15.00000 s\n');
fprintf('ASSUMPTION capture time   : 12.00000 s\n');
fprintf('MEASURED AI time          : 8.67151 s\n');
fprintf('TRACE reference routeCode : %d\n',refRouteCode);
fprintf('Expected destination      : OPHTHALMOLOGY\n');
fprintf('Simulation stop time      : 300 s\n');
fprintf('============================================\n');

open_system(mdl);

end


% ============================================================
% FIND LEGACY BLOCK DESPITE LINE BREAKS IN LIBRARY NAME
% ============================================================

function blockPath = findLegacyBlock(rootLibrary,targetName)

blocks = find_system( ...
    rootLibrary, ...
    'LookUnderMasks','all', ...
    'FollowLinks','on', ...
    'Type','Block');

blockPath = '';

for k = 1:length(blocks)

    cleanName = strrep( ...
        blocks{k}, ...
        sprintf('\n'), ...
        ' ');

    if ~isempty(strfind(cleanName,targetName))
        blockPath = blocks{k};
        break;
    end
end

if isempty(blockPath)

    error( ...
        ['Unable to locate legacy SimEvents block: ' ...
         targetName]);

end

end


% ============================================================
% CONNECT ONE ENTITY OUTPUT TO DEFAULT ENTITY INPUT
% ============================================================

function connectEntity(model,source,destination,outputIndex)

if nargin < 4
    outputIndex = 1;
end

sourcePorts = get_param( ...
    source, ...
    'PortHandles');

destinationPorts = get_param( ...
    destination, ...
    'PortHandles');

outHandle = findEntityOutput( ...
    sourcePorts, ...
    outputIndex);

inHandle = findEntityInput( ...
    destinationPorts);

add_line( ...
    model, ...
    outHandle, ...
    inHandle);

end


% ============================================================
% CONNECT SPECIFIC ROUTER OUTPUT TO ENTITY INPUT
% ============================================================

function connectEntityOutput( ...
    model,source,destination,outputIndex)

sourcePorts = get_param( ...
    source, ...
    'PortHandles');

destinationPorts = get_param( ...
    destination, ...
    'PortHandles');

outHandle = findEntityOutput( ...
    sourcePorts, ...
    outputIndex);

inHandle = findEntityInput( ...
    destinationPorts);

add_line( ...
    model, ...
    outHandle, ...
    inHandle);

end


% ============================================================
% FIND LEGACY ENTITY OUTPUT HANDLE
% ============================================================

function h = findEntityOutput(portHandles,index)

% Legacy SimEvents generally exposes entity connections as
% right-side connection handles.

if isfield(portHandles,'RConn') && ...
        length(portHandles.RConn) >= index

    h = portHandles.RConn(index);
    return;
end

% Fallback only if this installation represents them as Outport.

if isfield(portHandles,'Outport') && ...
        length(portHandles.Outport) >= index

    h = portHandles.Outport(index);
    return;
end

error( ...
    'Could not resolve legacy SimEvents entity output port.');

end


% ============================================================
% FIND LEGACY ENTITY INPUT HANDLE
% ============================================================

function h = findEntityInput(portHandles)

% Legacy SimEvents generally exposes entity inputs as
% left-side connection handles.

if isfield(portHandles,'LConn') && ...
        ~isempty(portHandles.LConn)

    h = portHandles.LConn(1);
    return;
end

% Fallback only if represented as Inport.

if isfield(portHandles,'Inport') && ...
        ~isempty(portHandles.Inport)

    h = portHandles.Inport(1);
    return;
end

error( ...
    'Could not resolve legacy SimEvents entity input port.');

end