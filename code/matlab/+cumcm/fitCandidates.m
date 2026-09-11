function result = fitCandidates(x, y, candidates)
%FITCANDIDATES Fit linear and quadratic polynomial candidates.
arguments
    x (:,1) double
    y (:,1) double
    candidates = ["linear", "quadratic"]
end
if numel(x) ~= numel(y) || any(~isfinite(x)) || any(~isfinite(y))
    error('cumcm:InvalidData', 'x and y must have matching finite values.');
end
candidates = string(candidates);
rmse = zeros(size(candidates));
models = cell(size(candidates));
degrees = zeros(size(candidates));
for i = 1:numel(candidates)
    switch candidates(i)
        case "linear", degree = 1;
        case "quadratic", degree = 2;
        otherwise, error('cumcm:UnknownModel', 'Unknown fitting candidate.');
    end
    if numel(x) <= degree
        error('cumcm:InsufficientData', 'Insufficient observations.');
    end
    coefficient = polyfit(x, y, degree);
    prediction = polyval(coefficient, x);
    rmse(i) = sqrt(mean((y - prediction).^2));
    models{i} = struct('coefficient', coefficient, 'prediction', prediction);
    degrees(i) = degree;
end
minimum = min(rmse);
eligible = find(rmse <= minimum + max(1e-12, minimum * 1e-6));
[~, local] = min(degrees(eligible));
best = eligible(local);
values = struct('bestModel', candidates(best), ...
    'coefficients', models{best}.coefficient, ...
    'predictions', models{best}.prediction, 'candidateRmse', rmse);
result = struct('method', 'interpolation-fitting', 'values', values, ...
    'diagnostics', struct('rmse', rmse(best), 'n', numel(y)), ...
    'assumptions', {{'Polynomial use is restricted to the observed domain.'}});
end

