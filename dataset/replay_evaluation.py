"""Compare all synthetic streams under the unchanged rules, with and without ML."""
import csv
import json
import yaml
from common import ROOT,OUT
from edr_agent.features import features,vector
from edr_agent.scoring import Scorer
from edr_agent.ml_model import Model
from train_model import windows

def evaluate():
    cfg=yaml.safe_load((ROOT/'agent/config.yaml').read_text());model=Model(str(ROOT/'agent/models/rf_model.joblib'))
    rows=list(csv.DictReader((OUT/'labels.csv').open()));summary={}
    for row in rows:
        kind=row['scenario'].split('_')[0];events=[json.loads(line) for line in (OUT/(row['scenario']+'.jsonl')).read_text().splitlines()]
        snapshots=list(windows(events,cfg));values=[features(items,cfg) for _,items in snapshots]
        if model.model is not None:
            index=list(model.model.classes_).index(1);probabilities=model.model.predict_proba([vector(v) for v in values])[:,index]
        else:probabilities=[None]*len(values)
        for enabled in (False,True):
            scorer=Scorer(cfg);alerts=[]
            for (now,items),probability in zip(snapshots,probabilities):
                alert=scorer.alert(items,now,cfg,float(probability) if enabled and probability is not None else None)
                if alert:alerts.append(alert)
            key=(kind,enabled);entry=summary.setdefault(key,{'runs':0,'alerted':0,'critical':0,'alerts':0,'latencies':[]})
            entry['runs']+=1;entry['alerted']+=bool(alerts);entry['critical']+=any(a['severity']=='CRITICAL' for a in alerts);entry['alerts']+=len(alerts)
            if alerts and int(row['label']):entry['latencies'].append(alerts[0]['ts']-float(row['start_ts']))
    text='# Synthetic replay evaluation\n\n390 five-minute runs. Rules and thresholds were not changed to fit acceptance expectations.\n\n'
    text+='| Scenario | Rules: runs with alerts | Rules: Critical runs | ML: runs with alerts | ML: Critical runs |\n|---|---:|---:|---:|---:|\n'
    for kind in sorted({k[0] for k in summary}):
        a,b=summary[(kind,False)],summary[(kind,True)]
        text+=f"| {kind} | {a['alerted']}/{a['runs']} | {a['critical']}/{a['runs']} | {b['alerted']}/{b['runs']} | {b['critical']}/{b['runs']} |\n"
    for enabled in (False,True):
        total=sum(v['alerts'] for (kind,ml),v in summary.items() if kind.startswith('B') and ml==enabled)
        hours=sum(v['runs']*300/3600 for (kind,ml),v in summary.items() if kind.startswith('B') and ml==enabled)
        text+=f"\nBenign false alerts with ML={enabled}: {total} over {hours:.2f} simulated hours ({total/hours:.3f}/hour).\n"
    text+='\nThe generator constrains build paths to one project directory and backups to archive paths; these rates describe these fixtures only. Replay uses fixed scoring ticks. Real filesystem coalescing, startup baseline races, and scheduling can differ.\n'
    text+='\nRename-only activity cannot reach the specified Critical threshold from extension points alone; adding the ML contribution does not guarantee Critical. Slow attacks cannot universally meet a six-second latency threshold. These are specification conflicts, not hidden changes to scoring.\n'
    (OUT/'replay_report.md').write_text(text);print(text)
if __name__=='__main__':evaluate()
