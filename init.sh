#!/bin/bash

# Instalação do Chrome Driver
apt-get update && \
apt-get install -y gnupg wget curl unzip --no-install-recommends && \
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
apt-get update -y && \
apt-get install -y google-chrome-stable && \
CHROMEVER=$(google-chrome --product-version | grep -o "[^\.]*\.[^\.]*\.[^\.]*") && \
DRIVERVER=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROMEVER") && \
wget -q --continue -P /chromedriver "http://chromedriver.storage.googleapis.com/$DRIVERVER/chromedriver_linux64.zip" && \
unzip /chromedriver/chromedriver* -d /usr/local/bin/ && \
chmod +x /usr/local/bin/chromedriver && \
rm -rf /chromedriver

# Execução do seu script Python
python main.py
