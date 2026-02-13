
import sys
import os
import traceback

sys.path.append(os.getcwd())

print("--- Testing routes_auth import ---")
try:
    from edge_rsu.api import routes_auth
    print("Success: routes_auth")
except Exception:
    traceback.print_exc()
