function modelFile = instrument_netraai_v3()
% INSTRUMENT_NETRAAI_V3
%
% Adds operational metrics to the validated V2 model.
%
% MEASURED/SIMULATED:
%   - queue average waiting time
%   - resource utilization
%   - route throughput
%
% NOTE:
% Current patient mix is the balanced synthetic engineering
% scenario from V2, not a clinical prevalence model.

clc

srcModel = 'NetraAI_DigitalTwin_V2';
mdl = 'NetraAI_DigitalTwin_V3';

modelDir = fullfile(pwd,'nationals','simulink');
modelFile = fullfile(modelDir,[mdl '.mdl']);

try
    close_system(mdl,0);
catch
end

if exist(modelFile,'file')
    delete(modelFile);
end

load_system(srcModel);

% Save V2 as a separate V3 model.
save_system(srcModel,modelFile);

close_system(srcModel,0);
load_system(modelFile);

% ------------------------------------------------------------
% RENAME EXISTING ROUTE COUNTER VARIABLES
% ------------------------------------------------------------

for k = 1:5

    logger = [mdl '/Route ' num2str(k) ' Count'];

    set_param( ...
        logger, ...
        'VariableName', ...
        ['v3Route' num2str(k)]);

end

% ------------------------------------------------------------
% QUEUE WAIT STATISTICS
% Only ONE statistic enabled per queue so the output port
% is unambiguous in legacy SimEvents.
% ------------------------------------------------------------

queues = { ...
    [mdl '/Capture Queue'], ...
    [mdl '/AI Queue'], ...
    [mdl '/Ophthalmology Queue'], ...
    [mdl '/Human Review Queue']};

queueVars = { ...
    'v3CaptureWait', ...
    'v3AIWait', ...
    'v3OphWait', ...
    'v3HumanWait'};

for k = 1:length(queues)

    set_param(queues{k},'StatAverageWait','on');

    % Keep other optional statistics disabled.
    set_param(queues{k},'StatNumberDeparted','off');
    set_param(queues{k},'StatNumberInBlock','off');
    set_param(queues{k},'StatAverageQueueLength','off');
    set_param(queues{k},'StatNumberTimedout','off');

end

% ------------------------------------------------------------
% SERVER UTILIZATION STATISTICS
% ------------------------------------------------------------

servers = { ...
    [mdl '/Fundus Capture'], ...
    [mdl '/TRACE AI Processing'], ...
    [mdl '/Ophthalmologist Review'], ...
    [mdl '/Human Reviewer']};

serverVars = { ...
    'v3CaptureUtil', ...
    'v3AIUtil', ...
    'v3OphUtil', ...
    'v3HumanUtil'};

for k = 1:length(servers)

    set_param(servers{k},'StatUtilization','on');

    set_param(servers{k},'StatNumberDeparted','off');
    set_param(servers{k},'StatNumberInBlock','off');
    set_param(servers{k},'StatNumberPreempted','off');
    set_param(servers{k},'StatPendingEntity','off');
    set_param(servers{k},'StatAverageWait','off');
    set_param(servers{k},'StatNumberTimedout','off');

end

% Create statistics ports.
set_param(mdl,'SimulationCommand','update');

% ------------------------------------------------------------
% ADD QUEUE WAIT LOGGERS
% ------------------------------------------------------------

for k = 1:length(queues)

    logger = [mdl '/Metric Queue ' num2str(k)];

    add_block( ...
        'simulink/Sinks/To Workspace', ...
        logger, ...
        'VariableName',queueVars{k}, ...
        'SaveFormat','Array', ...
        'Position', ...
        [2100 40+(k-1)*65 2220 70+(k-1)*65]);

    ph = get_param(queues{k},'PortHandles');
    lh = get_param(logger,'PortHandles');

    if isempty(ph.Outport)
        error(['No statistics port on queue ' num2str(k)]);
    end

    add_line( ...
        mdl, ...
        ph.Outport(1), ...
        lh.Inport(1), ...
        'autorouting','on');

end

% ------------------------------------------------------------
% ADD UTILIZATION LOGGERS
% ------------------------------------------------------------

for k = 1:length(servers)

    logger = [mdl '/Metric Util ' num2str(k)];

    add_block( ...
        'simulink/Sinks/To Workspace', ...
        logger, ...
        'VariableName',serverVars{k}, ...
        'SaveFormat','Array', ...
        'Position', ...
        [2280 40+(k-1)*65 2400 70+(k-1)*65]);

    ph = get_param(servers{k},'PortHandles');
    lh = get_param(logger,'PortHandles');

    if isempty(ph.Outport)
        error(['No utilization port on server ' num2str(k)]);
    end

    add_line( ...
        mdl, ...
        ph.Outport(1), ...
        lh.Inport(1), ...
        'autorouting','on');

end

% ------------------------------------------------------------
% SOLVER
% ------------------------------------------------------------

set_param(mdl,'Solver','VariableStepDiscrete');
set_param(mdl,'MaxStep','1');

save_system(mdl);

fprintf('\n============================================\n');
fprintf(' NETRAAI DIGITAL TWIN V3 INSTRUMENTED\n');
fprintf('============================================\n');
fprintf('Capture queue wait       : enabled\n');
fprintf('AI queue wait            : enabled\n');
fprintf('Ophthalmology queue wait : enabled\n');
fprintf('Human review queue wait  : enabled\n');
fprintf('Capture utilization      : enabled\n');
fprintf('AI utilization           : enabled\n');
fprintf('Ophthalmology utilization: enabled\n');
fprintf('Human-review utilization : enabled\n');
fprintf('============================================\n');

open_system(mdl);

end