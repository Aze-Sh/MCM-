"""Publication figures for the CUMCM 2026 problem B evidence package."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon
import numpy as np

import b_geometry as geometry
import b_strategy as strategy
import b_paper_analysis
import q1_q2_analysis


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STYLE_DIR = PROJECT_ROOT / 'figure-styles'
if str(STYLE_DIR) not in sys.path:
    sys.path.insert(0, str(STYLE_DIR))
from python_style import COLORS, export_figure, setup_paper_style  # noqa: E402


PRACTICE_FILES = [
    'official-practice-q3-首次.json',
    'official-practice-q3-v2-second-20260911.json',
    'official-practice-q3-v3-third-20260911.json',
    'official-practice-q4-v2-first-20260911.json',
    'official-practice-q4-v2-second-20260911.json',
    'official-practice-q4-v3-third-20260911.json',
]


def _q1_figure(report):
    q1 = report['q1']
    vertices = np.asarray(q1['vertices_m'], dtype=float)
    minimum_center = np.asarray(q1['minimum_enclosing_center_m'], dtype=float)
    minimum_radius = q1['minimum_enclosing_radius_m']
    diameter_circle_center = (vertices[0] + vertices[1]) / 2.0

    fig, ax = plt.subplots(figsize=(4.5, 3.35))
    ax.add_patch(Polygon(
        vertices, closed=True, facecolor='#DCEAF7', edgecolor=COLORS['blue'],
        linewidth=1.8))
    ax.add_patch(Circle(
        diameter_circle_center, q1['diameter_circle_radius_m'], fill=False,
        edgecolor=COLORS['vermillion'], linestyle='--', linewidth=1.6))
    ax.add_patch(Circle(
        minimum_center, minimum_radius, fill=False,
        edgecolor=COLORS['green'], linewidth=1.7))
    closed = np.vstack((vertices, vertices[0]))
    ax.plot(closed[:, 0], closed[:, 1], color=COLORS['blue'])
    ax.plot(vertices[:2, 0], vertices[:2, 1], color=COLORS['purple'],
            linewidth=2.2)
    ax.scatter(vertices[:, 0], vertices[:, 1], color='#222222', s=20, zorder=5)
    for label, point, offset in zip(
            ('$A$', '$B$', '$C$'), vertices,
            [(-3.5, -3.3), (1.1, -3.3), (1.1, 1.0)]):
        ax.text(point[0] + offset[0], point[1] + offset[1], label)
    ax.annotate(r'$D=40\,\mathrm{m}$', xy=(20, 0), xytext=(20, -8),
                ha='center', arrowprops=dict(arrowstyle='-', color=COLORS['purple']))
    ax.annotate(r'$r_*=23.094\,\mathrm{m}>D/2$',
                xy=minimum_center + [0, minimum_radius], xytext=(47, 30),
                ha='left', color=COLORS['green'],
                arrowprops=dict(arrowstyle='->', color=COLORS['green']))
    ax.text(20, 9, r'$\Omega$', ha='center', color=COLORS['blue'], fontsize=12)
    ax.text(20, 17, r'$r=D/2$', ha='center', color=COLORS['vermillion'])
    ax.set_xlabel('$x$ (m)')
    ax.set_ylabel('$y$ (m)')
    ax.set_aspect('equal')
    ax.set_xlim(-7, 65)
    ax.set_ylim(-12, 48)
    ax.tick_params(which='both', top=True, right=True)
    fig.tight_layout()
    return fig


def _q2_figure(report):
    q2 = report['q2']
    sensor = np.asarray(q2['first_sensor_m'], dtype=float)
    centers = np.asarray(q2['candidate_disc_centers_m'], dtype=float)
    radius = q2['guaranteed_receive_radius_m']
    detectors = np.asarray(q2['recommended_detectors_m'], dtype=float)
    sector = geometry.first_bearing_sector(
        sensor, q2['measured_bearing_deg'],
        q2['bearing_half_error_deg'], q2['maximum_possible_receive_range_m'], 181)

    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    ax.add_patch(Polygon(
        sector, closed=True, facecolor='#FCE9C3', edgecolor=COLORS['orange'],
        linewidth=1.4, alpha=0.9))
    for index, center in enumerate(centers):
        ax.add_patch(Circle(
            center, radius, fill=False, edgecolor=COLORS['gray'],
            linestyle='--', linewidth=1.0))

    x = np.linspace(-250, 1800, 520)
    y = np.linspace(-1050, 1050, 520)
    xx, yy = np.meshgrid(x, y)
    grid = np.stack((xx, yy), axis=-1)
    max_distance = np.max(
        np.linalg.norm(grid[:, :, None, :] - centers[None, None, :, :], axis=-1),
        axis=2)
    ax.contourf(xx, yy, max_distance, levels=[0, radius],
                colors=['#CDEBDD'], alpha=0.9)
    ax.contour(xx, yy, max_distance, levels=[radius],
               colors=[COLORS['green']], linewidths=1.7)
    ax.scatter(*sensor, color='#222222', s=28, zorder=6)
    ax.text(sensor[0] - 80, sensor[1] - 85, '$S_1$')
    ax.scatter(detectors[:, 0], detectors[:, 1], marker='D',
               color=COLORS['blue'], s=32, zorder=6)
    ax.text(detectors[0, 0] + 35, detectors[0, 1] + 25, '$S_2^+$')
    ax.text(detectors[1, 0] + 35, detectors[1, 1] - 75, '$S_2^-$')
    ax.text(810, 0, r'$\mathcal{C}$', color=COLORS['green'], fontsize=12)
    ax.text(1260, 55, r'$\Omega_1$', color=COLORS['orange'], fontsize=11)
    ax.text(-190, 920, '1000 m discs', color=COLORS['gray'], fontsize=8)
    ax.plot([0, 1600], [0, 0], color='#222222', linewidth=0.9, alpha=0.7)
    ax.set_xlabel('$x$ (m)')
    ax.set_ylabel('$y$ (m)')
    ax.set_aspect('equal')
    ax.set_xlim(-250, 1800)
    ax.set_ylim(-1050, 1050)
    ax.tick_params(which='both', top=True, right=True)
    fig.tight_layout()
    return fig


def _load_practice_results():
    output_dir = PROJECT_ROOT / 'output'
    return [json.loads((output_dir / name).read_text(encoding='utf-8'))
            for name in PRACTICE_FILES]


def _practice_figure(results):
    labels = ['Q3-1', 'Q3-2', 'Q3-3', 'Q4-1', 'Q4-2', 'Q4-3']
    cleared = np.array([item['cleared_count'] for item in results])
    sources = np.array([item['source_count'] for item in results])
    fractions = 100.0 * cleared / sources
    components = np.array([[item['time_components_s'][key] for item in results]
                           for key in ('movement', 'measurement',
                                       'channel_switch', 'clearance')])

    fig, axes = plt.subplots(1, 2, figsize=(7.3, 3.2),
                             gridspec_kw={'width_ratios': [0.9, 1.35]})
    ax = axes[0]
    colors = [COLORS['blue']] * 3 + [COLORS['orange']] * 3
    bars = ax.bar(labels, fractions, color=colors, width=0.68)
    for bar, done, total in zip(bars, cleared, sources):
        ax.text(bar.get_x() + bar.get_width() / 2, 101.5,
                f'{done}/{total}', ha='center', va='bottom', color='#222222',
                fontsize=7.2)
    ax.set_ylim(0, 112)
    ax.set_ylabel('Clear fraction (%)')
    ax.axhline(100, color='#222222', linewidth=0.8)
    ax.tick_params(axis='x', rotation=35)

    ax = axes[1]
    bottom = np.zeros(len(labels))
    names = ['Movement', 'Measurement', 'Channel switch', 'Clearance']
    stack_colors = [COLORS['blue'], COLORS['orange'], COLORS['purple'], COLORS['green']]
    for values, name, color in zip(components, names, stack_colors):
        ax.bar(labels, values, bottom=bottom, label=name, color=color, width=0.68)
        bottom += values
    for index, total in enumerate(bottom):
        ax.text(index, total + 180, f'{total / 1000:.2f}k',
                ha='center', va='bottom', fontsize=7.5)
    ax.set_ylim(0, max(bottom) * 1.36)
    ax.set_ylabel('Virtual time (s)')
    ax.tick_params(axis='x', rotation=35)
    ax.legend(loc='upper left', ncol=2, borderaxespad=0.6)
    for axis in axes:
        axis.tick_params(which='both', top=True, right=True)
    fig.tight_layout(w_pad=2.0)
    return fig


def _algorithm_flow_figure():
    fig, ax = plt.subplots(figsize=(7.2, 4.7))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    def box(x, y, width, height, text, color, *, decision=False):
        if decision:
            vertices = np.array([
                [x + width / 2, y + height], [x + width, y + height / 2],
                [x + width / 2, y], [x, y + height / 2],
            ])
            patch = Polygon(vertices, closed=True, facecolor=color,
                            edgecolor='#333333', linewidth=1.1)
        else:
            patch = FancyBboxPatch(
                (x, y), width, height,
                boxstyle='round,pad=0.03,rounding_size=0.08',
                facecolor=color, edgecolor='#333333', linewidth=1.1)
        ax.add_patch(patch)
        ax.text(x + width / 2, y + height / 2, text,
                ha='center', va='center', fontsize=8.3)

    def arrow(x1, y1, x2, y2, label=None, *, bend=0.0):
        patch = FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=9,
            linewidth=1.0, color='#444444',
            connectionstyle=f'arc3,rad={bend}')
        ax.add_patch(patch)
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.14,
                    label, ha='center', va='bottom', fontsize=7.5)

    box(0.5, 6.4, 1.9, 0.8, '最近未完成\n覆盖点', '#DCEAF7')
    box(3.2, 6.4, 2.0, 0.8, '扫描未清除\n频道', '#DCEAF7')
    box(6.2, 6.25, 2.0, 1.1, '正示向？', '#FCE9C3', decision=True)
    box(9.1, 6.4, 2.4, 0.8, '初始化示向扇形\n与源域交集', '#E8DDF3')

    box(9.1, 4.45, 2.4, 0.8, '自适应测量\n并相交可行域', '#E8DDF3')
    box(6.2, 4.3, 2.0, 1.1, '$r_*\\leq19.5$ m？', '#FCE9C3', decision=True)
    box(3.3, 4.45, 1.8, 0.8, '执行清除', '#CDEBDD')
    box(0.5, 4.45, 2.1, 0.8, '有限 20 m 网格\n覆盖剩余区域', '#F9D9D5')

    box(2.9, 2.05, 2.6, 1.1, '已清除 16 个\n或覆盖全完成？', '#FCE9C3', decision=True)
    box(6.3, 2.2, 2.1, 0.8, '退出并保存\n日志与结果', '#CDEBDD')

    arrow(2.4, 6.8, 3.2, 6.8)
    arrow(5.2, 6.8, 6.2, 6.8)
    arrow(8.2, 6.8, 9.1, 6.8, '是')
    arrow(10.3, 6.4, 10.3, 5.25)
    arrow(9.1, 4.85, 8.2, 4.85)
    arrow(6.2, 4.85, 5.1, 4.85, '是')
    arrow(2.6, 4.85, 3.3, 4.85)
    arrow(4.2, 4.45, 4.2, 3.15)
    arrow(5.5, 2.6, 6.3, 2.6, '是')

    # The finite fallback sits on its own lower rail so its label and path do
    # not cross the direct successful-localisation branch.
    ax.plot([7.2, 7.2, 1.55], [4.3, 3.72, 3.72], color='#444444', linewidth=1.0)
    arrow(1.55, 3.72, 1.55, 4.45)
    ax.text(4.4, 3.82, '否：8 次后兜底', ha='center', va='bottom', fontsize=7.5)

    # A negative directional response only advances the channel scan.  Route
    # this branch through the clear gap below the top row, away from the title.
    ax.plot([7.2, 7.2, 4.2], [6.25, 5.82, 5.82], color='#444444', linewidth=1.0)
    arrow(4.2, 5.82, 4.2, 6.4, '否')

    # An unfinished coverage pass returns along the outside of the diagram.
    ax.plot([4.2, 4.2, 0.18, 0.18], [2.05, 1.15, 1.15, 6.8],
            color='#444444', linewidth=1.0)
    arrow(0.18, 6.8, 0.5, 6.8, '否')

    ax.text(6.0, 7.75, '覆盖搜索、定位与清除的有限流程',
            ha='center', va='top', fontsize=10, fontweight='bold')
    ax.text(6.0, 0.35,
            '只用正示向缩小可行域；无信号不用于排除定向源位置',
            ha='center', va='center', fontsize=8, color=COLORS['gray'])
    return fig


def _coverage_directional_figure():
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.45),
                             gridspec_kw={'width_ratios': [1.05, 0.95]})

    ax = axes[0]
    points = np.asarray(strategy.coverage_points(600.0))
    ax.add_patch(Circle((0, 0), 1800, facecolor='#F7F7F7',
                        edgecolor='#333333', linewidth=1.2))
    ax.scatter(points[:, 0], points[:, 1], s=11, facecolor='white',
               edgecolor=COLORS['blue'], linewidth=0.7, zorder=3)
    source = np.array([180.0, 240.0])
    ax.scatter(*source, marker='*', s=85, color=COLORS['vermillion'], zorder=5)
    ax.add_patch(Circle(source, 1000, fill=False, edgecolor=COLORS['green'],
                        linestyle='--', linewidth=1.1))
    cell = np.array([[0, 0], [600, 0], [600, 600], [0, 600]])
    ax.add_patch(Polygon(cell, closed=True, fill=False, edgecolor=COLORS['orange'],
                         linewidth=2.0, zorder=4))
    ax.text(source[0] + 75, source[1] + 55, '$G$', color=COLORS['vermillion'])
    ax.text(-1750, 1560, '61 coverage points', fontsize=8, color=COLORS['blue'])
    ax.text(-1750, 1370, '$R=1800$ m', fontsize=8)
    ax.set_xlabel('$x$ (m)')
    ax.set_ylabel('$y$ (m)')
    ax.set_aspect('equal')
    ax.set_xlim(-2050, 2050)
    ax.set_ylim(-2050, 2050)
    ax.tick_params(which='both', top=True, right=True)

    ax = axes[1]
    square = np.array([[0, 0], [600, 0], [600, 600], [0, 600]])
    g = np.array([230.0, 270.0])
    direction = np.array([0.82, 0.57])
    normal = np.array([-direction[1], direction[0]])
    span = 1200.0
    boundary_a = g - span * normal
    boundary_b = g + span * normal
    half_plane = np.array([
        boundary_a, boundary_b,
        boundary_b + span * direction,
        boundary_a + span * direction,
    ])
    ax.add_patch(Polygon(half_plane, closed=True, facecolor='#CDEBDD',
                         edgecolor='none', alpha=0.8))
    ax.add_patch(Polygon(square, closed=True, fill=False, edgecolor='#222222',
                         linewidth=1.8))
    in_half_plane = ((square - g) @ direction) >= -1e-9
    for vertex in square:
        ax.plot([g[0], vertex[0]], [g[1], vertex[1]], color='#AAAAAA',
                linestyle='--', linewidth=0.8)
    ax.scatter(square[~in_half_plane, 0], square[~in_half_plane, 1], s=28,
               facecolor='white', edgecolor='#333333', zorder=4)
    ax.scatter(square[in_half_plane, 0], square[in_half_plane, 1], s=34,
               facecolor=COLORS['green'], edgecolor='#222222', zorder=5)
    witness = square[in_half_plane][np.argmin(
        np.linalg.norm(square[in_half_plane] - g, axis=1))]
    ax.plot([g[0], witness[0]], [g[1], witness[1]], color=COLORS['vermillion'],
            linewidth=2.0, zorder=4)
    ax.scatter(*g, marker='*', s=90, color=COLORS['vermillion'], zorder=6)
    ax.add_patch(FancyArrowPatch(
        g, g + 250 * direction, arrowstyle='-|>', mutation_scale=10,
        color=COLORS['green'], linewidth=1.4))
    ax.plot([boundary_a[0], boundary_b[0]], [boundary_a[1], boundary_b[1]],
            color=COLORS['green'], linewidth=1.2)
    ax.text(g[0] - 42, g[1] - 55, '$G$')
    ax.text(430, 430, 'radiating half-plane', fontsize=8, color=COLORS['green'])
    ax.text(25, 635, r'$h=600$ m,  $d_{max}=600\sqrt{2}=848.53$ m', fontsize=8)
    ax.set_aspect('equal')
    ax.set_xlim(-90, 760)
    ax.set_ylim(-70, 760)
    ax.axis('off')

    fig.tight_layout(w_pad=1.0)
    return fig


def _parameter_sensitivity_figure(evidence):
    error_rows = evidence['q2_sensitivity']['error_sweep_at_1500_m']
    range_rows = evidence['q2_sensitivity']['range_sweep_at_1_deg']
    operating = evidence['q2_sensitivity']['operating_point']
    errors = np.array([row['error_deg'] for row in error_rows])
    error_baselines = np.array([row['transverse_baseline_m'] for row in error_rows])
    error_angles = np.array([row['minimum_crossing_angle_deg'] for row in error_rows])
    ranges = np.array([row['max_range_m'] for row in range_rows]) / 1000.0
    range_baselines = np.array([row['transverse_baseline_m'] for row in range_rows])
    range_angles = np.array([row['minimum_crossing_angle_deg'] for row in range_rows])

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.4), sharex='col')
    panels = (
        (axes[0, 0], errors, error_baselines, 'Transverse baseline (m)'),
        (axes[1, 0], errors, error_angles, 'Worst crossing angle (deg)'),
        (axes[0, 1], ranges, range_baselines, 'Transverse baseline (m)'),
        (axes[1, 1], ranges, range_angles, 'Worst crossing angle (deg)'),
    )
    for ax, x_values, y_values, ylabel in panels:
        ax.plot(x_values, y_values, marker='o', markersize=3.2,
                linewidth=1.25, color=COLORS['blue'])
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.22, linewidth=0.5)
        ax.tick_params(which='both', top=True, right=True)
    axes[1, 0].set_xlabel(r'Bearing half-error $\varepsilon$ (deg)')
    axes[1, 1].set_xlabel(r'Range ratio $R/r_0$')
    axes[0, 0].axvline(operating['error_deg'], color=COLORS['vermillion'],
                       linestyle='--', linewidth=0.9)
    axes[1, 0].axvline(operating['error_deg'], color=COLORS['vermillion'],
                       linestyle='--', linewidth=0.9)
    axes[0, 1].axvline(operating['max_range_m'] / 1000.0,
                       color=COLORS['vermillion'], linestyle='--', linewidth=0.9)
    axes[1, 1].axvline(operating['max_range_m'] / 1000.0,
                       color=COLORS['vermillion'], linestyle='--', linewidth=0.9)
    axes[0, 0].text(operating['error_deg'] + 0.08, max(error_baselines) - 12,
                    'operating point', color=COLORS['vermillion'], fontsize=7)
    axes[0, 1].text(operating['max_range_m'] / 1000.0 + 0.025,
                    max(range_baselines) - 45, 'operating point',
                    color=COLORS['vermillion'], fontsize=7)
    fig.tight_layout(w_pad=1.4, h_pad=0.8)
    return fig


def _strategy_ablation_figure(evidence):
    ablation = evidence['strategy_ablation']
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.25))
    problems = ['Q3', 'Q4']
    versions = ['v1', 'v2', 'v3']
    x = np.arange(len(problems))
    width = 0.22
    for index, (version, color) in enumerate(zip(
            versions, (COLORS['gray'], COLORS['blue'], COLORS['green']))):
        values = [ablation[key]['versions'][version]['mean_virtual_time_s'] / 1000
                  for key in ('q3', 'q4')]
        axes[0].bar(x + (index - 1) * width, values, width,
                    label=version, color=color)
    axes[0].set_xticks(x, problems)
    axes[0].set_ylabel('Mean virtual time (ks)')
    axes[0].set_title('All 50 paired cases per problem')
    axes[0].legend(ncol=3, loc='upper center')
    for index, key in enumerate(('q3', 'q4')):
        reduction = ablation[key]['v1_to_v2_virtual_time_reduction_percent']
        v1_time = ablation[key]['versions']['v1']['mean_virtual_time_s'] / 1000
        v2_time = ablation[key]['versions']['v2']['mean_virtual_time_s'] / 1000
        axes[0].text(index, (v1_time + v2_time) / 2,
                     f'v1→v2  −{reduction:.2f}%',
                     ha='center', va='center', fontsize=7.2,
                     color=COLORS['blue'],
                     bbox={'facecolor': 'white', 'edgecolor': 'none',
                           'alpha': 0.82, 'pad': 1.5})

    x = np.arange(len(problems))
    for index, (version, color) in enumerate((
            ('v2', COLORS['blue']), ('v3', COLORS['green']))):
        values = [ablation[key][f'source16_{version}_mean_virtual_time_s'] / 1000
                  for key in ('q3', 'q4')]
        axes[1].bar(x + (index - 0.5) * 0.3, values, 0.3,
                    label=version, color=color)
    axes[1].set_xticks(x, problems)
    axes[1].set_ylabel('Mean virtual time (ks)')
    axes[1].set_title('Four 16-source paired cases')
    axes[1].legend(ncol=2, loc='upper center')
    for index, key in enumerate(('q3', 'q4')):
        reduction = ablation[key]['source16_v2_to_v3_reduction_percent']
        top = ablation[key]['source16_v2_mean_virtual_time_s'] / 1000
        axes[1].text(index, top + 0.35, f'v2→v3  −{reduction:.2f}%',
                     ha='center', va='bottom', fontsize=7.2,
                     color=COLORS['green'],
                     bbox={'facecolor': 'white', 'edgecolor': 'none',
                           'alpha': 0.82, 'pad': 1.5})
    for ax in axes:
        ax.set_ylim(0, 20)
        ax.grid(axis='y', alpha=0.22, linewidth=0.5)
        ax.tick_params(which='both', top=True, right=True)
    fig.text(0.5, 0.005, 'Every displayed group retained a 100% clear fraction.',
             ha='center', fontsize=7.2, color=COLORS['gray'])
    fig.tight_layout(w_pad=1.8, rect=(0, 0.04, 1, 1))
    return fig


def _directional_stress_figure(evidence):
    stress = evidence['q4_directional_stress']
    rows = stress['runs']
    fractions = np.array([row['directional_fraction'] for row in rows])
    times = np.array([row['virtual_time_s'] for row in rows]) / 1000.0
    source_counts = np.array([row['source_count'] for row in rows])
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2),
                             gridspec_kw={'width_ratios': [1.35, 0.85]})
    scatter = axes[0].scatter(
        100 * fractions, times, c=source_counts, cmap='viridis',
        s=28, edgecolor='white', linewidth=0.35)
    axes[0].axvline(50, color='#999999', linestyle='--', linewidth=0.8)
    axes[0].axvline(70, color='#999999', linestyle='--', linewidth=0.8)
    axes[0].set_xlabel('Directional-source fraction (%)')
    axes[0].set_ylabel('Virtual time (ks)')
    axes[0].grid(alpha=0.22, linewidth=0.5)
    cbar = fig.colorbar(scatter, ax=axes[0], pad=0.02)
    cbar.set_label('Source count')

    bins = stress['bins']
    labels = ['<50%', '50–70%', '≥70%']
    means = [item['mean_virtual_time_s'] / 1000 for item in bins]
    bars = axes[1].bar(labels, means,
                       color=(COLORS['blue'], COLORS['orange'], COLORS['green']))
    axes[1].set_ylabel('Mean virtual time (ks)')
    axes[1].set_ylim(0, max(means) * 1.25)
    axes[1].grid(axis='y', alpha=0.22, linewidth=0.5)
    for bar, item in zip(bars, bins):
        axes[1].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 0.25,
                     f"n={item['count']}\nall clear",
                     ha='center', va='bottom', fontsize=7.2)
    axes[1].set_title('Directional-ratio strata')
    for ax in axes:
        ax.tick_params(which='both', top=True, right=True)
    fig.tight_layout(w_pad=1.5)
    return fig


def build_all(output_dir=None):
    setup_paper_style()
    output_dir = Path(output_dir) if output_dir else PROJECT_ROOT / 'figures' / 'final'
    report_path = PROJECT_ROOT / 'output' / 'q1-q2-geometry-20260911.json'
    report = (json.loads(report_path.read_text(encoding='utf-8'))
              if report_path.exists() else q1_q2_analysis.build_report())
    evidence_path = PROJECT_ROOT / 'output' / 'paper-evidence-20260912.json'
    evidence = (json.loads(evidence_path.read_text(encoding='utf-8'))
                if evidence_path.exists() else b_paper_analysis.build_report())
    figures = {
        'q1-region-counterexample': _q1_figure(report),
        'q2-second-detector-region': _q2_figure(report),
        'q34-algorithm-flow': _algorithm_flow_figure(),
        'q34-coverage-directional-proof': _coverage_directional_figure(),
        'q34-practice-summary': _practice_figure(_load_practice_results()),
        'q2-parameter-sensitivity': _parameter_sensitivity_figure(evidence),
        'q34-strategy-ablation': _strategy_ablation_figure(evidence),
        'q4-directional-stress': _directional_stress_figure(evidence),
    }
    outputs = {}
    for name, figure in figures.items():
        outputs[name] = export_figure(figure, output_dir / name, include_svg=True)
        plt.close(figure)
    return outputs


def main():
    outputs = build_all()
    for paths in outputs.values():
        for path in paths:
            print(path)


if __name__ == '__main__':
    main()
