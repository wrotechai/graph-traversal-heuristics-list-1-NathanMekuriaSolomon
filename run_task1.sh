#!/bin/bash
# Task 1 runner — finds shortest path from stop A to stop B.
python3 -m pip install pandas
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python3 -X utf8 solution.py "$1" "$2" "$3" "$4"
