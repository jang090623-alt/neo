#!/bin/bash
# 사용: pair.sh 출력폴더 scad A:B
out=$1; scad=$2; a=${3%:*}; b=${3#*:}; f=$out/$a-$b.stl
openscad -D "A=\"$a\"" -D "B=\"$b\"" -o $f $scad >/dev/null 2>&1
if [ -f $f ]; then python3 -I /tmp/claude-0/-home-user-neo/21154a9a-5e67-5b18-aa52-799842e662e3/scratchpad/tools/vol.py $f | sed "s#^.*/##"; else echo "$a-$b: 겹침 0"; fi
