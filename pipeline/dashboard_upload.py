"""Upload saved classifications to the owner-private temporary import endpoint.
Credential is read through hidden terminal input and never saved.
"""
import argparse,getpass,json,time,urllib.request
from pathlib import Path
from .common import read_json,write_json
from .store import records

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--restart',action='store_true');args=parser.parse_args()
    token=getpass.getpass('Site service credential (hidden): ')
    root=Path('runs/final-100k')
    config=read_json(root/'label_configuration.json')
    state=Path('evidence/dashboard-import-progress.json')
    previous=read_json(state) if state.exists() else {}
    offset=0 if args.restart else previous.get('uploaded',0)
    revision='final-100013-a88f521a4089'
    rows=records(root/'source.sqlite',config['label_config'])
    batch=[];position=0
    def send(batch,position):
        body=json.dumps({'revision':revision,'rows':batch},ensure_ascii=False).encode()
        for attempt in range(4):
            try:
                req=urllib.request.Request('https://spotify-review-evidence.jenna851121.chatgpt.site/api/import',data=body,headers={'Content-Type':'application/json','OAI-Sites-Authorization':'Bearer '+token},method='POST')
                with urllib.request.urlopen(req,timeout=90) as response: result=json.load(response)
                assert result['accepted']==len(batch) and result['revision']==revision
                break
            except Exception:
                if attempt==3:raise
                time.sleep(2**attempt)
        write_json(state,{'state':'importing' if position<100013 else 'uploaded_pending_validation','uploaded':position,'total':100013,'revision':revision})
        if position%1000==0 or position==100013:print('Saved to dashboard database:',position,flush=True)
    for row in rows:
        position+=1
        if position<=offset:continue
        batch.append(row)
        if len(batch)==100:send(batch,position);batch=[]
    if batch:send(batch,position)

if __name__=='__main__':main()
