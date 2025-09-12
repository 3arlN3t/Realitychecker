#!/usr/bin/env python3
import os, sys
os.execv(sys.executable, [sys.executable, 'scripts/db/simple_db_setup.py'] + sys.argv[1:])

