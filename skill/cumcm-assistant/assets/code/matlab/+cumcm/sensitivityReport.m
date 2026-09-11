function result = sensitivityReport(model, parameters, design)
%SENSITIVITYREPORT Central finite-difference local sensitivities.
arguments
    model function_handle
    parameters struct
    design struct = struct()
end
if isfield(design,'relativeStep'), relativeStep=design.relativeStep; else, relativeStep=1e-4; end
if relativeStep<=0 || relativeStep>=1
    error('cumcm:InvalidStep','Relative step must be between zero and one.');
end
names=fieldnames(parameters);
if isempty(names), error('cumcm:InvalidParameters','Parameters cannot be empty.'); end
derivatives=struct();
steps=struct();
for i=1:numel(names)
    name=names{i}; value=parameters.(name);
    if ~isscalar(value) || ~isfinite(value), error('cumcm:InvalidParameters','All parameters must be finite scalars.'); end
    step=relativeStep*max(1,abs(value));
    upper=parameters; lower=parameters;
    upper.(name)=value+step; lower.(name)=value-step;
    derivatives.(name)=(model(upper)-model(lower))/(2*step);
    steps.(name)=step;
end
values=struct('baseline',model(parameters),'derivatives',derivatives);
result=struct('method','sensitivity-robustness','values',values, ...
    'diagnostics',struct('relativeStep',relativeStep,'absoluteSteps',steps,'scheme','central'), ...
    'assumptions',{{'The model is locally smooth.'}});
end

