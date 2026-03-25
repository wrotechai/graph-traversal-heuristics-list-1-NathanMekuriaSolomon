#!/bin/bash
# Task 2 runner — TSP: visit all stops and return to start.
python3 -m pip install pandas
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python3 -X utf8 solution.py "$1" "$2" "$3" "$4"
