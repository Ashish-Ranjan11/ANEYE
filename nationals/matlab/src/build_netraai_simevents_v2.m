function modelFile = build_netraai_simevents_v2()
% BUILD_NETRAAI_SIMEVENTS_V2
%
% ANEYE / NetraAI TRACE-DR Digital Twin V2
% MATLAB R2014a + SimEvents 4.3.2
%
% V2 adds:
%   - five TRACE patient classes
%   - shared capture resource
%   - shared AI resource
%   - actual attribute-based TRACE routing
%   - ophthalmology review queue/server
%   - human review queue/server
%   - route counters
%
% IMPORTANT:
% Route mix is a SYNTHETIC BALANCED ENGINEERING TEST.
% It is NOT a clinical prevalence estimate.

clc

fprintf('\n============================================\n');
fprintf(' ANEYE / NETRAAI DIGITAL TWIN V2\n');
fprintf(' MIXED TRACE POPULATION\n');
fprintf('============================================\n');

srcDir = fullfile(pwd,'nationals','matlab','src');
addpath(srcDir);

load_system('simeventslib');

% ------------------------------------------------------------
% TRUST CONTRACT
% ------------------------------------------------------------
C = netraai_trust_contract();

fprintf('\nTrust Contract : %s\n', ...
    C.system.contractVersion);

fprintf('Routing        : %s\n', ...
    C.trust.routingVersion);

% ------------------------------------------------------------
% LIBRARY BLOCKS
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

inputSwitchLib = ...
    'simeventslib/Routing/Input Switch';

outputSwitchLib = ...
    'simeventslib/Routing/Output Switch';

setAttributeLib = ...
    'simeventslib/Attributes/Set Attribute';

% ------------------------------------------------------------
% MODEL
% ------------------------------------------------------------
mdl = 'NetraAI_DigitalTwin_V2';

modelDir = fullfile( ...
    pwd,'nationals','simulink');

if ~exist(modelDir,'dir')
    mkdir(modelDir);
end

modelFile = fullfile( ...
    modelDir,[mdl '.mdl']);

try
    close_system(mdl,0);
catch
end

if exist(modelFile,'file')
    delete(modelFile);
end

new_system(mdl);

set_param(mdl,'StopTime','1200');
set_param(mdl,'Solver','VariableStepDiscrete');
set_param(mdl,'MaxStep','1');

% ============================================================
% 1. FIVE SYNTHETIC TRACE POPULATIONS
% ============================================================
%
% Each generator produces one entity every 75 s.
% Five generators together -> mean 1 entity / 15 s.
%
% This yields a balanced route test:
% 20% Route1
% 20% Route2
% 20% Route3
% 20% Route4
% 20% Route5
%
% ASSUMPTION ONLY.

routeLabels = { ...
    'Route1 Routine', ...
    'Route2 Referral', ...
    'Route3 HumanReview', ...
    'Route4 ReviewRecapture', ...
    'Route5 Recapture'};

generatorY = [40 135 230 325 420];

generators = cell(1,5);
setters = cell(1,5);

for k = 1:5

    generators{k} = ...
        [mdl '/' routeLabels{k} ' Generator'];

    setters{k} = ...
        [mdl '/' routeLabels{k} ' Attribute'];

    add_block( ...
        generatorLib, ...
        generators{k}, ...
        'Position', ...
        [30 generatorY(k) 150 generatorY(k)+45]);

    set_param( ...
        generators{k}, ...
        'GenerateEntitiesUpon', ...
        'Intergeneration time from dialog');

    set_param( ...
        generators{k}, ...
        'Distribution','Constant');

    set_param( ...
        generators{k}, ...
        'Period','75');

    set_param( ...
        generators{k}, ...
        'GenerateEntityAtSimulationStart','on');

    set_param( ...
        generators{k}, ...
        'ResponseWhenBlocked','Pause generation');

    add_block( ...
        setAttributeLib, ...
        setters{k}, ...
        'Position', ...
        [185 generatorY(k) 315 generatorY(k)+45]);

    set_param( ...
        setters{k}, ...
        'AttributeName','routeCode');

    set_param( ...
        setters{k}, ...
        'AttributeFrom','Dialog');

    set_param( ...
        setters{k}, ...
        'AttributeValue',num2str(k));

    set_param( ...
        setters{k}, ...
        'AttributeCreate','on');

end

% ============================================================
% 2. MERGE ALL PATIENT TYPES
% ============================================================

merger = [mdl '/Population Merger'];

add_block( ...
    inputSwitchLib, ...
    merger, ...
    'Position',[365 155 485 355]);

set_param( ...
    merger, ...
    'NumberInputPorts','5');

set_param( ...
    merger, ...
    'SwitchingCriterion','Round robin');

% ============================================================
% 3. SHARED FUNDUS CAPTURE RESOURCE
% ============================================================

captureQueue = [mdl '/Capture Queue'];
captureServer = [mdl '/Fundus Capture'];

add_block( ...
    queueLib, ...
    captureQueue, ...
    'Position',[540 220 640 270]);

set_param( ...
    captureQueue, ...
    'Capacity','100');

