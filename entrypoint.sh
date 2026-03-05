#!/bin/sh
set -e

# Restore databases from GCS (if replicas exist)
litestream restore -if-replica-exists -config /etc/litestream.yml /app/storage/messages.db
litestream restore -if-replica-exists -config /etc/litestream.yml /app/storage/oauth.db

# Set up deploy key (Cloud Run mounts it as DEPLOY_KEY env var)
if [ -n "$DEPLOY_KEY" ]; then
  mkdir -p /root/.ssh
  printf '%s\n' "$DEPLOY_KEY" > /root/.ssh/deploy_key
  chmod 600 /root/.ssh/deploy_key
  cat > /root/.ssh/config <<SSHEOF
Host github.com
  IdentityFile /root/.ssh/deploy_key
  StrictHostKeyChecking no
SSHEOF
  # Clone repo for live vocabulary (vocabularies/ becomes the git working tree)
  if [ -n "$HELLOWORLD_REPO" ]; then
    git clone --depth 1 "$HELLOWORLD_REPO" /tmp/repo 2>/dev/null || true
    if [ -d /tmp/repo/vocabularies ]; then
      rm -rf /app/vocabularies
      cp -r /tmp/repo/vocabularies /app/vocabularies
      mv /tmp/repo/.git /app/.git
      rm -rf /tmp/repo
      git -C /app config user.email "helloworld-deploy@nrsh.org"
      git -C /app config user.name "HelloWorld MCP Server"
    fi
  fi
fi

# Run the app under Litestream (replicates continuously, forwards signals)
exec litestream replicate -config /etc/litestream.yml -exec \
  "python3 helloworld.py --mcp --port 8080 --auth"
