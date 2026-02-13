#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python deps
pip install -r requirements.txt

# Build Frontend
cd dashboard
npm install
npm run build
cd ..

# Run migrations (if any)
# python -c "import edge_rsu.database.connection; import asyncio; asyncio.run(edge_rsu.database.connection.init_db())"
