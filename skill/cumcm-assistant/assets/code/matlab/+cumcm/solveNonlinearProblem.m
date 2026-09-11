function result = solveNonlinearProblem(problem)
%SOLVENONLINEARPROBLEM Minimal local nonlinear optimization wrapper.
arguments
    problem struct
end
if ~isfield(problem,'objective') || ~isfield(problem,'x0')
    error('cumcm:InvalidModel','Problem needs objective and x0.');
end
if exist('fmincon','file')==2
    fields={'A','b','Aeq','beq','lb','ub','nonlcon'};
    args=cell(1,numel(fields));
    for i=1:numel(fields), if isfield(problem,fields{i}), args{i}=problem.(fields{i}); else, args{i}=[]; end, end
    options=optimoptions('fmincon','Display','none');
    [x,fval,exitflag,output]=fmincon(problem.objective,problem.x0,args{:},options);
else
    if any(isfield(problem,{'A','b','Aeq','beq','lb','ub','nonlcon'}))
        error('cumcm:MissingToolbox','Optimization Toolbox is required for constrained nonlinear problems.');
    end
    [x,fval,exitflag,output]=fminsearch(problem.objective,problem.x0,optimset('Display','off'));
end
success=exitflag>0;
if ~success, x=[]; fval=[]; end
values=struct('solution',x,'objective',fval);
result=struct('method','nonlinear-multiobjective','values',values, ...
    'diagnostics',struct('success',success,'message',output.message,'localOptimumOnly',true), ...
    'assumptions',{{'The solution is local unless separately proven global.'}});
end
