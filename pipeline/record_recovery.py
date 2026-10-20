"""Capture actual subprocess output as asciinema v2 and a standalone player.
No credentials are passed in commands, recorded, or embedded in the artifact.
"""
import html
import json
import subprocess
import sys
import time
from pathlib import Path
from .common import configuration, read_json, write_json
from .store import status


def main():
    root = Path('runs/checkpoint-10000')
    out = Path('evidence/recovery-10k')
    out.mkdir(parents=True, exist_ok=True)
    config = configuration('config-2-workers.json')
    start = time.monotonic()
    events = []
    cast = out / 'stop-resume.cast'
    header = {'version': 2, 'width': 110, 'height': 30, 'timestamp': int(time.time()),
              'title': 'Real Jev checkpoint: save, stop, resume', 'env': {'TERM': 'xterm-256color'}}
    cast.write_text(json.dumps(header)+'\n')
    def emit(value):
        print(value, flush=True)
        event = [round(time.monotonic()-start, 6), 'o', value+'\r\n']
        events.append(event)
        with cast.open('a') as handle: handle.write(json.dumps(event,ensure_ascii=False)+'\n')
    for phase in ('initial','resume'):
        before = status(root/'source.sqlite', config['label_config'])
        command = [sys.executable, '-m', 'pipeline', '--config', 'config-2-workers.json',
                   'checkpoint', '--input', 'data/course/analysis_10000.csv', '--run-dir', str(root),
                   '--phase', phase, '--execute-paid', '--budget-usd', '0.80', '--stop-after', '25']
        emit('$ '+' '.join(command))
        emit('Observed saved status before: '+json.dumps(before,ensure_ascii=False))
        child = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        for line in child.stdout: emit(line.rstrip('\n'))
        code = child.wait()
        emit('Actual exit code: '+str(code))
        emit('Observed saved status after: '+json.dumps(status(root/'source.sqlite',config['label_config']),ensure_ascii=False))
        if code: raise SystemExit(code)
    before=set(read_json(root/'checkpoint_before.json')['completed_ids'])
    after=set(read_json(root/'checkpoint_after.json')['completed_ids'])
    attempts=[read_json(path) for path in (root/'attempts').glob('*.json')]
    resumed=[rid for call in attempts if call['phase']=='resume' and call['role']=='enrich' for rid in call['review_ids']]
    checks={'evidence_kind':'real_paid_execution_recording','before_completed_ids':len(before),
            'after_completed_ids':len(after),'saved_ids_retained':before<=after,
            'already_saved_ids_reclassified_on_resume':sorted(before & set(resumed)),
            'successful_new_unique_results':sum(c['outcome']=='succeeded' and c['stage']=='classification' for c in attempts),
            'budget_cap_usd':'0.80','max_workers':2,'recording_duration_seconds':round(time.monotonic()-start,6)}
    assert before<after and not checks['already_saved_ids_reclassified_on_resume']
    write_json(out/'checks.json',checks)
    emit('Verified from real saved attempts: '+json.dumps(checks))
    payload=json.dumps(events,ensure_ascii=False).replace('<','\\u003c')
    page='''<!doctype html><meta charset="utf-8"><title>Real stop/resume recording</title>
<style>body{background:#101820;color:#eee;font:16px system-ui;padding:24px}pre{white-space:pre-wrap;font:14px monospace;line-height:1.5}input{width:70%}button{padding:8px}</style>
<h1>Real Jev stop / resume recording</h1><p>Actual commands, subprocess output, and saved database observations. Playback speed: 10×. Original timestamps remain in the accompanying .cast file.</p>
<button id="play">Play</button> <input id="seek" type="range" min="0" step="0.1" value="0"><span id="time"></span><pre id="terminal"></pre>
<script>const events=EVENTS;const end=events.at(-1)[0];seek.max=end;let running=false,last=0;
function draw(){let t=+seek.value;terminal.textContent=events.filter(e=>e[0]<=t).map(e=>e[2]).join('');document.getElementById('time').textContent=t.toFixed(1)+' / '+end.toFixed(1)+' s';}
seek.oninput=draw;play.onclick=()=>{running=!running;play.textContent=running?'Pause':'Play';last=performance.now();};
function frame(now){if(running){seek.value=Math.min(end,+seek.value+(now-last)/100);draw();if(+seek.value>=end){running=false;play.textContent='Play';}}last=now;requestAnimationFrame(frame);}draw();requestAnimationFrame(frame);</script>'''.replace('EVENTS',payload)
    (out/'stop-resume.html').write_text(page)
    (out/'README.md').write_text('# Actual stop/resume recording\n\nTwo real paid invocations classify 25 new unique texts each, save and stop. The resumed invocation excludes all already saved IDs. The .cast captures actual subprocess output at original timings; the HTML is an offline player. This is a terminal recording, not a screen video. Existing labels were seeded from the completed 500 checkpoint. No Golden50 answers or credentials are recorded.\n')

if __name__=='__main__': main()
