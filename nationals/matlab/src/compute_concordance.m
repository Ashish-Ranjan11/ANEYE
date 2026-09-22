function [score, status, support, conflict, limitations] = ...
    compute_concordance(grade, ma, he, ex, se, nv)
% COMPUTE_CONCORDANCE
% MATLAB R2014a port of NetraAI CONCORDANCE_V2.
%
% Inputs:
%   grade       ICDR grade 0..4
%   ma/he/ex/se lesion evidence, normalized 0..1
%   nv          independent NV evidence 0..1
%               use [] when NV model/evidence unavailable
%
% IMPORTANT:
%   This checks compatibility of independent retinal evidence
%   with the global grade. It does NOT overwrite the AI grade.

ma = clip01(ma);
he = clip01(he);
ex = clip01(ex);
se = clip01(se);

pathology = max([ma he ex se]);

support = {};
conflict = {};
limitations = {};

% ============================================================
% GRADE 0
% ============================================================
if grade == 0

    value = 1.0 - pathology;

    if pathology > 0.45
        conflict{end+1} = ...
            'Retinal lesion evidence is present despite a Grade-0 prediction.';
    else
        support{end+1} = ...
            'No strong independently detected DR-lesion evidence.';
    end

% ============================================================
% GRADE 1
% ============================================================
elseif grade == 1

    nonMA = max([he ex se]);

    value = ...
        0.65 * ma + ...
        0.35 * (1.0 - nonMA);

    if ma > 0.35
        support{end+1} = ...
            'Microaneurysm evidence supports mild NPDR.';
    end

    if nonMA > 0.55
        conflict{end+1} = ...
            'Additional lesion evidence is stronger than expected for an MA-only mild pattern.';
    end

% ============================================================
% GRADE 2
% ============================================================
elseif grade == 2

    additional = max([he ex se]);

    value = ...
        0.45 * ma + ...
        0.55 * additional;

    if ma > 0.30
        support{end+1} = ...
            'Microaneurysm evidence detected.';
    end

    if he > 0.35
        support{end+1} = ...
            'Hemorrhage evidence detected.';
    end

    if ex > 0.35
        support{end+1} = ...
            'Hard-exudate evidence detected.';
    end

    if se > 0.35
        support{end+1} = ...
            'Soft-exudate evidence detected.';
    end

    if additional < 0.25
        conflict{end+1} = ...
            'Weak additional lesion evidence for a moderate-NPDR prediction.';
    end

% ============================================================
% GRADE 3
% ============================================================
elseif grade == 3

    burden = sort([ma he ex se],'descend');

    genericBurden = mean(burden(1:3));

    % CONCORDANCE_V2 does not yet independently measure
    % full quadrant-aware 4-2-1 criteria.
    value = min(genericBurden,0.69);

    limitations{end+1} = ...
        'Full quadrant-aware 4-2-1 evidence is not independently measured.';

    if he > 0.55
        support{end+1} = ...
            'High hemorrhagic lesion evidence supports advanced retinal pathology.';
    end

    if genericBurden < 0.40
        conflict{end+1} = ...
            'Severe-grade prediction has weak supporting lesion burden.';
    end

% ============================================================
% GRADE 4
% ============================================================
else

    advancedBurden = max([he ex se]);

    if isempty(nv)

        value = min(0.45 * pathology,0.49);

        limitations{end+1} = ...
            'Independent neovascularization detector is not available.';

        conflict{end+1} = ...
            'PDR prediction cannot be independently supported with NV evidence.';

        if advancedBurden > 0.50
            support{end+1} = ...
                'Advanced retinal pathology evidence is present.';
        end

    else

        nv = clip01(nv);

        value = ...
            0.70 * nv + ...
            0.30 * advancedBurden;

        if nv >= 0.50
            support{end+1} = ...
                'Independent neovascularization evidence supports the PDR prediction.';
        else
            conflict{end+1} = ...
                'PDR prediction has weak independent neovascularization evidence.';
        end

    end
end

value = clip01(value);

% Python round(...,1) equivalent for positive score.
score = round(value * 1000) / 10;

% CONCORDANCE_V2 classification
if score >= 75.0 && isempty(conflict)
    status = 'HIGH';
elseif score >= 50.0
    status = 'MODERATE';
else
    status = 'LOW';
end

end


function x = clip01(x)

x = double(x);

if x < 0
    x = 0;
elseif x > 1
    x = 1;
end

end