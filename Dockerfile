FROM --platform=linux/amd64 python:3.13-slim-bookworm

# tini for signal handling
ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /tini
RUN chmod +x /tini

# Build tools needed for eclipse-zenoh Rust compilation
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY requirements.txt requirements.txt

RUN uv pip install --system --no-cache -r requirements.txt

COPY --chmod=555 ./bin/* /usr/local/bin/

ENTRYPOINT ["/tini", "-g", "--", "/bin/bash", "-c"]
