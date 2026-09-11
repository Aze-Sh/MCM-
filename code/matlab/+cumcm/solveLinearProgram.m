function result = solveLinearProgram(model)
%SOLVELINEARPROGRAM Solve an LP and preserve solver status.
arguments
    model struct
end
if exist('linprog', 'file') ~= 2
    error('cumcm:MissingToolbox', 'Optimization Toolbox linprog is required.');
end
required = {'f'};
if ~all(isfield(model, required))
    error('cumcm:InvalidModel', 'Model must contain objective f.');
end
fields = {'A','b','Aeq','beq','lb','ub'};
defaults = {[],[],[],[],[],[]};
args = cell(size(fields));
for i = 1:numel(fields)
    if isfield(model, fields{i}), args{i}=model.(fields{i}); else, args{i}=defaults{i}; end
end
options = optimoptions('linprog', 'Display', 'none');
[x, objective, exitflag, output] = linprog(model.f, args{:}, options);
success = exitflag > 0;
if success
    violation = 0;
    if ~isempty(args{1}), violation = max(0, max(args{1}*x-args{2})); end
    solution = x;
else
    violation = NaN;
    solution = [];
    objective = [];
end
values = struct('solution', solution, 'objective', objective);
diagnostics = struct('success', success, 'status', exitflag, ...
    'message', output.message, 'maxConstraintViolation', violation);
result = struct('method', 'lp-milp', 'values', values, ...
    'diagnostics', diagnostics, 'assumptions', {{'Objective is minimized without direction changes.'}});
end
