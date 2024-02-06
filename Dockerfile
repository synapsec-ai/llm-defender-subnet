FROM ubuntu:22.04

RUN apt-get update && apt-get install -y python3 python3-pip libssl-dev python3.10-dev python3.10-venv

# Copy required files
COPY llm_defender .
COPY pyproject.toml .
COPY setup.cfg .
COPY setup.py .

RUN /bin/bash -c "python3 -m venv /tmp/.venv && source /tmp/.venv/bin/activate && pip3 install -e . && pip3 uninstall -y uvloop"