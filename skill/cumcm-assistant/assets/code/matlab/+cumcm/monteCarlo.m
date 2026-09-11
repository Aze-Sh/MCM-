function result = monteCarlo(simulator, n, seed)
%MONTECARLO Reproducible scalar replications using a local stream.
arguments
    simulator function_handle
    n (1,1) double {mustBeInteger,mustBeGreaterThanOrEqual(n,2)}
    seed (1,1) double {mustBeInteger} = 0
end
stream = RandStream('mt19937ar', 'Seed', seed);
samples = zeros(n,1);
for i = 1:n
    samples(i) = simulator(stream);
end
if any(~isfinite(samples))
    error('cumcm:InvalidSimulation', 'Simulator returned non-finite output.');
end
mu = mean(samples);
se = std(samples,0)/sqrt(n);
values = struct('mean', mu, 'ci95', [mu-1.96*se, mu+1.96*se], 'samples', samples);
result = struct('method', 'monte-carlo-des', 'values', values, ...
    'diagnostics', struct('n', n, 'seed', seed, 'standardError', se), ...
    'assumptions', {{'Replications are independent under the simulator.'}});
end

