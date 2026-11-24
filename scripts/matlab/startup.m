% Run from the repo root to put project MATLAB code on the path.
root = fileparts(mfilename('fullpath'));
addpath(root, fullfile(root, 'scripts'), fullfile(root, 'models'));
fprintf('ES327 MATLAB paths added from %s\n', root);
