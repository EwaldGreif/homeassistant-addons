FROM python:3.11-slim

# Hilfstool jq installieren
RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*

COPY run.sh /
RUN chmod +x /run.sh

CMD ["/run.sh"]
