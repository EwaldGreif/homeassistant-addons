FROM python:3.11-slim

# Flask + jq installieren (optional, falls weitere Optionen genutzt werden)
RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*
RUN pip install flask

COPY run.sh /
COPY app /app

RUN chmod +x /run.sh

CMD ["/run.sh"]
