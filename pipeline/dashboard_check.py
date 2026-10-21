"""Compare deployed SQL results with every saved original ID/hash/status.
Use --private to supply the Site service token through hidden terminal input.
"""
import argparse,getpass,hashlib,json,urllib.request,urllib.error
from .common import read_json,write_json
from .store import records

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--private',action='store_true');parser.add_argument('--classification-only',action='store_true');args=parser.parse_args()
    headers={}
    if args.private:headers['OAI-Sites-Authorization']='Bearer '+getpass.getpass('Site service credential (hidden): ')
    base='https://spotify-review-evidence.jenna851121.chatgpt.site'
    def get(path):
        with urllib.request.urlopen(urllib.request.Request(base+path,headers=headers),timeout=90) as r:return json.load(r)
    config=read_json('runs/final-100k/label_configuration.json')
    rows=sorted(records('runs/final-100k/source.sqlite',config['label_config']),key=lambda r:r['review_id'])
    checked=0
    for start in range(0,len(rows),1000):
        part=rows[start:start+1000]
        expected=hashlib.sha256(''.join(r['review_id']+'|'+r['source_sha256']+'|'+r['status']+'\n' for r in part).encode()).hexdigest()
        actual=get('/api/integrity?page='+str(start//1000))
        assert actual['sha256']==expected and actual['rows']==len(part),(start,actual)
        checked+=len(part)
    try:
        urllib.request.urlopen(urllib.request.Request(base+'/api/import',headers=headers,data=b'{}',method='POST'),timeout=90)
    except urllib.error.HTTPError as error:
        assert error.code==405, 'Import endpoint is not disabled'
    else:
        raise AssertionError('Unexpected write endpoint response')
    summary=get('/api/summary');assert summary['coverage']['completed']==100000 and summary['coverage']['quarantined']==13
    ranking=get('/api/issues');expected=read_json('evidence/final-classification-audit/evidence_pack.json')['ranking']
    for a,b in zip(ranking,expected):
        for field in ['issue_id','rank','complaint_count','severity_sum','priority_score','mean_severity']:assert str(a[field])==str(b[field]),field
    assert len(ranking)==len(expected)
    # Check actual source/prediction payloads, not only stored hash columns.
    samples=[rows[i] for i in [0,len(rows)//4,len(rows)//2,3*len(rows)//4,len(rows)-1]]
    samples+= [next(r for r in rows if r['status']=='quarantined')]
    for row in samples:
        actual=get('/api/reviews/'+row['review_id'])
        assert actual['source']==row['source'] and actual.get('prediction')==row['prediction']
    quality=get('/api/quality');assert quality['summary']['sample_size']==5000
    if not args.classification_only:
        assert len(quality['verification'])==5000 and not quality['summary'].get('pending_verifications',0)
        memo=get('/api/recommendation');assert memo['structured']['priority_issue_id'] in {r['issue_id'] for r in ranking}
    result={'stage':'classification_database_only' if args.classification_only else 'final_dashboard','status':'pass','access':'owner-private' if args.private else 'anonymous-public','all_id_hash_status_rows_checked':checked,'actual_source_prediction_samples':len(samples),'ranking_matches':True,'import_endpoint_disabled':True,'coverage':summary['coverage'],'quality':quality['summary'],'url':base}
    write_json('evidence/dashboard-'+('classification-' if args.classification_only else 'final-')+('private' if args.private else 'public')+'-checks.json',result)
    print('Dashboard verified:',checked,'IDs/hashes/statuses; all rankings; source/prediction samples.',flush=True)
if __name__=='__main__':main()