add_block( ...
    serverLib, ...
    captureServer, ...
    'Position',[690 220 810 270]);

set_param( ...
    captureServer, ...
    'ServiceTimeFrom','Dialog');

% ASSUMPTION
set_param( ...
    captureServer, ...
    'ServiceTime','12');

% ============================================================
% 4. SHARED AI RESOURCE
% ============================================================

aiQueue = [mdl '/AI Queue'];
aiServer = [mdl '/TRACE AI Processing'];

add_block( ...
    queueLib, ...
    aiQueue, ...
    'Position',[860 220 960 270]);

set_param( ...
    aiQueue, ...
    'Capacity','100');

add_block( ...
    serverLib, ...
    aiServer, ...
    'Position',[1010 220 1145 270]);

set_param( ...
    aiServer, ...
    'ServiceTimeFrom','Dialog');

% MEASURED - ONE REFERENCE CASE
set_param( ...
    aiServer, ...
    'ServiceTime','8.67151');

% ============================================================
% 5. TRACE OUTPUT ROUTER
% ============================================================

router = [mdl '/TRACE Router'];

add_block( ...
    outputSwitchLib, ...
    router, ...
    'Position',[1200 145 1320 345]);

set_param( ...
    router, ...
    'NumberOutputPorts','5');

set_param( ...
    router, ...
    'SwitchingCriterion','From attribute');

set_param( ...
    router, ...
    'AttributeName','routeCode');

% ============================================================
% 6. ROUTE 1 - ROUTINE
% ============================================================

routineSink = [mdl '/1 ROUTINE'];

add_block( ...
    sinkLib, ...
    routineSink, ...
    'Position',[1580 30 1710 70]);

set_param( ...
    routineSink, ...
    'StatNumberArrived','on');

% ============================================================
% 7. ROUTE 2 - OPHTHALMOLOGY
% ============================================================

ophQueue = [mdl '/Ophthalmology Queue'];
ophServer = [mdl '/Ophthalmologist Review'];
ophSink = [mdl '/2 OPHTHALMOLOGY'];

add_block( ...
    queueLib, ...
    ophQueue, ...
    'Position',[1400 110 1500 155]);

set_param( ...
    ophQueue, ...
    'Capacity','100');

add_block( ...
    serverLib, ...
    ophServer, ...
    'Position',[1540 110 1665 155]);

set_param( ...
    ophServer, ...
    'ServiceTimeFrom','Dialog');

% ASSUMPTION for V2
set_param( ...
    ophServer, ...
    'ServiceTime','30');

add_block( ...
    sinkLib, ...
    ophSink, ...
    'Position',[1710 110 1840 155]);

set_param( ...
    ophSink, ...
    'StatNumberArrived','on');

% ============================================================
% 8. ROUTE 3 - HUMAN REVIEW
% ============================================================

humanQueue = [mdl '/Human Review Queue'];
humanServer = [mdl '/Human Reviewer'];
humanSink = [mdl '/3 HUMAN REVIEW'];

add_block( ...
    queueLib, ...
    humanQueue, ...
    'Position',[1400 205 1500 250]);

set_param( ...
    humanQueue, ...
    'Capacity','100');

add_block( ...
    serverLib, ...
    humanServer, ...
    'Position',[1540 205 1665 250]);

set_param( ...
    humanServer, ...
    'ServiceTimeFrom','Dialog');

% ASSUMPTION for V2
set_param( ...
    humanServer, ...
    'ServiceTime','45');

add_block( ...
    sinkLib, ...
    humanSink, ...
    'Position',[1710 205 1840 250]);

set_param( ...
    humanSink, ...
    'StatNumberArrived','on');

% ============================================================
% 9. ROUTE 4 - REVIEW / RECAPTURE DEMAND
% ============================================================

reviewSink = [mdl '/4 REVIEW RECAPTURE'];

add_block( ...
    sinkLib, ...
    reviewSink, ...
    'Position',[1580 315 1740 360]);

set_param( ...
    reviewSink, ...
    'StatNumberArrived','on');

% ============================================================
% 10. ROUTE 5 - RECAPTURE DEMAND
% ============================================================

recaptureSink = [mdl '/5 RECAPTURE'];

add_block( ...
    sinkLib, ...
    recaptureSink, ...
    'Position',[1580 410 1710 455]);

set_param( ...
    recaptureSink, ...
    'StatNumberArrived','on');

% ============================================================
% 11. CONNECT GENERATORS TO ATTRIBUTES
% ============================================================

for k = 1:5

    connectEntity( ...
        mdl, ...
        generators{k}, ...
        setters{k});

end

% ============================================================
% 12. ATTRIBUTES TO FIVE INPUT-SWITCH PORTS
% ============================================================

for k = 1:5

    connectEntityToInput( ...
        mdl, ...
        setters{k}, ...
        merger, ...
        k);

end

% ============================================================
% 13. SHARED RESOURCE PIPELINE
% ============================================================

connectEntity(mdl,merger,captureQueue);
connectEntity(mdl,captureQueue,captureServer);
connectEntity(mdl,captureServer,aiQueue);
connectEntity(mdl,aiQueue,aiServer);
connectEntity(mdl,aiServer,router);

