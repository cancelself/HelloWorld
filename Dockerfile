FROM python:3.12-slim

WORKDIR /app

# Install Litestream
ADD https://github.com/benbjohnson/litestream/releases/download/v0.3.13/litestream-v0.3.13-linux-amd64.tar.gz /tmp/litestream.tar.gz
RUN tar -xzf /tmp/litestream.tar.gz -C /usr/local/bin && rm /tmp/litestream.tar.gz

# Install runtime dependencies (core language is stdlib-only, these are for the MCP server)
RUN pip install --no-cache-dir mcp[cli] anthropic

# Copy project
COPY src/ src/
COPY vocabularies/ vocabularies/
COPY helloworld.py .
COPY litestream.yml /etc/litestream.yml
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Persistent storage: OAuth tokens, message bus, collision log
RUN mkdir -p storage
VOLUME /app/storage

EXPOSE 8080

ENV HELLOWORLD_SERVER_URL=http://localhost:8080
ENV HELLOWORLD_OAUTH_DB=/app/storage/oauth.db
ENV HW_TRANSPORT=sqlite
ENV HW_SQLITE_PATH=/app/storage/messages.db

ENTRYPOINT ["./entrypoint.sh"]
