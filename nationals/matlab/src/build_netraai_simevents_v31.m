function modelFile = build_netraai_simevents_v31()
% BUILD_NETRAAI_SIMEVENTS_V31
%
% ANEYE / NetraAI Digital Twin V3.1
% MATLAB R2014a + SimEvents 4.3.2
%
% PURPOSE
% -------
% Correct the artificial synchronized-arrival behaviour of V3.
%
% V3:
%   Five generators fired simultaneously every 75 seconds.
%
% V3.1:
%   One patient generator every 15 seconds
%       ->
%   Round-robin splitter
%       ->
%   routeCode 1..5
%       ->
%   Population Merger
%       ->
%   Shared Capture / AI / TRACE pipeline
%
% Balanced 20% route assignment is an ENGINEERING TEST.
% It is NOT a clinical prevalence assumption.

clc

fprintf('\n');
fprintf('============================================\n');
fprintf(' ANEYE / NETRAAI DIGITAL TWIN V3.1\n');
fprintf(' DE-SYNCHRONIZED PATIENT ARRIVAL\n');
fprintf('============================================\n');

% ============================================================
% 1. PROJECT PATHS
% ============================================================

projectRoot = pwd;

srcDir = fullfile( ...
    projectRoot, ...
    'nationals', ...
    'matlab', ...
    'src');

modelDir = fullfile( ...
    projectRoot, ...
    'nationals', ...
    'simulink');

addpath(srcDir);

if ~exist(modelDir,'dir')
    mkdir(modelDir);
end

srcModel = 'NetraAI_DigitalTwin_V3';
mdl = 'NetraAI_DigitalTwin_V3_1';

srcModelFile = fullfile( ...
    modelDir, ...
    [srcModel '.mdl']);

modelFile = fullfile( ...
    modelDir, ...
    [mdl '.mdl']);

% ------------------------------------------------------------
% Confirm validated V3 exists
% ------------------------------------------------------------

if exist(srcModelFile,'file') ~= 2

    error( ...
        ['Validated V3 model not found: ' ...
         srcModelFile]);

end

fprintf('\nValidated V3 source:\n%s\n',srcModelFile);

% ============================================================
% 2. CLEAN ANY PREVIOUS V3.1 COPY
% ============================================================

try
    close_system(mdl,0);
catch
end

if exist(modelFile,'file') == 2

    delete(modelFile);

end

% ============================================================
% 3. CLONE VALIDATED V3
% ============================================================

fprintf('\nLoading validated V3...\n');

load_system(srcModelFile);

fprintf('V3 loaded.\n');

save_system( ...
    srcModel, ...
    modelFile);

fprintf('V3 copied to V3.1 model file.\n');

try
    close_system(srcModel,0);
catch
end

load_system(modelFile);

fprintf('Validated V3 model cloned successfully.\n');

% ============================================================
% 4. LOAD LEGACY SIMEVENTS LIBRARY
% ============================================================

load_system('simeventslib');

generatorLib = findLegacyBlock( ...
    'simeventslib', ...
    'Time-Based Entity Generator');

outputSwitchLib = ...
    'simeventslib/Routing/Output Switch';

% ============================================================
% 5. EXISTING ROUTE ATTRIBUTE BLOCKS
% ============================================================

setters = { ...
    [mdl '/Route1 Routine Attribute'], ...
    [mdl '/Route2 Referral Attribute'], ...
    [mdl '/Route3 HumanReview Attribute'], ...
    [mdl '/Route4 ReviewRecapture Attribute'], ...
    [mdl '/Route5 Recapture Attribute']};

% Verify all expected blocks exist.
for k = 1:5

    try
        get_param(setters{k},'Handle');
    catch
        error( ...
            ['Expected V3 route attribute block missing: ' ...
             setters{k}]);
    end

end

% ============================================================
% 6. REMOVE OLD SYNCHRONIZED GENERATORS
% ============================================================

oldGenerators = { ...
    [mdl '/Route1 Routine Generator'], ...
    [mdl '/Route2 Referral Generator'], ...
    [mdl '/Route3 HumanReview Generator'], ...
    [mdl '/Route4 ReviewRecapture Generator'], ...
    [mdl '/Route5 Recapture Generator']};

