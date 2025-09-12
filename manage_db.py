#!/usr/bin/env python3
import os, sys
os.execv(sys.executable, [sys.executable, 'scripts/db/manage_db.py'] + sys.argv[1:])

