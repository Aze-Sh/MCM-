function colors = matlabStyle(fig)
%MATLABSTYLE Apply a Chinese-capable, colorblind-safe paper style.
if nargin < 1
    fig = gcf;
end
set(fig, 'Color', 'w', 'Units', 'centimeters', 'Position', [2 2 16 10.5]);
fonts = listfonts;
preferred = {'Microsoft YaHei', 'Noto Sans CJK SC', 'SimHei', 'Arial'};
fontName = 'Arial';
for k = 1:numel(preferred)
    if any(strcmpi(fonts, preferred{k}))
        fontName = preferred{k};
        break;
    end
end
set(findall(fig, '-property', 'FontName'), 'FontName', fontName);
set(findall(fig, 'Type', 'axes'), 'FontSize', 9, 'LineWidth', 0.9, ...
    'TickDir', 'in', 'Box', 'on');
colors = [0.0000 0.4470 0.6980; 0.9020 0.6240 0.0000; ...
          0.0000 0.6200 0.4510; 0.8350 0.3690 0.0000; ...
          0.4940 0.1840 0.5560];
colororder(colors);
end

function paths = exportPaperFigure(fig, outputStem)
%EXPORTPAPERFIGURE Export vector PDF/SVG and a 400-DPI PNG fallback.
matlabStyle(fig);
paths = {outputStem + ".pdf", outputStem + ".svg", outputStem + ".png"};
exportgraphics(fig, paths{1}, 'ContentType', 'vector');
exportgraphics(fig, paths{2}, 'ContentType', 'vector');
exportgraphics(fig, paths{3}, 'Resolution', 400);
end
