#!/usr/bin/env python3
import os, sys
os.execv(sys.executable, [sys.executable, 'scripts/monitoring/monitor_health.py'] + sys.argv[1:])