% ============================================================
% 14. TRACE OUTPUT CONNECTIONS
% ============================================================

connectEntityOutput( ...
    mdl,router,routineSink,1);

connectEntityOutput( ...
    mdl,router,ophQueue,2);

connectEntity(mdl,ophQueue,ophServer);
connectEntity(mdl,ophServer,ophSink);

connectEntityOutput( ...
    mdl,router,humanQueue,3);

connectEntity(mdl,humanQueue,humanServer);
connectEntity(mdl,humanServer,humanSink);

connectEntityOutput( ...
    mdl,router,reviewSink,4);

connectEntityOutput( ...
    mdl,router,recaptureSink,5);

% ============================================================
% 15. UPDATE MODEL TO EXPOSE STATISTICS PORTS
% ============================================================

set_param(mdl,'SimulationCommand','update');

% ============================================================
% 16. ADD ROUTE COUNTERS
% ============================================================

sinks = { ...
    routineSink, ...
    ophSink, ...
    humanSink, ...
    reviewSink, ...
    recaptureSink};

varNames = { ...
    'v2Route1', ...
    'v2Route2', ...
    'v2Route3', ...
    'v2Route4', ...
    'v2Route5'};

loggerY = [30 110 205 315 410];

for k = 1:5

    logger = ...
        [mdl '/Route ' num2str(k) ' Count'];

    add_block( ...
        'simulink/Sinks/To Workspace', ...
        logger, ...
        'VariableName',varNames{k}, ...
        'SaveFormat','Array', ...
        'Position', ...
        [1900 loggerY(k) 2015 loggerY(k)+35]);

    sinkPorts = get_param( ...
        sinks{k}, ...
        'PortHandles');

    loggerPorts = get_param( ...
        logger, ...
        'PortHandles');

    add_line( ...
        mdl, ...
        sinkPorts.Outport(1), ...
        loggerPorts.Inport(1), ...
        'autorouting','on');

end

% ============================================================
% 17. SAVE
% ============================================================

save_system( ...
    mdl, ...
    modelFile);

fprintf('\n============================================\n');
fprintf(' NETRAAI DIGITAL TWIN V2 CREATED\n');
fprintf('============================================\n');

fprintf('Synthetic route mix      : BALANCED 20%% each\n');
fprintf('Each route period        : 75 s\n');
fprintf('Combined mean arrival    : 15 s\n');
fprintf('Capture service          : 12 s [ASSUMPTION]\n');
fprintf('AI service               : 8.67151 s [MEASURED-1 CASE]\n');
fprintf('Ophthalmology review     : 30 s [ASSUMPTION]\n');
fprintf('Human review             : 45 s [ASSUMPTION]\n');
fprintf('Simulation horizon       : 1200 s\n');

fprintf('\nModel:\n%s\n',modelFile);

fprintf('============================================\n');

open_system(mdl);

end


% ============================================================
% LEGACY BLOCK FINDER
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
    error(['Block not found: ' targetName]);
end

end


% ============================================================
% STANDARD ENTITY CONNECTION
% ============================================================

function connectEntity(model,source,destination)

src = get_param(source,'PortHandles');
dst = get_param(destination,'PortHandles');

srcPort = getEntityOutput(src,1);
dstPort = getEntityInput(dst,1);

add_line(model,srcPort,dstPort);

end


% ============================================================
% CONNECT TO SPECIFIC INPUT PORT
% ============================================================

function connectEntityToInput( ...
    model,source,destination,inputIndex)

src = get_param(source,'PortHandles');
dst = get_param(destination,'PortHandles');

srcPort = getEntityOutput(src,1);
dstPort = getEntityInput(dst,inputIndex);

add_line(model,srcPort,dstPort);

end


% ============================================================
% CONNECT SPECIFIC OUTPUT PORT
% ============================================================

function connectEntityOutput( ...
    model,source,destination,outputIndex)

src = get_param(source,'PortHandles');
dst = get_param(destination,'PortHandles');

srcPort = getEntityOutput(src,outputIndex);
dstPort = getEntityInput(dst,1);

add_line(model,srcPort,dstPort);

end


% ============================================================
% ENTITY OUTPUT
% ============================================================

function h = getEntityOutput(portHandles,index)

if isfield(portHandles,'RConn') && ...
        length(portHandles.RConn) >= index

    h = portHandles.RConn(index);
    return;
end

if isfield(portHandles,'Outport') && ...
        length(portHandles.Outport) >= index

    h = portHandles.Outport(index);
    return;
end

error('Unable to resolve entity output port.');

end


% ============================================================
% ENTITY INPUT
% ============================================================

function h = getEntityInput(portHandles,index)

if isfield(portHandles,'LConn') && ...
        length(portHandles.LConn) >= index

    h = portHandles.LConn(index);
    return;
end

if isfield(portHandles,'Inport') && ...
        length(portHandles.Inport) >= index

    h = portHandles.Inport(index);
    return;
end

error('Unable to resolve entity input port.');

end