#!/bin/bash
cd "$(dirname "$0")"
python3 export.py > export.log 2>&1
echo EXPORT_DONE >> export.log
python3 verify.py --sweep > verify.log 2>&1 &
python3 slice.py > slice.log 2>&1
echo SLICE_DONE >> slice.log
wait
echo ALL_DONE >> verify.log
