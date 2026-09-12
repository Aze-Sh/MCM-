% Export normalized MATLAB outputs for the transparent shared fixtures.
toolDir = fileparts(mfilename('fullpath'));
repoRoot = fileparts(toolDir);
addpath(fullfile(repoRoot, 'code', 'matlab'));
outputDir = fullfile(repoRoot, 'validation', 'output', 'matlab');
if ~isfolder(outputDir), mkdir(outputDir); end

T = table([1;1;3], [1;NaN;Inf], 'VariableNames', {'id','x'});
r = cumcm.auditData(T, struct('key', "id"));
writeNormalized('audit-basic-v1', struct('method',r.method,'values',struct( ...
    'missing',r.values.missing,'duplicate_key_rows',r.values.duplicateKeyRows), ...
    'diagnostics',r.diagnostics), outputDir);

r = cumcm.fitCandidates((0:3)', (1:2:7)', ["linear","quadratic"]);
writeNormalized('fit-linear-v1', struct('method',r.method,'values',struct( ...
    'best_model',char(r.values.bestModel),'coefficients',r.values.coefficients), ...
    'diagnostics',struct('rmse',r.diagnostics.rmse)), outputDir);

r = cumcm.fitCandidates((0:3)', [-2;1;4;7], "linear");
writeNormalized('regression-linear-v1', struct('method','regression-inference', ...
    'values',struct('coefficients',r.values.coefficients), ...
    'diagnostics',struct('rmse',r.diagnostics.rmse)), outputDir);

r = cumcm.forecastBacktest((1:8)', 2, ["naive","drift"]);
writeNormalized('forecast-seasonal-v1', struct('method',r.method,'values',struct( ...
    'best_model',char(r.values.bestModel),'forecast',r.values.forecast'), ...
    'diagnostics',struct('leakage_safe',r.diagnostics.leakageSafe)), outputDir);

if exist('linprog','file') == 2
    r = cumcm.solveLinearProgram(struct('f',[-1;-1],'A',[1 2],'b',4,'lb',[0;0]));
    writeNormalized('lp-basic-v1', struct('method',r.method,'values',struct( ...
        'objective',r.values.objective),'diagnostics',struct('success',r.diagnostics.success, ...
        'max_constraint_violation',r.diagnostics.maxConstraintViolation)), outputDir);
end

r = cumcm.solveNonlinearProblem(struct('objective',@(x)(x-2).^2,'x0',0));
writeNormalized('nonlinear-basic-v1', struct('method',r.method,'values',struct( ...
    'objective',r.values.objective),'diagnostics',struct('success',r.diagnostics.success, ...
    'local_optimum_only',r.diagnostics.localOptimumOnly)), outputDir);

G = graph([1 2 1],[2 3 3],[1 2 5],["a","b","c"]);
r = cumcm.shortestPathReport(G,"a","c");
writeNormalized('graph-shortest-v1', struct('method',r.method,'values',struct( ...
    'path',{cellstr(r.values.path)},'cost',r.values.cost), ...
    'diagnostics',struct('reachable',r.diagnostics.reachable)), outputDir);

r = cumcm.monteCarlo(@(~)2.5,4,7);
writeNormalized('monte-carlo-mean-v1', struct('method',r.method, ...
    'values',struct('mean',r.values.mean),'diagnostics',struct('n',4,'seed',7)), outputDir);

r = cumcm.solveOde(@(~,y)-y,[0 1],1,struct());
writeNormalized('ode-decay-v1', struct('method',r.method, ...
    'values',struct('y_final',r.values.y(end)),'diagnostics',struct('success',true)), outputDir);

r = cumcm.entropyTopsis([9 2;5 5;2 9],[true false]);
writeNormalized('topsis-basic-v1', struct('method',r.method,'values',struct( ...
    'ranking',r.values.ranking'-1,'weights',r.values.weights), ...
    'diagnostics',struct('feasible',true)), outputDir);

r = cumcm.evaluateModels([0;.1;1;1.1;2;2.1;3;3.1],[0;0;1;1;0;0;1;1],repelem((0:3)',2),"nearest-centroid");
writeNormalized('ml-classification-v1', struct('method',r.method, ...
    'values',struct('best_model',char(r.values.bestModel)), ...
    'diagnostics',struct('group_disjoint',r.diagnostics.groupDisjoint)), outputDir);

r = cumcm.sensitivityReport(@(p)2*p.x-3*p.y,struct('x',1,'y',2),struct('relativeStep',1e-5));
writeNormalized('sensitivity-linear-v1', struct('method',r.method, ...
    'values',struct('derivatives',r.values.derivatives), ...
    'diagnostics',struct('scheme',r.diagnostics.scheme)), outputDir);

fig = figure('Visible','off'); plot([0 1],[0 1]);
r = cumcm.saveFigure(fig,fullfile(outputDir,'plot-line-v1.png'),struct('fixture','plot-line-v1'));
close(fig);
writeNormalized('plot-line-v1', struct('method',r.method, ...
    'values',struct('dpi',r.values.dpi),'diagnostics',struct('exists',r.diagnostics.exists)), outputDir);

function writeNormalized(id, payload, outputDir)
path = fullfile(outputDir, string(id) + ".json");
fid = fopen(path,'w','n','UTF-8');
cleanup = onCleanup(@()fclose(fid));
fwrite(fid,jsonencode(payload,'PrettyPrint',true),'char');
end