fprintf('\nRemoving synchronized V3 generators...\n');

for k = 1:length(oldGenerators)

    try

        delete_block(oldGenerators{k});

        fprintf( ...
            'Removed generator %d\n', ...
            k);

    catch ME

        fprintf( ...
            'Generator %d already absent or removal warning: %s\n', ...
            k, ...
            ME.message);

    end

end

% ============================================================
% 7. REFRESH AFTER GENERATOR REMOVAL
% ============================================================

try

    set_param( ...
        mdl, ...
        'SimulationCommand', ...
        'update');

catch ME

    fprintf( ...
        'Intermediate update warning: %s\n', ...
        ME.message);

end

% ============================================================
% 8. CLEAR OLD INPUT CONNECTIONS TO SET ATTRIBUTE BLOCKS
% ============================================================

fprintf('\nClearing inherited route-setter inputs...\n');

for k = 1:5

    disconnectEntityInput( ...
        setters{k}, ...
        1);

end

fprintf('Old route-setter input connections cleared.\n');

% ============================================================
% 9. CREATE SINGLE PATIENT ARRIVAL STREAM
% ============================================================

arrival = [mdl '/Patient Arrival'];

try
    delete_block(arrival);
catch
end

add_block( ...
    generatorLib, ...
    arrival, ...
    'Position', ...
    [20 205 145 255]);

set_param( ...
    arrival, ...
    'GenerateEntitiesUpon', ...
    'Intergeneration time from dialog');

set_param( ...
    arrival, ...
    'Distribution', ...
    'Constant');

% ASSUMPTION:
% one patient every 15 seconds
set_param( ...
    arrival, ...
    'Period', ...
    '15');

set_param( ...
    arrival, ...
    'GenerateEntityAtSimulationStart', ...
    'on');

set_param( ...
    arrival, ...
    'ResponseWhenBlocked', ...
    'Pause generation');

fprintf('Single 15-second patient stream created.\n');

% ============================================================
% 10. CREATE ROUND-ROBIN TRACE CLASS SPLITTER
% ============================================================

splitter = ...
    [mdl '/Balanced TRACE Class Splitter'];

try
    delete_block(splitter);
catch
end

add_block( ...
    outputSwitchLib, ...
    splitter, ...
    'Position', ...
    [180 145 305 345]);

set_param( ...
    splitter, ...
    'NumberOutputPorts', ...
    '5');

set_param( ...
    splitter, ...
    'SwitchingCriterion', ...
    'Round robin');

fprintf('Five-way round-robin TRACE splitter created.\n');

% ============================================================
% 11. REPOSITION ROUTE ATTRIBUTE BLOCKS
% ============================================================

setterY = [ ...
    40, ...
    135, ...
    230, ...
    325, ...
    420];

for k = 1:5

    set_param( ...
        setters{k}, ...
        'Position', ...
        [365 setterY(k) 500 setterY(k)+45]);

end

% ============================================================
% 12. VERIFY ROUTE ATTRIBUTE VALUES
% ============================================================

fprintf('\nChecking frozen routeCode values...\n');

for k = 1:5

    value = get_param( ...
        setters{k}, ...
        'AttributeValue');

    expected = num2str(k);

    fprintf( ...
        'Route class %d -> routeCode %s\n', ...
        k, ...
        value);

    if ~strcmp(value,expected)

        error( ...
            ['routeCode mismatch for route class ' ...
             num2str(k) ...
             '. Expected ' ...
             expected ...
             ' but found ' ...
             value]);

    end

end

% ============================================================
% 13. POPULATION MERGER
% ============================================================

merger = [mdl '/Population Merger'];

try
    get_param(merger,'Handle');
catch
    error('Population Merger block is missing from V3.');
end

set_param( ...
    merger, ...
    'Position', ...
    [555 155 675 355]);

% Existing:
%
% Set Attribute 1 \
% Set Attribute 2  \
% Set Attribute 3   -> Population Merger
% Set Attribute 4  /
% Set Attribute 5 /
%
% are intentionally preserved.

