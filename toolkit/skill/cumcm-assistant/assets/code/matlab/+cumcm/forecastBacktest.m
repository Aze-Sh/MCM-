function result = forecastBacktest(y, horizon, models)
%FORECASTBACKTEST Expanding-window naive and drift backtest.
arguments
    y (:,1) double
    horizon (1,1) double {mustBeInteger,mustBePositive}
    models = ["naive", "drift"]
end
if any(~isfinite(y)) || numel(y) < max(6, 2*horizon + 2)
    error('cumcm:InsufficientData', 'Insufficient finite series length.');
end
models = string(models);
origins = max(4, horizon + 2):(numel(y) - horizon + 1);
errors = zeros(numel(models), numel(origins));
for oi = 1:numel(origins)
    origin = origins(oi);
    train = y(1:origin-1);
    actual = y(origin:origin+horizon-1);
    for mi = 1:numel(models)
        prediction = localForecast(train, horizon, models(mi));
        errors(mi, oi) = mean(abs(actual - prediction));
    end
end
meanError = mean(errors, 2);
[~, best] = min(meanError);
prediction = localForecast(y, horizon, models(best));
values = struct('bestModel', models(best), 'forecast', prediction, 'mae', meanError);
result = struct('method', 'time-series', 'values', values, ...
    'diagnostics', struct('originCount', numel(origins), 'leakageSafe', true), ...
    'assumptions', {{'Recent trend persists over the forecast horizon.'}});
end

function prediction = localForecast(train, horizon, model)
if model == "naive"
    prediction = repmat(train(end), horizon, 1);
elseif model == "drift"
    slope = (train(end)-train(1))/(numel(train)-1);
    prediction = train(end) + slope*(1:horizon)';
else
    error('cumcm:UnknownModel', 'Unknown forecast model.');
end
end

