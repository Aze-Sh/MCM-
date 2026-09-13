"""Compile the manuscript with XeLaTeX; no simulator or network is used."""

from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', default='xelatex')
    parser.add_argument('--format', help='Optional prebuilt XeLaTeX format for xetex')
    args = parser.parse_args()
    paper = Path(__file__).resolve().parent
    build = paper / '.build'
    build.mkdir(exist_ok=True)
    engine = shutil.which(args.engine)
    if engine is None:
        raise SystemExit('Install TeX Live or MiKTeX with XeLaTeX, ctex and Fandol fonts.')
    command = [engine]
    if args.format:
        command += [f'-fmt={Path(args.format).resolve()}', '-progname=xelatex']
    command += ['-interaction=nonstopmode', '-halt-on-error', '-output-directory=.build']
    report = {'documents': []}
    for source, destination, expected_pages in [
        ('main', 'main.pdf', 30), ('ai-usage', 'AI工具使用详情.pdf', 2)
    ]:
        for _ in range(2):
            with (build / f'{source}-compile.log').open('w') as output:
                subprocess.run(command + [source + '.tex'], cwd=paper,
                               stdout=output, stderr=subprocess.STDOUT, check=True)
        log = (build / f'{source}.log').read_text(errors='replace')
        defects = re.findall(r'.*(?:Overfull|Missing character|undefined references|undefined on input).*', log)
        if defects:
            raise SystemExit('\n'.join(defects))
        page_count = None
        if shutil.which('pdfinfo'):
            info = subprocess.check_output(['pdfinfo', str(build / f'{source}.pdf')], text=True)
            page_count = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
            if page_count != expected_pages:
                raise SystemExit(f'{source}: expected {expected_pages} pages, got {page_count}')
        target = paper / destination
        shutil.copy2(build / f'{source}.pdf', target)
        report['documents'].append({
            'file': destination, 'pages': page_count, 'expected_pages': expected_pages,
            'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'missing_glyphs': False, 'overfull_boxes': False, 'undefined_references': False,
        })
        print(f'Built {target.name}: {page_count if page_count else "page count not checked"}')
    (paper / 'build-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
