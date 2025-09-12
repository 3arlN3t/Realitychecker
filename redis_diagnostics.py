#!/usr/bin/env python3
import os, sys
os.execv(sys.executable, [sys.executable, 'scripts/monitoring/redis_diagnostics.py'] + sys.argv[1:])

