#!/usr/bin/env bash
# Usage: ./add_motor_data.sh LABEL VOLTAGE CURRENT RPM
if [ $# -lt 4 ]; then
  echo "Usage: $0 LABEL VOLTAGE CURRENT RPM"
  exit 1
fi
LABEL=$1; V=$2; I=$3; RPM=$4
# update pump_dataset.csv: find row by label and append columns (simple CSV rewrite)
python3 - <<PY
import csv,sys
label="${LABEL}"; V=${V}; I=${I}; RPM=${RPM}
rows=[]
with open('pump_dataset.csv','r') as f:
    r=csv.DictReader(f)
    fieldnames=r.fieldnames
    for row in r:
        if row['label']==label:
            row['voltage_V']=str(V); row['current_A']=str(I); row['rpm']=str(RPM)
        rows.append(row)
if 'voltage_V' not in fieldnames:
    fieldnames += ['voltage_V','current_A','rpm']
with open('pump_dataset.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fieldnames); w.writeheader(); w.writerows(rows)
print("Updated", label)
PY
