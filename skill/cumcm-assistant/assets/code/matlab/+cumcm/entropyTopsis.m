function result = entropyTopsis(X, benefit, weights)
%ENTROPYTOPSIS Entropy-weight TOPSIS with explicit orientation.
arguments
    X (:,:) double
    benefit (1,:) logical
    weights double = []
end
[n,p] = size(X);
if n < 2 || numel(benefit) ~= p || any(~isfinite(X),'all')
    error('cumcm:InvalidData', 'Invalid decision matrix or direction vector.');
end
spans = max(X,[],1)-min(X,[],1);
if any(spans == 0)
    error('cumcm:ConstantCriterion', 'Constant criterion is not informative.');
end
Z = (X-min(X,[],1))./spans;
Z(:,~benefit) = 1-Z(:,~benefit);
if isempty(weights)
    sums = sum(Z,1);
    P = zeros(size(Z));
    for j = 1:p
        if sums(j)>0, P(:,j)=Z(:,j)/sums(j); else, P(:,j)=1/n; end
    end
    terms = zeros(size(P));
    mask = P>0;
    terms(mask)=P(mask).*log(P(mask));
    entropy = -sum(terms,1)/log(n);
    divergence = 1-entropy;
    if sum(divergence) < eps, weights=ones(1,p)/p; else, weights=divergence/sum(divergence); end
else
    weights = weights(:)';
    if numel(weights)~=p || any(weights<0) || sum(weights)<=0
        error('cumcm:InvalidWeights','Invalid weights.');
    end
    weights=weights/sum(weights);
end
V=Z.*weights;
dPos=sqrt(sum((V-max(V,[],1)).^2,2));
dNeg=sqrt(sum((V-min(V,[],1)).^2,2));
score=dNeg./(dPos+dNeg);
[~,ranking]=sort(score,'descend');
values=struct('weights',weights,'scores',score,'ranking',ranking');
result=struct('method','ahp-entropy-topsis','values',values, ...
    'diagnostics',struct('criterionCount',p),'assumptions',{{'Criteria are compensatory.'}});
end

