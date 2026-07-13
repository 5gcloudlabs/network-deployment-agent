FROM python:3.12-slim

ARG KUBECTL_VERSION=v1.29.4

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl && \
    apt-get purge -y curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY prompts/ ./prompts/

# Root entrypoints for platform Helm chart commands (uvicorn main:app, chainlit run frontend.py)
RUN ln -sf backend/main.py main.py && \
    ln -sf frontend/frontend.py frontend.py && \
    ln -sf frontend/chainlit.md chainlit.md

EXPOSE 8000 8080
