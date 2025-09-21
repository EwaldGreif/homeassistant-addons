FROM python:3.11-slim

# Installationen
RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*
RUN pip install flask
RUN pip install pyyaml

COPY run.sh /
COPY app /app

RUN chmod +x /run.sh

CMD ["/run.sh"]
