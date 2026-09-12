function result = auditTable(tbl, contract)
%AUDITTABLE Compatibility alias for auditData.
if nargin < 2
    contract = struct();
end
result = cumcm.auditData(tbl, contract);
end

