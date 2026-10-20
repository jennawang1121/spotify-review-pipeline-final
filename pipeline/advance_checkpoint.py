"""Run the authorized 10k checkpoint through bounded runtime pauses.
Stops on any failure except the explicit runtime cap; never raises the budget.
"""
import argparse
import sys
import time
from pathlib import Path
from .common import configuration, read_json, write_json
from .runner import run_checkpoint
from .store import status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final-100k', action='store_true')
    args = parser.parse_args()
    config = configuration('config-final-100k.json' if args.final_100k else 'config-2-workers.json')
    run = Path('runs/final-100k' if args.final_100k else 'runs/checkpoint-10000')
    source = 'data/scope-100k/analysis.csv' if args.final_100k else 'data/course/analysis_10000.csv'
    label = '100k' if args.final_100k else '10k'
    phase = 'resume' if (run/'run_manifest.json').exists() else 'initial' 
    allocation = read_json('evidence/pilot-budget-allocation.json')
    cap = next(x['cumulative_cap_usd'] for x in allocation['allocations'] if x['directory']==str(run))
    assert cap == ('6.00' if args.final_100k else '0.80')
    progress = Path('evidence/final-100k-progress.json' if args.final_100k else 'evidence/checkpoint-10000-progress.json')
    for segment in range(1, 121):
        print('Starting bounded resume segment '+str(segment), flush=True)
        try:
            result = run_checkpoint(source, config, run, phase, cap, True)
        except ValueError as error:
            snapshot = status(run/'source.sqlite',config['label_config'])
            if 'Run time cap reached' not in str(error):
                write_json(progress, {'state':'failed_visible','error':str(error),'segment':segment,'snapshot':snapshot,'budget_cap_usd':cap})
                raise
            write_json(progress, {'state':'resuming_after_runtime_cap','segment':segment,'snapshot':snapshot,'budget_cap_usd':cap})
            print('Runtime cap pause; committed progress: '+str(snapshot),flush=True)
            phase = 'resume'
            continue
        write_json(progress, {'state':result['status'],'segment':segment,'snapshot':status(run/'source.sqlite',config['label_config']),'budget_cap_usd':cap})
        if result['status']=='completed':
            print(label+' checkpoint completed. Running zero-call warm replay.',flush=True)
            warm = run_checkpoint(source,config,run,'warm',cap,True)
            write_json(progress, {'state':'completed_and_warm_replayed','result':result,'warm':warm,'budget_cap_usd':cap,'snapshot':status(run/'source.sqlite',config['label_config'])})
            from .checkpoint_report import summarize
            summarize(run, Path('evidence/final-100k' if args.final_100k else 'evidence/checkpoint-10000'))
            return
    raise ValueError('Maximum bounded segments reached; saved progress retained.')

if __name__=='__main__': main()
