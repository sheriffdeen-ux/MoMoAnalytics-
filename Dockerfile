# Dockerfile for MoMo Analytics Ghana
# This file creates a self-contained, reproducible environment for deployment.

# Use a standard Debian image as the base
FROM debian:bookworm-slim

# Set environment variables to prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Set up a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /home/appuser/app

# 1. Install System Dependencies required to build Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    curl \
    llvm \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libffi-dev \
    liblzma-dev \
    ca-certificates \
    git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 2. Install mise
# We run this as the appuser
USER appuser
RUN curl https://mise.run | sh

# 3. Install Python using mise
# This ensures the correct Python version is built from source if needed
ENV PATH="/home/appuser/.local/bin:${PATH}"
RUN mise install python@3.11.0
RUN mise use --global python@3.11.0

# 4. Copy application code and install Python dependencies
COPY --chown=appuser:appuser . .
RUN mise exec python@3.11.0 -- pip install --no-cache-dir -r requirements.txt

# 5. Expose the port the app runs on and define the run command
EXPOSE 8080
CMD ["/home/appuser/.local/share/mise/installs/python/3.11.0/bin/gunicorn", "--bind", "0.0.0.0:8080", "final_system:app"]
