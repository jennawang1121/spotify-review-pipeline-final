"""Package the completed grading evidence, keeping unknown usage visible."""
import shutil,zipfile
from pathlib import Path
from .common import read_json,write_json,file_sha,read_jsonl

def main():
    root=Path('runs/final-100k');evidence=Path('evidence/final-100k');out=Path('outputs')
    progress=read_json('evidence/final-100k-progress.json')
    if progress['state']!='completed_and_warm_replayed':raise ValueError('Final stages and warm replay are not complete')
    check=read_json(evidence/'official-check.json')
    assert check['coverage']['valid_completed']==100000 and check['coverage']['quarantined']==13
    assert set(check['issue_counts'])<= {'invalid_usage'}, 'Resolve other checker issues before packaging'
    assert (evidence/'memo.editorial.md').exists() and (evidence/'memo-audit.json').exists(), 'Review memo first'
    for name in ['memo.md','memo.structured.json','issue_names.json','verification.jsonl','label_configuration.json']:
        shutil.copy2(root/name,evidence/('memo.raw.md' if name=='memo.md' else name))
    warm=[]
    for p in (root/'cost').glob('warm-*/measurement.json'):
        measurement=read_json(p)
        if measurement['outcome']=='completed':warm.append((p,measurement))
    assert warm
    path,measurement=warm[-1];calls=list(read_jsonl(path.parent/'calls.jsonl'));assert not calls
    write_json(evidence/'warm-check.json',{'new_api_calls':0,'new_api_cost_usd':'0','measurement':measurement,'calls_artifact':str(path.parent/'calls.jsonl')})
    archive=out/'spotify-100k-submission.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(Path('grading').iterdir()):
            if p.is_file():z.write(p,str(p))
        z.write('runs/reference-final-100k.json','runs/reference-final-100k.json')
        for p in sorted(evidence.rglob('*')):
            if p.is_file() and p.name!='lineage-calls.jsonl':z.write(p,str(p))
        for p in sorted((root/'analysis').iterdir()):
            if p.is_file():z.write(p,str(p))
        for name in ['membership.csv','memo.md','memo.structured.json','issue_names.json','verification.jsonl','run_manifest.json','seed_provenance.json']:
            z.write(root/name,str(root/name))
    artifacts=[]
    for p in [out/'spotify-100k-saved-run.zip',archive]:
        assert p.exists();artifacts.append({'file':p.name,'bytes':p.stat().st_size,'sha256':file_sha(p)})
    write_json(out/'final-artifact-manifest.json',{'classification_complete':100000,'quarantined':13,'official_checker_status':check['status'],'official_checker_issues':check['issue_counts'],'unknown_usage_policy':'Never replace missing provider usage with zero; failed attempts remain in the full call log.','artifacts':artifacts})
    print(artifacts)
if __name__=='__main__':main()
