"""Publication figures for the CUMCM 2026 problem B evidence package."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
import numpy as np

import b_geometry as geometry
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


def build_all(output_dir=None):
    setup_paper_style()
    output_dir = Path(output_dir) if output_dir else PROJECT_ROOT / 'figures' / 'final'
    report_path = PROJECT_ROOT / 'output' / 'q1-q2-geometry-20260911.json'
    report = (json.loads(report_path.read_text(encoding='utf-8'))
              if report_path.exists() else q1_q2_analysis.build_report())
    figures = {
        'q1-region-counterexample': _q1_figure(report),
        'q2-second-detector-region': _q2_figure(report),
        'q34-practice-summary': _practice_figure(_load_practice_results()),
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
