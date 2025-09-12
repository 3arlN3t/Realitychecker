#!/usr/bin/env python3
import os, sys
os.execv(sys.executable, [sys.executable, 'scripts/tools/debug_webhook_validation.py'] + sys.argv[1:])

