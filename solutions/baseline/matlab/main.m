% Contest entry point: run from the project root or use this file's location.
scriptDir = fileparts(mfilename('fullpath'));
projectRoot = fileparts(scriptDir);
dataDir = fullfile(projectRoot, 'data', 'raw');
outputDir = fullfile(projectRoot, 'output');
if ~isfolder(outputDir), mkdir(outputDir); end
fprintf('Read audited inputs from %s\n', dataDir);

