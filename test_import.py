

import sys
import os
import traceback

sys.path.append(os.getcwd())

print("--- Testing edge_rsu.config ---")
try:
    import edge_rsu.config
    print("Success: edge_rsu.config")
except Exception:
    traceback.print_exc()

print("\n--- Testing edge_rsu.database.connection ---")
try:
    import edge_rsu.database.connection
    print("Success: edge_rsu.database.connection")
except Exception:
    traceback.print_exc()

print("\n--- Testing edge_rsu.database.models ---")
try:
    import edge_rsu.database.models
    print("Success: edge_rsu.database.models")
except Exception:
    traceback.print_exc()

print("\n--- Testing routes_auth ---")
try:
    from edge_rsu.api import routes_auth
    print("Success: routes_auth")
except Exception:
    traceback.print_exc()

