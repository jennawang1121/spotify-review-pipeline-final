"""Finish offline final artifacts when the authorized paid run completes."""
import time
from pathlib import Path
from .common import configuration, read_json, write_json, write_jsonl
from .contract import export_grading, audit
from .checkpoint_report import summarize
from .store import records
import subprocess
import sys


def main():
    root = Path('runs/final-100k')
    progress = Path('evidence/final-100k-progress.json')
    end = time.monotonic() + 36*3600
    while time.monotonic() < end:
        state = read_json(progress)
        if state['state'] == 'failed_visible':
            raise RuntimeError('Paid run stopped visibly; do not produce a final completion claim.')
        if state['state'] == 'completed_and_warm_replayed':
            break
        time.sleep(60)
    else:
        raise RuntimeError('Final run not complete within artifact wait window.')
    config = configuration('config-final-100k.json')
    summary = summarize(root, 'evidence/final-100k')
    calls = {}
    for name in ['pilot-benchmark','checkpoint-500','checkpoint-10000','golden-evaluation','final-100k']:
        for path in (Path('runs')/name/'attempts').glob('*.json'):
            event = read_json(path)
            calls[event['request_id']] = event
    write_jsonl('evidence/final-100k/lineage-calls.jsonl', sorted(calls.values(),key=lambda x:(x['started_at'],x['request_id'])))
    # Use the actual earlier recorded checkpoint across the complete lineage;
    # never relabel historic initial/resume phases to satisfy the checker.
    before = 'runs/checkpoint-10000/checkpoint_before.json'
    after = root/'checkpoint_after.json'
    write_json(after, {'completed_ids':[r['review_id'] for r in records(root/'source.sqlite',config['label_config']) if r['status']=='completed']})
    if not Path('grading').exists():
        export_grading(root/'source.sqlite',config,'data/course/spotify_reviews_18months.csv',
                       'evidence/final-100k/lineage-calls.jsonl',before,after,'grading')
    subprocess.run([sys.executable,'course/check_submission.py','reference','--full','data/course/spotify_reviews_18months.csv','--analysis','data/scope-100k/analysis.csv','--out','runs/reference-final-100k.json'],check=True)
    subprocess.run([sys.executable,'course/check_submission.py','check','--reference','runs/reference-final-100k.json','--submission','grading','--out','evidence/final-100k/official-check.json'],check=True)
    from .final_feedback import build
    build()
    result = read_json('evidence/final-100k/official-check.json')
    write_json('evidence/final-artifacts-progress.json',{'state':'offline_artifacts_complete','checker_status':result['status'],'issues':result['issue_counts'],'remaining':['Audit final memo argument','Update deployed database/dashboard','Publish final repository artifacts','Verify public access and submit URL']})
    print('Final offline artifacts ready. Checker:',result['status'],flush=True)

if __name__ == '__main__':
    main()
