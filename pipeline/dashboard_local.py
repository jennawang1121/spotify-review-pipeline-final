"""Load saved pipeline records into the local dashboard database without API calls."""
import argparse,json,sqlite3
from pathlib import Path
from .common import read_json
from .store import records

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-dir',default='runs/final-100k');parser.add_argument('--dashboard',default='dashboard');args=parser.parse_args()
    site=Path(args.dashboard);run=Path(args.run_dir);seed=read_json(site/'data/seed.json');config=read_json(run/'label_configuration.json')
    destination=site/'.sites-runtime/preview.sqlite';destination.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(destination)
    db.execute('CREATE TABLE IF NOT EXISTS _preview_migrations(name TEXT PRIMARY KEY)')
    for path in sorted((site/'drizzle').glob('*.sql')):
        if not db.execute('SELECT name FROM _preview_migrations WHERE name=?',(path.name,)).fetchone():
            db.executescript(path.read_text());db.execute('INSERT INTO _preview_migrations VALUES(?)',(path.name,));db.commit()
    def values():
        for r in records(run/'source.sqlite',config['label_config']):
            if r['status']=='pending':raise ValueError('Unclassified record; local import refused')
            p=r['prediction'];payload={k:r[k] for k in ['prediction','provenance','cache_source_id','label_config']}
            yield(seed['revision'],r['review_id'],r['source_sha256'],json.dumps(r['source']),json.dumps(payload) if p else None,r['status'],p['topic'] if p else None,p['intent'] if p else None,p['severity'] if p else None,int(p['needs_review']) if p else None)
    with db:db.executemany('INSERT OR IGNORE INTO reviews(dataset_id,review_id,source_hash,source_json,prediction_json,status,topic,intent,severity,needs_review) VALUES(?,?,?,?,?,?,?,?,?,?)',values())
    n=db.execute('SELECT count(*) FROM reviews WHERE dataset_id=?',(seed['revision'],)).fetchone()[0];db.close()
    assert n==seed.get('external_count',len(seed['reviews']))
    print('Local dashboard database ready:',n,'records; zero model calls.')
if __name__=='__main__':main()
