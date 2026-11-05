#!/bin/bash
# rend.sh 출력png step cu [카메라] [크기]
cam=${4:-0,0,0,62,0,28,0}; size=${5:-1600,1100}
xvfb-run -a openscad -D step=$2 -D cu=$3 -o $1 --imgsize=$size --viewall --autocenter --colorscheme=Tomorrow --camera=$cam det.scad >/dev/null 2>&1 || echo "실패 $1"
