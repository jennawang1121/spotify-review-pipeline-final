"""Prepare an honest private dashboard while final independent checks run."""
import random,sqlite3
from pathlib import Path
from .common import read_json,write_json,canonical,digest
from .store import records,validate_prediction
from .providers import openai_request,response_json
from .runner import prediction_schema

def main():
    root=Path('runs/final-100k');config=read_json(root/'label_configuration.json')
    rows=list(records(root/'source.sqlite',config['label_config']))
    eligible=[r for r in rows if r['status']=='completed']
    sample=sorted(random.Random(config['verification_seed']).sample(sorted(eligible,key=lambda r:r['review_id']),5000),key=lambda r:r['review_id'])
    checked=[];pending=0
    for r in sample:
        rid=r['review_id'];text=r['source']['review_text'];failed=root/'verification_failures'/(rid+'.json')
        if failed.exists():checked.append(read_json(failed));continue
        payload=openai_request(config,config['prompts']['verification'],{'review_text':text,'taxonomy':config['taxonomy']},prediction_schema(config))
        fingerprint=digest(canonical(['openai','verify','verification',payload,config['label_config']]))
        p=root/'response_cache'/(fingerprint+'.json')
        if not p.exists():pending+=1;continue
        saved=read_json(p);prediction=response_json(saved['response']);validate_prediction(prediction,text,config['taxonomy'])
        checked.append({'review_id':rid,'status':'completed','independent_prediction':prediction,'first_prediction':r['prediction'],'verifier_request_id':saved['request_id'],'disagreements':[f for f in ('topic','intent','severity','needs_review') if prediction[f]!=r['prediction'][f]],'sentiment_absolute_difference':abs(prediction['sentiment']-r['prediction']['sentiment'])})
    valid=[r for r in checked if r['status']=='completed'];failed=[r for r in checked if r['status']=='failed']
    db=sqlite3.connect('file:'+str(root/'budget.sqlite')+'?mode=ro',uri=True)
    cost,count=db.execute("select sum(charged_nanos)/1e9,sum(outcome='succeeded') from reservations").fetchone();db.close()
    pack=read_json('evidence/final-classification-audit/evidence_pack.json')
    quality={'sample_size':5000,'valid_comparisons':len(valid),'failed_verifications':len(failed),'pending_verifications':pending,'agreement_counts':{f:sum(r['first_prediction'][f]==r['independent_prediction'][f] for r in valid) for f in ('topic','intent','severity','needs_review')},'needs_review_count':sum(r['prediction']['needs_review'] for r in eligible),'sentiment_mean_absolute_difference':sum(r['sentiment_absolute_difference'] for r in valid)/len(valid) if valid else None}
    summary={'status':'final_classification_complete_verification_in_progress','source_rows':len(rows),'completed':len(eligible),'costs_this_experiment':{'known_api_usd':str(cost)},'outcomes':{'succeeded':count},'quality':quality,'warm_replay_complete':False}
    pending_memo='Final recommendation is pending completion of independent verification and the memo stage. The issue ranking already reflects all 100,000 classified nonempty reviews.'
    seed={'revision':'final-100013-'+config['label_config'][:12],'external_count':len(rows),'metadata_version':'verification-progress-'+str(len(checked)),'reviews':[],'summary':summary,'memo':pending_memo,'raw_memo':pending_memo,'recommendation':{'priority_issue_id':'pending','recommendation':pending_memo,'alternatives':'Alternatives and limitations will be published with the final verified recommendation.','claim_ids':[],'review_ids':[]},'names':{'issues':[{'issue_id':r['issue_id'],'name':r['issue_id'].removeprefix('issue-').title()} for r in pack['ranking']]},'pack':pack,'taxonomy':config['taxonomy'],'verification':checked,'final_scope':read_json('evidence/scope-100k.json')}
    write_json('dashboard/data/seed.json',seed)
    print({'classified':len(eligible),'verification_valid':len(valid),'verification_failed':len(failed),'verification_pending':pending})
if __name__=='__main__':main()
