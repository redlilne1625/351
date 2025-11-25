#!/usr/bin/env bash
# Usage: ./add_run_template.sh LABEL VOLUME_ML START_TS END_TS NOTES "rpm=100;speed=1.2"
if [ $# -lt 5 ]; then
  echo "Usage: $0 LABEL VOLUME_ML START_TS END_TS NOTES TAGS"
  exit 1
fi
LABEL=$1; VOL=$2; START=$3; END=$4; NOTES=$5; TAGS=${6:-}
# append to calib_points.csv
if [ ! -f calib_points.csv ]; then
  echo "label,volume_ml,start_ts,end_ts,notes,tags" > calib_points.csv
fi
echo "${LABEL},${VOL},${START},${END},\"${NOTES}\",\"${TAGS}\"" >> calib_points.csv
echo "Appended ${LABEL}"
