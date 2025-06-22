# Dockerfile to build a custom Airflow image with Google Chrome and Chromedriver

# Start from the official Airflow image
FROM apache/airflow:2.7.3

# Switch to root user to install packages
USER root

# Install Google Chrome, its dependencies, and other tools like jq and unzip
RUN apt-get update \
    && apt-get install -y wget gnupg jq unzip \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Download and install Chromedriver for the STABLE version of Chrome
RUN CHROME_DRIVER_URL=$(wget -q -O - "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url') \
    && wget --no-verbose -O /tmp/chromedriver.zip "$CHROME_DRIVER_URL" \
    && unzip /tmp/chromedriver.zip -d /usr/bin \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/bin/chromedriver-linux64/chromedriver

# Create a symlink to chromedriver
RUN ln -s /usr/bin/chromedriver-linux64/chromedriver /usr/bin/chromedriver

# Switch back to the airflow user
USER airflow

# Copy the requirements file and install dependencies
COPY requirements.txt /opt/airflow/
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt 