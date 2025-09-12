#!/usr/bin/env python3
import os, sys
os.execv(sys.executable, [sys.executable, 'scripts/tools/verify_whatsapp_setup.py'] + sys.argv[1:])

