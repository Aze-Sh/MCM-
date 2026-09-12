"""Read actual local runs into version-labelled paper tables; never connect."""
import argparse
import json
from pathlib import Path

V6="residual-committed-policy-v6"
V7="obligation-service-interception-v7"


def read_run(folder):
    folder=Path(folder)
    summary=json.loads((folder/'summary.json').read_text(encoding='utf-8-sig'))
    official_file=folder/'official_observation.json'
    official=json.loads(official_file.read_text(encoding='utf-8-sig')) if official_file.exists() else {}
    last_clear=None;intents={};seen=set()
    for line in (folder/'actions.jsonl').read_text(encoding='utf-8-sig').splitlines():
        event=json.loads(line)
        if event.get('event')=='intent':
            intents[event['payload']['request_id']]=event['path']
        if event.get('event')!='response':
            continue
        rid=event['request_id'];reply=event['response']
        if rid in seen or not reply.get('accepted'):
            continue
        seen.add(rid)
        if intents.get(rid)=='/clear' and reply.get('clear_result')=='success':
            last_clear=reply['virtual_time_s']
    total=official.get('source_total_from_simulator')
    cleared=summary['cleared_count'];time_s=summary['virtual_time_s']
    episodes=[e for e in summary.get('route_episodes',[]) if e['status']=='arrived']
    return dict(folder=str(folder),strategy=summary['strategy'],problem=summary['problem'],
        run_kind=summary['run_kind'],case_code=summary['case_code'],cleared_count=cleared,
        official_source_total=total,clear_fraction=cleared/total if total else None,
        virtual_time_s=time_s,average_clear_time_s=time_s/cleared if cleared else None,
        travel_m=summary['travel_m'],movement_time_s=summary['travel_m']/5,
        tail_exclusion_time_s=None if last_clear is None else time_s-last_clear,
        official_program_runtime_s=official.get('official_program_runtime_s'),
        official_log_filename=official.get('official_log_filename'),
        local_elapsed_s=summary.get('local_elapsed_s'),
        completion_certificate=summary.get('completion_certificate'),
        exit_confirmed=summary.get('exit_confirmed'),error=summary.get('error'),
        completed_episode_count=len(episodes),
        minimum_episode_upper_slack_s=min((e['upper_minus_actual_s'] for e in episodes),default=None),
        adopted_tail_edits=sum(bool(e['changed']) for e in summary.get('tail_route_edits',[])),
        service_count=len(summary.get('service_receipts',[])),
        minimum_service_upper_slack_s=min((min(e['local_upper_slack_s'],e['completion_and_successor_slack_s']) for e in summary.get('service_receipts',[])),default=None),
        regional_probe_count=summary.get('regional_probe_count'),
        active_information_reads=summary.get('active_information_reads'),
        max_pending_sources=summary.get('max_pending_sources'),source_waits=summary.get('source_waits'))


def tex(value):
    if value is None:
        return r'\textbf{待补}'
    if isinstance(value,float):
        return f'{value:.3f}'
    result=str(value)
    return ''.join({'\\':r'\textbackslash{}','_':r'\_','%':r'\%','&':r'\&',
                    '#':r'\#','{':r'\{','}':r'\}','$':r'\$','^':r'\textasciicircum{}',
                    '~':r'\textasciitilde{}'}.get(c,c) for c in result)


def build_tables(rows,strategy=V7):
    version='第七版' if strategy==V7 else '第六版'
    lines=['% Only '+strategy+' formal rows supplied by the operator. Missing slots remain pending.']
    for problem in (3,4):
        selected=[r for r in rows if r['strategy']==strategy and r['problem']==problem and r['run_kind']=='formal']
        lines.extend([r'\begin{table}[htbp]\centering\small',
            r'\caption{问题'+str(problem)+version+r'正式结果}',
            r'\begin{tabular}{llrrr}\toprule',
            r'序号&案例编码&清除数&平均时间/秒&官方运行时间/秒\\\midrule'])
        for i in range(max(3,len(selected))):
            r=selected[i] if i<len(selected) else {}
            fields=[str(i+1),tex(r.get('case_code')),tex(r.get('cleared_count')),
                    tex(r.get('average_clear_time_s')),tex(r.get('official_program_runtime_s'))]
            lines.append('&'.join(fields)+r'\\')
        lines.extend([r'\bottomrule\end{tabular}\end{table}'])
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description='只读取你提供的实际运行文件夹，按版本整理论文结果')
    parser.add_argument('runs',nargs='+',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--strategy',choices=('v6','v7'),default='v7')
    parser.add_argument('--paper',type=Path,help='可选：将真实正式表写入带结果标记的论文LaTeX源文件')
    args=parser.parse_args();rows=[read_run(path) for path in args.runs]
    strategy=V7 if args.strategy=='v7' else V6
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'真实运行汇总.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (args.output/'正式结果表.tex').write_text(build_tables(rows,strategy),encoding='utf-8')
    if args.paper:
        manuscript=args.paper.read_text(encoding='utf-8')
        begin='% BEGIN_'+args.strategy.upper()+'_FORMAL_RESULTS';end='% END_'+args.strategy.upper()+'_FORMAL_RESULTS'
        first=manuscript.index(begin)+len(begin);last=manuscript.index(end,first)
        manuscript=manuscript[:first]+'\n'+build_tables(rows,strategy)+manuscript[last:]
        args.paper.write_text(manuscript,encoding='utf-8')
    lines=['# 实际运行结果','', '每行保留原版本与案例。不同案例间的耗时差不能直接归因为算法改进。','',
           '|版本|题号|类型|案例|清除数|虚拟时间|移动时间|末次清除后排除时间|官方耗时|',
           '|---|---|---|---|---:|---:|---:|---:|---:|']
    for row in rows:
        fields=[row[k] for k in ('strategy','problem','run_kind','case_code','cleared_count',
                                'virtual_time_s','movement_time_s','tail_exclusion_time_s','official_program_runtime_s')]
        lines.append('|'+ '|'.join('待补' if x is None else f'{x:.3f}' if isinstance(x,float) else str(x) for x in fields)+'|')
    (args.output/'真实运行汇总.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('已整理实际结果；没有启动或连接模拟器。')


if __name__=='__main__':
    main()
