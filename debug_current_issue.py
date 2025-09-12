#!/usr/bin/env python3
import os, sys
os.execv(sys.executable, [sys.executable, 'scripts/tools/debug_current_issue.py'] + sys.argv[1:])

