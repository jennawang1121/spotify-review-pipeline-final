"""Generate transparent offline quality and project-budget reports."""
from collections import Counter,defaultdict
from decimal import Decimal
from pathlib import Path
import sqlite3
from .common import read_json,read_jsonl,write_json,atomic_text
from .store import records

def build():
    root=Path('runs/final-100k');out=Path('evidence/final-100k')
    rows=list(read_jsonl(root/'verification.jsonl'))
    valid=[r for r in rows if r.get('status','completed')=='completed']
    failures=[r for r in rows if r.get('status')=='failed']
    config=read_json(root/'label_configuration.json')
    sources={r['review_id']:r['source']['review_text'] for r in records(root/'source.sqlite',config['label_config'])}
    confusion={}
    examples=[]
    for field in ('topic','intent','severity','needs_review'):
        count=Counter((str(r['first_prediction'][field]),str(r['independent_prediction'][field])) for r in valid)
        confusion[field]={a+' -> '+b:n for (a,b),n in count.most_common()}
        mismatches=[r for r in valid if r['first_prediction'][field]!=r['independent_prediction'][field]]
        for r in mismatches[:5]:examples.append({'field':field,'review_id':r['review_id'],'source':sources[r['review_id']],'first':r['first_prediction'][field],'verifier':r['independent_prediction'][field],'meaning':'Observed disagreement; neither model is assumed to be ground truth.'})
    report={'selected_sample':len(rows),'valid_comparisons':len(valid),'failed_verifications':len(failures),'confusion':confusion,'examples':examples,'failures':failures,'labels_changed_after_verification':0,'reference_labels_supplied_to_models':False}
    write_json(out/'quality-feedback.json',report)
    text=['# Final independent verification feedback','',f'Selected sample: {len(rows)} original IDs. Valid comparisons: {len(valid)}. Failed independent checks: {len(failures)}. Failed checks remain in the sample denominator and never count as agreements. Sentiment MAE uses valid comparisons only.','', 'This measures model disagreement, not human accuracy. No first-pass label was overwritten to improve agreement. Golden 50 reference answers were not supplied to either model.','', '## Observed disagreements','']
    for e in examples:
        text.extend([f"- {e['field']}: {e['first']} → {e['verifier']} — review `{e['review_id']}`",'  Source: '+repr(e['source'])])
    text.extend(['','## Bounded verifier failures',''])
    for r in failures:text.append('- Review `'+r['review_id']+'`: '+r['error']+' Saved attempt `'+r['verifier_request_id']+'`.')
    text.extend(['','## Interpretation','', 'Inspect topic boundaries, severity evidence and review flags separately. A quote mismatch is an extraction/validation failure and cannot establish a semantic label error. Do not change predictions based only on the verifier, and do not tune prompts on the held-out reference. Prioritize manual inspection of severe functional harm and recurring confusion patterns before using the recommendation for a product decision.'])
    atomic_text(out/'quality-feedback.md','\n'.join(text)+'\n')
    budget=read_json('evidence/pilot-budget-allocation.json');spend=[]
    for allocation in budget['allocations']:
        p=Path(allocation['directory'])/'budget.sqlite'
        if not p.exists():continue
        db=sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True)
        paid,reserved,count=db.execute('select coalesce(sum(charged_nanos),0),coalesce(sum(case when charged_nanos is null then reserved_nanos else 0 end),0),sum(charged_nanos is null) from reservations').fetchone();db.close()
        spend.append({'directory':allocation['directory'],'known_usd':str(Decimal(paid)/Decimal(10**9)),'unresolved_reserved_usd':str(Decimal(reserved)/Decimal(10**9)),'unresolved_attempts':count or 0})
    known=sum(Decimal(s['known_usd']) for s in spend);reserved=sum(Decimal(s['unresolved_reserved_usd']) for s in spend)
    write_json(out/'project-cost.json',{'known_api_usd':str(known),'unresolved_reserved_usd':str(reserved),'known_plus_reservations_usd':str(known+reserved),'approved_total_api_cap_usd':'7.00','within_allocated_boundary':known+reserved<=Decimal('7'),'experiments':spend,'provider_invoice_reconciled':False,'hosting_and_local_compute':'excluded'})
    return report

if __name__=='__main__':build()
