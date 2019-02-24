FROM python:2
MAINTAINER Dmitriy Kargapolov <dmitriy.kargapolov@idt.net>

RUN apt-get update && apt-get install -y --no-install-recommends \
    stoken \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
 && curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && echo "deb https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update && apt-get install -y --no-install-recommends \
    google-chrome-stable \
    fontconfig \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-symbola \
    fonts-noto \
    ttf-freefont \
 && apt-get purge --auto-remove -y curl gnupg \
 && rm -rf /var/lib/apt/lists/*

ARG USER
ARG HOME
ARG USERADD

RUN /bin/sh -c "$USERADD"

USER $USER
ENV USER $USER
ENV HOME $HOME
WORKDIR $HOME

COPY requirements.txt .

RUN pip install virtualenv
RUN virtualenv venv --no-site-packages
RUN venv/bin/pip install -r requirements.txt

RUN wget -cO d.zip \
    https://chromedriver.storage.googleapis.com/72.0.3626.69/chromedriver_linux64.zip \
 && unzip d -d bin/ && rm -f d.zip

COPY mfakeys.py .
RUN venv/bin/pyinstaller --onefile --add-binary "bin/chromedriver:bin" mfakeys.py
ENV PATH=$PATH:$HOME/dist
ENTRYPOINT []
CMD ["bash"]
