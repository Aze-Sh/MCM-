"""Compile the manuscript and full listings without using a simulator or network."""

from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess

from generate_appendix import generate, source_files
from make_formal_tables import generate as formal_tables


def input_hashes(root):
    paths = set(source_files(root))
    paths.update((root / 'paper').glob('*.tex'))
    paths.update((root / 'paper/figures').glob('*.pdf'))
    paths.update(root / name for name in (
        'paper/results.json', 'paper/figure-data.json',
        'submission_inputs/formal_results.csv', 'submission_inputs/human_review.json'))
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', default='xelatex')
    parser.add_argument('--format', help='Optional prebuilt XeLaTeX format for xetex')
    args = parser.parse_args()
    paper = Path(__file__).resolve().parent
    root = paper.parent
    build = paper / '.build'
    build.mkdir(exist_ok=True)
    (root / 'submission').mkdir(exist_ok=True)
    engine = shutil.which(args.engine)
    if engine is None:
        raise SystemExit('Install TeX Live or MiKTeX with XeLaTeX, ctex, fvextra and Fandol fonts.')
    formal_tables(root)
    records = generate(root)
    command = [engine]
    if args.format:
        command += [f'-fmt={Path(args.format).resolve()}', '-progname=xelatex']
    command += ['-interaction=nonstopmode', '-halt-on-error', '-output-directory=.build']
    report = {'documents': [], 'source_files': len(records),
              'source_lines': sum(r['lines'] for r in records)}
    for source, destination in [('main', 'submission/论文.pdf'), ('ai-usage', 'AI工具使用详情.pdf')]:
        for _ in range(2):
            with (build / f'{source}-compile.log').open('w', encoding='utf-8') as output:
                completed = subprocess.run(command + [source + '.tex'], cwd=paper,
                                           stdout=output, stderr=subprocess.STDOUT)
            if completed.returncode:
                raise SystemExit(f'Compile failed; inspect paper/.build/{source}-compile.log')
        log = (build / f'{source}.log').read_text(encoding='utf-8', errors='replace')
        defects = re.findall(r'.*(?:Overfull|Missing character|undefined references|undefined on input).*', log)
        if defects:
            raise SystemExit('\n'.join(defects))
        pages = int(re.search(r'Output written on .*?\((\d+) pages?', log, re.S).group(1))
        body_pages = None
        if source == 'main':
            aux = (build / 'main.aux').read_text(encoding='utf-8')
            body_pages = int(re.search(r'\\newlabel\{main_end\}\{\{[^}]*\}\{(\d+)\}', aux).group(1))
            if body_pages > 30 or pages <= body_pages:
                raise SystemExit(f'Main text is {body_pages} pages; total is {pages}. Check the page limit and appendix.')
        target = root / destination
        shutil.copy2(build / f'{source}.pdf', target)
        report['documents'].append(dict(
            file=destination, pages=pages, body_and_references_pages=body_pages,
            sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            missing_glyphs=False, overfull_boxes=False, undefined_references=False))
        print(f'Built {target.name}: {pages} pages; main text and references: {body_pages}')
    report['input_sha256'] = input_hashes(root)
    (paper / 'build-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
