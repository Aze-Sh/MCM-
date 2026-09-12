function result = auditData(tbl, contract)
%AUDITDATA Non-mutating table quality audit.
arguments
    tbl table
    contract struct = struct()
end
names = tbl.Properties.VariableNames;
missing = struct();
nonfinite = struct();
for i = 1:numel(names)
    name = names{i};
    missing.(name) = sum(ismissing(tbl.(name)));
    if isnumeric(tbl.(name))
        nonfinite.(name) = sum(isinf(tbl.(name)));
    end
end
duplicateKeyRows = 0;
if isfield(contract, 'key')
    keys = cellstr(string(contract.key));
    if ~all(ismember(keys, names))
        error('cumcm:MissingKey', 'Contract key is absent from table.');
    end
    [~, ~, group] = unique(tbl(:, keys), 'rows', 'stable');
    counts = accumarray(group, 1);
    duplicateKeyRows = sum(counts(group) > 1);
end
values = struct('rows', height(tbl), 'columns', {names}, ...
    'missing', missing, 'nonfinite', nonfinite, ...
    'duplicateKeyRows', duplicateKeyRows);
result = struct('method', 'data-audit', 'values', values, ...
    'diagnostics', struct('mutated', false, 'contractChecked', ~isempty(fieldnames(contract))), ...
    'assumptions', {{'Missing, zero, and non-finite values have distinct meanings.'}});
end

