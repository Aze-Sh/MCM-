function result = saveFigure(fig, path, metadata)
%SAVEFIGURE Export a vector figure or 300-DPI raster.
arguments
    fig matlab.ui.Figure
    path {mustBeTextScalar}
    metadata struct = struct()
end
[folder,~,extension]=fileparts(path);
if strlength(folder)>0 && ~isfolder(folder), mkdir(folder); end
extension=lower(extension);
if any(strcmp(extension,{'.pdf','.svg'}))
    exportgraphics(fig,path,'ContentType','vector');
    dpi=300;
elseif any(strcmp(extension,{'.png','.jpg','.jpeg','.tif','.tiff'}))
    exportgraphics(fig,path,'Resolution',300);
    dpi=300;
else
    error('cumcm:InvalidFormat','Unsupported figure format.');
end
values=struct('path',char(path),'dpi',dpi,'metadata',metadata);
result=struct('method','scientific-plotting','values',values, ...
    'diagnostics',struct('exists',isfile(path),'format',extension), ...
    'assumptions',{{'Figure labels and data were prepared by the caller.'}});
end