% ============================================================
% 14. PATIENT ARRIVAL -> ROUND-ROBIN SPLITTER
% ============================================================

safeConnectEntity( ...
    mdl, ...
    arrival, ...
    splitter);

fprintf('\nPatient Arrival -> TRACE Class Splitter connected.\n');

% ============================================================
% 15. SPLITTER OUTPUTS -> ROUTE ATTRIBUTE BLOCKS
% ============================================================

for k = 1:5

    safeConnectEntityOutput( ...
        mdl, ...
        splitter, ...
        setters{k}, ...
        k);

    fprintf( ...
        'Splitter output %d -> routeCode %d connected.\n', ...
        k, ...
        k);

end

fprintf('Round-robin TRACE class connections created.\n');

% ============================================================
% 16. STRUCTURAL UPDATE
% ============================================================

fprintf('\nUpdating model diagram...\n');

set_param( ...
    mdl, ...
    'SimulationCommand', ...
    'update');

fprintf('Model diagram update: PASS\n');

% ============================================================
% 17. VERIFY SPLITTER CONFIGURATION
% ============================================================

criterion = get_param( ...
    splitter, ...
    'SwitchingCriterion');

numPorts = get_param( ...
    splitter, ...
    'NumberOutputPorts');

fprintf('\nTRACE splitter criterion : %s\n',criterion);
fprintf('TRACE splitter outputs   : %s\n',numPorts);

if ~strcmp(criterion,'Round robin')

    error( ...
        'TRACE class splitter is not configured as Round robin.');

end

if ~strcmp(numPorts,'5')

    error( ...
        'TRACE class splitter does not have five outputs.');

end

fprintf('TRACE splitter configuration: PASS\n');

% ============================================================
% 18. VERIFY ORIGINAL TRACE OUTPUT ROUTER REMAINS CORRECT
% ============================================================

traceRouter = ...
    [mdl '/TRACE Router'];

traceCriterion = get_param( ...
    traceRouter, ...
    'SwitchingCriterion');

traceAttribute = get_param( ...
    traceRouter, ...
    'AttributeName');

traceOutputs = get_param( ...
    traceRouter, ...
    'NumberOutputPorts');

fprintf('\nTRACE decision router:\n');
fprintf('Criterion : %s\n',traceCriterion);
fprintf('Attribute : %s\n',traceAttribute);
fprintf('Outputs   : %s\n',traceOutputs);

if ~strcmp(traceCriterion,'From attribute')

    error( ...
        'Validated TRACE Router criterion was altered.');

end

if ~strcmp(traceAttribute,'routeCode')

    error( ...
        'Validated TRACE Router routeCode attribute was altered.');

end

if ~strcmp(traceOutputs,'5')

    error( ...
        'Validated TRACE Router output count was altered.');

end

fprintf('TRACE decision router integrity: PASS\n');

% ============================================================
% 19. SOLVER CONFIGURATION
% ============================================================

set_param( ...
    mdl, ...
    'Solver', ...
    'VariableStepDiscrete');

set_param( ...
    mdl, ...
    'MaxStep', ...
    '1');

set_param( ...
    mdl, ...
    'StopTime', ...
    '1200');

% ============================================================
% 20. MODEL DESCRIPTION
% ============================================================

descriptionText = [ ...
    'ANEYE / NetraAI Digital Twin V3.1. ' ...
    'A single deterministic patient stream generates one case ' ...
    'every 15 seconds. A round-robin splitter assigns balanced ' ...
    'TRACE engineering-test classes 1 through 5. ' ...
    'The balanced route distribution is not intended to represent ' ...
    'clinical prevalence. Shared capture, AI, review, and TRACE ' ...
    'routing resources are inherited from validated Digital Twin V3.'];

try

    set_param( ...
        mdl, ...
        'Description', ...
        descriptionText);

catch
end

% ============================================================
% 21. SAVE MODEL
% ============================================================

save_system( ...
    mdl, ...
    modelFile);

fprintf('\n');
fprintf('============================================\n');
fprintf(' NETRAAI V3.1 CREATED SUCCESSFULLY\n');
fprintf('============================================\n');

fprintf( ...
    'Arrival streams       : 1\n');

