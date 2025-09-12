#!/usr/bin/env python3
import os, sys
os.execv(sys.executable, [sys.executable, 'scripts/tools/setup_real_whatsapp.py'] + sys.argv[1:])

