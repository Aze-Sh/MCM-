classdef TestCore < matlab.unittest.TestCase
    methods (Test)
        function auditDetectsMissingAndDuplicates(testCase)
            T = table([1;1;3], [1;NaN;Inf], 'VariableNames', {'id','x'});
            result = cumcm.auditTable(T, struct('key', "id"));
            testCase.verifyEqual(result.values.missing.x, 1);
            testCase.verifyEqual(result.values.nonfinite.x, 1);
            testCase.verifyEqual(result.values.duplicateKeyRows, 2);
        end

        function fittingRecoversExactLinearModel(testCase)
            result = cumcm.fitCandidates((0:3)', (1:2:7)', ...
                ["linear", "quadratic"]);
            testCase.verifyEqual(result.values.bestModel, "linear");
            testCase.verifyEqual(result.values.coefficients, [2 1], ...
                'AbsTol', 1e-10);
        end

        function regressionRecoversKnownCoefficients(testCase)
            result = cumcm.fitCandidates((0:3)', [-2;1;4;7], "linear");
            testCase.verifyEqual(result.values.coefficients, [3 -2], ...
                'AbsTol', 1e-10);
        end

        function forecastSelectsDriftForArithmeticTrend(testCase)
            result = cumcm.forecastBacktest((1:8)', 2, ["naive", "drift"]);
            testCase.verifyEqual(result.values.bestModel, "drift");
            testCase.verifyEqual(result.values.forecast, [9;10], ...
                'AbsTol', 1e-10);
            testCase.verifyTrue(result.diagnostics.leakageSafe);
        end

        function linearProgramFindsCheckedVertex(testCase)
            testCase.assumeTrue(exist('linprog', 'file') == 2, ...
                'Optimization Toolbox is not installed.');
            model = struct('f', [-1;-1], 'A', [1 2], 'b', 4, ...
                'lb', [0;0]);
            result = cumcm.solveLinearProgram(model);
            testCase.verifyTrue(result.diagnostics.success);
            testCase.verifyEqual(result.values.objective, -4, ...
                'AbsTol', 1e-8);
            testCase.verifyLessThanOrEqual( ...
                result.diagnostics.maxConstraintViolation, 1e-8);
        end

        function nonlinearProblemFindsKnownMinimum(testCase)
            problem = struct('objective', @(x)(x-2).^2, 'x0', 0);
            result = cumcm.solveNonlinearProblem(problem);
            testCase.verifyTrue(result.diagnostics.success);
            testCase.verifyEqual(result.values.solution, 2, 'AbsTol', 1e-5);
            testCase.verifyEqual(result.values.objective, 0, 'AbsTol', 1e-8);
            testCase.verifyTrue(result.diagnostics.localOptimumOnly);
        end

        function dominantAlternativeRanksFirst(testCase)
            X = [9 2; 5 5; 2 9];
            result = cumcm.entropyTopsis(X, [true false]);
            testCase.verifyEqual(result.values.ranking(1), 1);
            testCase.verifyEqual(sum(result.values.weights), 1, 'AbsTol', 1e-10);
        end

        function monteCarloIsReproducible(testCase)
            one = cumcm.monteCarlo(@(stream) randn(stream), 100, 7);
            two = cumcm.monteCarlo(@(stream) randn(stream), 100, 7);
            testCase.verifyEqual(one.values.samples, two.values.samples);
        end

        function odeMatchesDecay(testCase)
            result = cumcm.solveOde(@(~, y) -y, [0 1], 1, struct());
            testCase.verifyEqual(result.values.y(end), exp(-1), 'RelTol', 1e-5);
        end

        function shortestPathRecomputesCost(testCase)
            G = graph([1 2 1], [2 3 3], [1 2 5]);
            result = cumcm.shortestPathReport(G, 1, 3);
            testCase.verifyEqual(result.values.path, [1 2 3]);
            testCase.verifyEqual(result.values.cost, 3);
        end

        function classificationKeepsDeclaredGroups(testCase)
            X = [0;.1;1;1.1;2;2.1;3;3.1];
            y = [0;0;1;1;0;0;1;1];
            groups = repelem((0:3)', 2);
            result = cumcm.evaluateModels(X, y, groups, ...
                "nearest-centroid");
            testCase.verifyTrue(result.diagnostics.groupDisjoint);
            testCase.verifyEqual(result.values.accuracy, 0.5, ...
                'AbsTol', 1e-12);
        end

        function sensitivityRecoversLinearDerivatives(testCase)
            result = cumcm.sensitivityReport(@(p)2*p.x-3*p.y, ...
                struct('x',1,'y',2), struct('relativeStep',1e-5));
            testCase.verifyEqual(result.values.derivatives.x, 2, ...
                'AbsTol', 1e-8);
            testCase.verifyEqual(result.values.derivatives.y, -3, ...
                'AbsTol', 1e-8);
            testCase.verifyEqual(result.diagnostics.scheme, 'central');
        end

        function figureExportCreatesRasterArtifact(testCase)
            path = [tempname '.png'];
            fig = figure('Visible', 'off');
            testCase.addTeardown(@() close(fig));
            testCase.addTeardown(@() deleteIfExists(path));
            ax = axes('Parent', fig);
            plot(ax, [0 1], [0 1]);
            result = cumcm.saveFigure(fig, path, ...
                struct('fixture', 'plot-line-v1'));
            testCase.verifyTrue(isfile(path));
            testCase.verifyEqual(result.values.dpi, 300);
            testCase.verifyTrue(result.diagnostics.exists);
        end
    end
end

function deleteIfExists(path)
if isfile(path)
    delete(path);
end
end
