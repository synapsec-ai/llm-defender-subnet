FROM python:3.10.14-bookworm

ARG USER_UID=10001
ARG USER_GID=$USER_UID
ARG USERNAME=llm-defender-validator-user

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

# Copy required files
RUN mkdir -p /llm-defender-subnet && mkdir -p /home/$USERNAME/.bittensor && mkdir -p /home/$USERNAME/.llm-defender-subnet
COPY llm_defender /llm-defender-subnet/llm_defender
COPY pyproject.toml /llm-defender-subnet

# Setup permissions
RUN chown -R $USER_UID:$USER_GID /llm-defender-subnet \
&& chown -R $USER_UID:$USER_GID /home/$USERNAME/.bittensor \
&& chown -R $USER_ID:$USER_GID /home/$USERNAME \
&& chown -R $USER_ID:$USER_GID /home/$USERNAME/.llm-defender-subnet \
&& chmod -R 755 /home/$USERNAME \
&& chmod -R 755 /llm-defender-subnet \
&& chmod -R 755 /home/$USERNAME/.bittensor \
&& chmod -R 777 /home/$USERNAME/.llm-defender-subnet

# Change to the user and do subnet installation
USER $USERNAME

RUN /bin/bash -c "python3 -m venv /llm-defender-subnet/.venv && source /llm-defender-subnet/.venv/bin/activate && pip3 install -e /llm-defender-subnet/.[validator]"
