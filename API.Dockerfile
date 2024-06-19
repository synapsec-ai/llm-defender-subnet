from docker pull python:3.10.14-bookworm

# Copy required files
COPY llm_defender /var/run/llm-defender-subnet/llm_defender
COPY pyproject.toml /var/run/llm-defender-subnet

RUN /bin/bash -c "python3 -m venv /tmp/.venv && source /tmp/.venv/bin/activate && pip3 install -e /var/run/llm-defender-subnet/.[validator,api]