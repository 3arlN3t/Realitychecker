#!/usr/bin/env python3
import os, sys
os.execv(sys.executable, [sys.executable, 'scripts/tools/populate_sample_data.py'] + sys.argv[1:])

