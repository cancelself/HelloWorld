#!/bin/sh
set -e

# Restore databases from GCS (if replicas exist)
litestream restore -if-replica-exists -config /etc/litestream.yml /app/storage/messages.db
litestream restore -if-replica-exists -config /etc/litestream.yml /app/storage/oauth.db

# Run the app under Litestream (replicates continuously, forwards signals)
exec litestream replicate -config /etc/litestream.yml -exec \
  "python3 helloworld.py --mcp --port 8080 --auth"