fprintf( ...
    'Patient period        : 15 s [ASSUMPTION]\n');

fprintf( ...
    'TRACE class splitter  : ROUND ROBIN\n');

fprintf( ...
    'Route mix             : 20%% each [ENGINEERING TEST]\n');

fprintf( ...
    'Capture time          : 12 s [ASSUMPTION]\n');

fprintf( ...
    'AI time               : 8.67151 s [MEASURED-1 CASE]\n');

fprintf( ...
    'Ophthalmology review  : 30 s [ASSUMPTION]\n');

fprintf( ...
    'Human review          : 45 s [ASSUMPTION]\n');

fprintf( ...
    'Simulation horizon    : 1200 s\n');

fprintf( ...
    'Model file            : %s\n', ...
    modelFile);

fprintf('============================================\n');

open_system(mdl);

end


% ============================================================
% FIND LEGACY SIMEVENTS BLOCK
% ============================================================

function blockPath = findLegacyBlock( ...
    rootLibrary, ...
    targetName)

blocks = find_system( ...
    rootLibrary, ...
    'LookUnderMasks', ...
    'all', ...
    'FollowLinks', ...
    'on', ...
    'Type', ...
    'Block');

blockPath = '';

for k = 1:length(blocks)

    cleanName = strrep( ...
        blocks{k}, ...
        sprintf('\n'), ...
        ' ');

    if ~isempty( ...
            strfind( ...
                cleanName, ...
                targetName))

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
% SAFE STANDARD ENTITY CONNECTION
% ============================================================

function safeConnectEntity( ...
    model, ...
    source, ...
    destination)

srcHandles = get_param( ...
    source, ...
    'PortHandles');

dstHandles = get_param( ...
    destination, ...
    'PortHandles');

srcPort = getEntityOutput( ...
    srcHandles, ...
    1);

dstPort = getEntityInput( ...
    dstHandles, ...
    1);

% Clear inherited lines if present.
disconnectPortLine(srcPort);
disconnectPortLine(dstPort);

add_line( ...
    model, ...
    srcPort, ...
    dstPort, ...
    'autorouting', ...
    'on');

end


% ============================================================
% SAFE SPECIFIC OUTPUT CONNECTION
% ============================================================

function safeConnectEntityOutput( ...
    model, ...
    source, ...
    destination, ...
    outputIndex)

srcHandles = get_param( ...
    source, ...
    'PortHandles');

dstHandles = get_param( ...
    destination, ...
    'PortHandles');

srcPort = getEntityOutput( ...
    srcHandles, ...
    outputIndex);

dstPort = getEntityInput( ...
    dstHandles, ...
    1);

% Critical R2014a compatibility cleanup.
disconnectPortLine(srcPort);
disconnectPortLine(dstPort);

add_line( ...
    model, ...
    srcPort, ...
    dstPort, ...
    'autorouting', ...
    'on');

end


% ============================================================
% DISCONNECT SPECIFIC ENTITY INPUT
% ============================================================

function disconnectEntityInput( ...
    blockPath, ...
    inputIndex)

portHandles = get_param( ...
    blockPath, ...
    'PortHandles');

inputPort = getEntityInput( ...
    portHandles, ...
    inputIndex);

disconnectPortLine(inputPort);

end


% ============================================================
% REMOVE LINE ATTACHED TO PORT
% ============================================================

function disconnectPortLine(portHandle)

if isempty(portHandle)
    return;
end

try

    lineHandle = get_param( ...
        portHandle, ...
        'Line');

    if ~isempty(lineHandle) && ...
            lineHandle ~= -1

        delete_line(lineHandle);

    end

catch
    % Port currently has no attached line.
end

end


% ============================================================
% GET LEGACY ENTITY OUTPUT PORT
% ============================================================

function h = getEntityOutput( ...
    portHandles, ...
    index)

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

error( ...
    ['Unable to resolve entity output port ' ...
     num2str(index) '.']);

end


% ============================================================
% GET LEGACY ENTITY INPUT PORT
% ============================================================

function h = getEntityInput( ...
    portHandles, ...
    index)

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

error( ...
    ['Unable to resolve entity input port ' ...
     num2str(index) '.']);

end