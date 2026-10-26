"""Run-level split, shared feature extraction, and honest synthetic evaluation."""
import argparse
import csv
import json
import random
import joblib
import numpy as np
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,confusion_matrix
from sklearn.model_selection import train_test_split
from common import ROOT,OUT,output_dir
from edr_agent.features import features,vector,FEATURE_NAMES
from edr_agent.window import Window
from generate_events import BASE

def windows(events: list[dict],cfg: dict):
    window=Window(cfg['window_seconds']);index=0
    for now in range(BASE+2,BASE+301,2):
        while index<len(events) and events[index]['ts']<=now:window.add(events[index]);index+=1
        yield now,window.snapshot(now)

def train(seed: int=42) -> None:
    output_dir();cfg=yaml.safe_load((ROOT/'agent/config.yaml').read_text());labels=list(csv.DictReader((OUT/'labels.csv').open()))
    ids=[row['scenario'] for row in labels]
    train_ids,test_ids=train_test_split(ids,test_size=.3,random_state=seed,stratify=[row['scenario'].split('_')[0] for row in labels])
    assert not set(train_ids)&set(test_ids)
    train_set=set(train_ids);x_train=[];y_train=[];x_test=[];y_test=[]
    for row in labels:
        events=[json.loads(line) for line in (OUT/(row['scenario']+'.jsonl')).read_text().splitlines()]
        for now,items in windows(events,cfg):
            label=int(int(row['label'])==1 and min(now,float(row['end_ts']))-max(now-10,float(row['start_ts']))>=3)
            x,y=(x_train,y_train) if row['scenario'] in train_set else (x_test,y_test)
            x.append(vector(features(items,cfg)));y.append(label)
    model=RandomForestClassifier(n_estimators=200,max_depth=12,class_weight='balanced',random_state=42)
    model.fit(x_train,y_train);pred=model.predict(x_test)
    scores={name:float(fn(y_test,pred)) for name,fn in [('accuracy',accuracy_score),('precision',precision_score),('recall',recall_score),('F1',f1_score)]}
    folder=ROOT/'agent/models'
    if folder.is_symlink():raise ValueError('Model directory must not be a symlink')
    folder.mkdir(exist_ok=True);joblib.dump(model,folder/'rf_model.joblib')
    report='# Synthetic model evaluation\n\nThis model is trained on synthetic data; its real-world performance is unknown.\n\n'
    report+=f'{len(train_ids)} training runs / {len(test_ids)} test runs; {len(x_train)} training windows / {len(x_test)} test windows. Split by scenario run; no overlap.\n\n'
    report+='| Metric | Value |\n|---|---:|\n'+''.join(f'| {k} | {v:.4f} |\n' for k,v in scores.items())
    report+='\nConfusion matrix (rows true, columns predicted; class order 0, 1):\n\n```\n'+str(confusion_matrix(y_test,pred))+'\n```\n\n| Feature | Importance |\n|---|---:|\n'
    report+=''.join(f'| {k} | {v:.5f} |\n' for k,v in zip(FEATURE_NAMES,model.feature_importances_))
    report+='\nTargets: recall >= 0.95, precision >= 0.90. '+('Met.' if scores['recall']>=.95 and scores['precision']>=.9 else 'Not met; no tuning on the held-out test set was performed.')+'\n'
    (OUT/'ml_report.md').write_text(report);(OUT/'split.json').write_text(json.dumps({'train':train_ids,'test':test_ids},indent=2));print(report)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=42);a=p.parse_args();train(a.seed)
