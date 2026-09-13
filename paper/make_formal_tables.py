"""Use measured CSV values when present; preserve genuinely empty result cells."""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def escape(value):
    replacements = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
                    '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}',
                    '^': r'\textasciicircum{}'}
    return ''.join(replacements.get(c, c) for c in str(value))


def generate(root=ROOT):
    with (root / 'submission_inputs/formal_results.csv').open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    for problem in (3, 4):
        lines = []
        for index in (1, 2, 3):
            row = next(r for r in rows if r['problem'] == str(problem) and r['test'] == str(index))
            cells = [row[key].strip() for key in ('case_code', 'cleared_count', 'average_time_s', 'real_time_s')]
            lines.append(' & '.join(escape(c) if c else r'\blank' for c in cells) + r'\\[10pt]')
        lines[-1] += r'\bottomrule'
        (root / f'paper/formal_q{problem}.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    generate()
