FROM ubuntu:22.04

RUN apt-get update && apt-get install -y python3 python3-pip python3.10-venv

# Copy required files
COPY llm_defender /var/run/llm-defender-subnet/llm_defender
COPY pyproject.toml /var/run/llm-defender-subnet

RUN /bin/bash -c "python3 -m venv /tmp/.venv && source /tmp/.venv/bin/activate && pip3 install -e /var/run/llm-defender-subnet/.[validator]"