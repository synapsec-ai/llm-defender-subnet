from python:3.10.14-bookworm

ARG USER_UID=10001
ARG USER_GID=$USER_UID
ARG USERNAME=llm-defender-api-user

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

# Copy required files
RUN mkdir -p /llm-defender-subnet && mkdir -p /.bittensor
COPY llm_defender /llm-defender-subnet/llm_defender
COPY pyproject.toml /llm-defender-subnet

# Setup permissions
RUN chown -R $USER_UID:$USER_GID /llm-defender-subnet/ && chown -R $USER_UID:$USER_GID /.bittensor && chmod -R 755 /llm-defender-subnet && chmod -R 755 /.bittensor

USER $USERNAME

RUN /bin/bash -c "python3 -m venv /llm-defender-subnet/.venv && source /llm-defender-subnet/.venv/bin/activate && pip3 install -e /llm-defender-subnet/.[validator]"
