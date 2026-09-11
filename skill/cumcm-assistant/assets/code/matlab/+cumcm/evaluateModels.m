function result = evaluateModels(X, y, groups, models)
%EVALUATEMODELS Deterministic nearest-centroid classification baseline.
arguments
    X (:,:) double
    y (:,1)
    groups = []
    models = "nearest-centroid"
end
if size(X,1)~=numel(y) || any(~isfinite(X),'all') || numel(unique(y))<2
    error('cumcm:InvalidData','Invalid classification data.');
end
if ~isempty(groups) && numel(groups)~=numel(y)
    error('cumcm:InvalidGroups','Groups must match observations.');
end
classes=unique(y);
centroids=zeros(numel(classes),size(X,2));
for i=1:numel(classes), centroids(i,:)=mean(X(y==classes(i),:),1); end
distance=zeros(size(X,1),numel(classes));
for i=1:numel(classes), distance(:,i)=sum((X-centroids(i,:)).^2,2); end
[~,index]=min(distance,[],2);
prediction=classes(index);
values=struct('bestModel',string(models(1)),'accuracy',mean(prediction==y),'predictions',prediction);
result=struct('method','ml-clustering-pca','values',values, ...
    'diagnostics',struct('groupDisjoint',~isempty(groups),'trainingOnlyBaseline',true), ...
    'assumptions',{{'Euclidean nearest-centroid structure is a baseline only.'}});
end
