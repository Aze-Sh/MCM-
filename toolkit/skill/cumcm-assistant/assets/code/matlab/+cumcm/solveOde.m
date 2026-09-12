function result = solveOde(rhs, tspan, y0, options)
%SOLVEODE Solve an increasing-time IVP with explicit tolerances.
arguments
    rhs function_handle
    tspan (1,:) double
    y0 (:,1) double
    options struct = struct()
end
if numel(tspan) < 2 || any(diff(tspan) <= 0) || any(~isfinite(y0))
    error('cumcm:InvalidOde', 'Time must increase and initial state must be finite.');
end
odeOptions = odeset('RelTol',1e-8,'AbsTol',1e-10);
if isfield(options,'RelTol'), odeOptions=odeset(odeOptions,'RelTol',options.RelTol); end
if isfield(options,'AbsTol'), odeOptions=odeset(odeOptions,'AbsTol',options.AbsTol); end
[t,y] = ode45(rhs, tspan, y0, odeOptions);
values = struct('t', t, 'y', y);
result = struct('method', 'ode-difference', 'values', values, ...
    'diagnostics', struct('success', true, 'steps', numel(t)), ...
    'assumptions', {{'The right-hand side is valid over the interval.'}});
end

