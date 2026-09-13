"""Build the submission from an explicit file list; never connect to a simulator."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'paper'))
from generate_appendix import manifest
from build import input_hashes

LIMIT = 20 * 1024 * 1024
REVIEW_KEYS = ('model_and_proofs_reviewed', 'code_reviewed', 'data_and_figures_reviewed',
               'references_reviewed', 'ai_disclosure_completed', 'final_paper_checked')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def formal_metadata(path):
    # Read the public envelope only. The encrypted and signed file is never edited.
    with path.open('rb') as f:
        prefix = f.read(262144)
    if not prefix.startswith(b'JMBPLOG1'):
        raise ValueError('不是可识别的模拟器日志')
    start = prefix.find(b'{', 8, 64)
    if start < 0:
        raise ValueError('日志缺少公共元数据')
    return json.JSONDecoder().raw_decode(prefix[start:].decode('utf-8', errors='replace'))[0]


def check_inputs(root=ROOT):
    pending, errors, logs = [], [], []
    with (root / 'submission_inputs/formal_results.csv').open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    slots = {(str(q), str(i)) for q in (3, 4) for i in (1, 2, 3)}
    if len(rows) != 6 or {(r.get('problem'), r.get('test')) for r in rows} != slots:
        return ['正式结果必须包含Q3、Q4各三行'], ['正式结果行号不完整或重复'], []
    codes = set()
    for row in rows:
        label = f"Q{row['problem']} 第{row['test']}次"
        directory = root / f"submission_inputs/formal/q{row['problem']}/test_{row['test']}"
        found = sorted(directory.glob('*.jlog'))
        if not found:
            pending.append(f'{label}：缺少原始正式日志')
        elif len(found) != 1:
            errors.append(f'{label}：每个目录只能放同一次测试的一份日志')
        else:
            log = found[0]
            if log.is_symlink():
                errors.append(f'{label}：不接受符号链接')
                continue
            try:
                meta = formal_metadata(log)
                if meta.get('package_type') != 'formal_behavior_log':
                    raise ValueError('必须是正式日志，演练日志不能代替')
                if int(meta.get('problem_no', -1)) != int(row['problem']):
                    raise ValueError('日志题号与目录不一致')
                if int(meta.get('formal_index', -1)) != int(row['test']):
                    raise ValueError('日志正式次数与目录不一致')
                if str(meta.get('case_code', '')) != row['case_code'].strip():
                    raise ValueError('日志案例编码与表格不一致')
                if row['log_filename'].strip() != log.name:
                    raise ValueError('表格中的原始文件名与日志不一致')
                logs.append(log)
            except (ValueError, TypeError, KeyError) as exc:
                errors.append(f'{label}：{exc}')
        for key in ('case_code', 'cleared_count', 'virtual_time_s', 'real_time_s', 'log_filename'):
            if not row.get(key, '').strip():
                pending.append(f'{label}：{key} 待填')
        code = row['case_code'].strip()
        if code:
            if code in codes:
                errors.append(f'{label}：案例编码重复')
            codes.add(code)
        try:
            numbers = {k: float(row[k]) for k in ('cleared_count', 'virtual_time_s', 'average_time_s', 'real_time_s') if row.get(k, '').strip()}
            if any(not math.isfinite(v) or v < 0 for v in numbers.values()):
                raise ValueError('数值必须为有限非负数')
            count = numbers.get('cleared_count')
            if count is not None and (not count.is_integer() or count > 16):
                raise ValueError('实际清除数必须为0至16的整数')
            if count and 'virtual_time_s' in numbers:
                if 'average_time_s' not in numbers:
                    pending.append(f'{label}：平均时间待填（总虚拟时间/实际清除数）')
                elif abs(numbers['average_time_s'] - numbers['virtual_time_s'] / count) > 0.02:
                    raise ValueError('平均时间与总时间/清除数不一致')
            if count == 0 and row['average_time_s'].strip():
                raise ValueError('清除数为0时平均时间应留空')
        except ValueError as exc:
            errors.append(f'{label}：{exc}')
        if row.get('upload_confirmed', '').strip().lower() not in ('true', 'yes', '1'):
            pending.append(f'{label}：尚未确认模拟器日志上传成功')
    review = json.loads((root / 'submission_inputs/human_review.json').read_text(encoding='utf-8'))
    for key in REVIEW_KEYS:
        if review.get(key) is not True:
            pending.append(f'人工核验待完成：{key}')
    ai_source = root / 'paper/ai-usage.tex'
    if ai_source.exists() and any(r'\blank' in line and r'\newcommand' not in line
                                  for line in ai_source.read_text(encoding='utf-8').splitlines()):
        pending.append('AI使用详情仍有待填项：请据实补充工具信息和人工核验记录后重新编译')
    for key, description in (
        ('q2_comparison', '问题二的实测对照'), ('sensitivity', '参数敏感性实验'),
        ('ablation', '同输入消融实验'), ('practice_details', '演练清除数和现实时间核对')):
        if not any(p.is_file() and p.name not in ('.gitkeep', 'README.md') for p in (root / 'submission_inputs' / key).rglob('*')):
            pending.append(f'{description}：当前论文有空栏，需补测填写或据实改为未开展的后续工作')
    return pending, errors, logs


def support_files(root=ROOT):
    names = ['README.md', 'run_robot.py', 'solve_questions.py', 'start_robot.ps1',
             'check.py', 'prepare_submission.py', 'AI工具使用详情.pdf']
    paths = [root / name for name in names]
    for directory in ('src', 'tools', 'tests', 'docs', 'validation', 'paper', 'submission_inputs'):
        for p in sorted((root / directory).rglob('*')):
            if not p.is_file() or any(part.startswith('.') or part == '__pycache__' for part in p.relative_to(root).parts):
                continue
            if p.suffix not in ('.py', '.ps1', '.md', '.json', '.jsonl', '.csv', '.tex', '.pdf'):
                continue
            paths.append(p)
    return paths


def check_anonymity(files):
    # Pattern checks assist review; they cannot infer every name or school affiliation.
    patterns = [r'(?<![A-Za-z0-9.])\d{12}(?![A-Za-z0-9.])', '/' + r'home/[^/\s]+/',
                r'[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
                r'https?://github\.com/[^\s/]+/']
    flagged = []
    for path in files:
        if path.suffix in ('.pdf', '.jlog'):
            continue
        value = path.read_text(encoding='utf-8-sig')
        if any(re.search(pattern, value) for pattern in patterns):
            flagged.append(path.name)
    return sorted(set(flagged))


def write_zip(destination, entries):
    # Fixed timestamps make identical inputs produce identical ZIP bytes and MD5.
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def prepare(root=ROOT, check_only=False):
    pending, errors, logs = check_inputs(root)
    files = support_files(root)
    if any(p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) for p in files):
        errors.append('支撑材料不接受外部路径或符号链接')
    flagged = check_anonymity(files)
    if flagged:
        errors.append('匿名检查发现待人工核对文件：' + '、'.join(flagged))
    try:
        report = json.loads((root / 'paper/build-report.json').read_text(encoding='utf-8'))
        if report.get('input_sha256') != input_hashes(root):
            errors.append('论文输入已变更，请先运行 python paper/build.py')
        if json.loads((root / 'paper/source_manifest.json').read_text(encoding='utf-8')) != manifest(root):
            errors.append('完整程序附录已过期，请重新编译论文')
        for record in report['documents']:
            path = root / record['file']
            if sha(path.read_bytes()) != record['sha256']:
                errors.append(f"PDF与构建记录不一致：{record['file']}")
            if path.stat().st_size > LIMIT:
                errors.append(f"PDF超过20MB：{record['file']}")
    except (OSError, KeyError, ValueError):
        errors.append('缺少有效论文或构建记录，请先编译论文')
    status = dict(ready=not pending and not errors, pending=pending, errors=errors,
                  formal_logs=len(logs), official_simulator_used=False,
                  anonymity='Custom text checked; original signed official logs are preserved verbatim and may contain system identity fields.')
    if check_only:
        return status
    output = root / 'submission'
    output.mkdir(exist_ok=True)
    if not errors:
        entries = {p.relative_to(root).as_posix(): p.read_bytes() for p in files}
        # The official AI disclosure is at the archive root.
        for p in logs:
            entries[p.relative_to(root).as_posix()] = p.read_bytes()
        for p in (root / 'submission_inputs').rglob('.gitkeep'):
            entries[p.relative_to(root).as_posix()] = b''
        entries['FILE_MANIFEST.json'] = (json.dumps(
            {name: dict(bytes=len(data), sha256=sha(data)) for name, data in sorted(entries.items())},
            ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        write_zip(output / '支撑材料.zip', entries)
        if (output / '支撑材料.zip').stat().st_size > LIMIT:
            status['errors'].append('支撑材料ZIP超过20MB，不能按当前文件提交')
            status['ready'] = False
    lines = ['# 提交检查', '', '**' + ('文件检查通过，提交前仍须人工核对。' if status['ready'] else '尚有待补项目，当前为待完成材料。') + '**', '',
             '## 缺项', '']
    lines += [f'- [ ] {item}' for item in pending] or ['无。']
    lines += ['', '## 文件检查错误', ''] + ([f'- {item}' for item in status['errors']] or ['无。'])
    lines += ['', '正式日志必须使用模拟器导出的原始文件名和原始字节；不要修改其中系统写入的身份字段。',
              '源码、论文和普通结果采用匿名材料；原始日志按题目要求作为指定系统产物提交。',
              '生成MD5之前先备份最终PDF和ZIP；生成后不要改动文件，任何改动均需重新生成并提交MD5。', '']
    (output / '待补清单.md').write_text('\n'.join(lines), encoding='utf-8')
    (output / 'status.json').write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='只检查；缺项或错误时退出码为2')
    args = parser.parse_args()
    try:
        result = prepare(check_only=args.check)
    except (OSError, ValueError, KeyError) as exc:
        print(f'材料检查失败：{exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result['errors'] or (args.check and not result['ready']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
