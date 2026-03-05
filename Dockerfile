FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies (core language is stdlib-only, these are for the MCP server)
RUN pip install --no-cache-dir mcp[cli] anthropic

# Copy project
COPY src/ src/
COPY vocabularies/ vocabularies/
COPY helloworld.py .

# Persistent storage: OAuth tokens, message bus, collision log
RUN mkdir -p storage
VOLUME /app/storage

EXPOSE 8080

# Default: HTTP + OAuth on port 8080
# Override HELLOWORLD_SERVER_URL with your public URL
# OAuth DB lives at HELLOWORLD_OAUTH_DB (default: storage/oauth.db)
ENV HELLOWORLD_SERVER_URL=http://localhost:8080
ENV HELLOWORLD_OAUTH_DB=/app/storage/oauth.db

ENTRYPOINT ["python3", "helloworld.py", "--mcp", "--port", "8080", "--auth"]
