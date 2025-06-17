# Python 3.11 with pip pre-installed
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Ensure pip is up to date and available in PATH
RUN python -m pip install --upgrade pip

# Set the default user
USER $USERNAME

# Set working directory
WORKDIR /workspaces/sql-join-relationship-analysis

# Make sure pip is available for the vscode user
RUN python -m pip install --user --upgrade pip

# Verify installations
RUN python --version && pip --version