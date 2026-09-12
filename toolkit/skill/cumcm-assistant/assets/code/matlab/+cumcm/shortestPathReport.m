function result = shortestPathReport(G, source, target)
%SHORTESTPATHREPORT Return path and independently recomputed edge cost.
arguments
    G graph
    source
    target
end
[path, reported] = shortestpath(G, source, target);
if isempty(path)
    error('cumcm:NoPath', 'No path exists between source and target.');
end
cost = 0;
for i = 1:numel(path)-1
    edge = findedge(G, path(i), path(i+1));
    if isempty(G.Edges.Weight), cost = cost + 1; else, cost = cost + G.Edges.Weight(edge); end
end
if abs(cost-reported) > 1e-10
    error('cumcm:CostMismatch', 'Independent path cost does not match graph result.');
end
values = struct('path', path, 'cost', cost);
result = struct('method', 'graph-flow-routing', 'values', values, ...
    'diagnostics', struct('reachable', true, 'edgeCount', numel(path)-1), ...
    'assumptions', {{'Edge weights are additive and nonnegative.'}});
end

