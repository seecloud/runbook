FROM ubuntu:16.04
MAINTAINER Kirill Zaitsev <k.zaitsev@me.com>

RUN apt-get update && apt-get install --yes wget git-core python-dev build-essential

# ubuntu's pip is too old to work with the version of requests we
# require, so get pip with get-pip.py
RUN wget https://bootstrap.pypa.io/get-pip.py && \
  python get-pip.py && \
  rm -f get-pip.py

COPY . /app
WORKDIR /app

RUN python setup.py install
RUN pip install -r requirements.txt

WORKDIR /app/runbook
EXPOSE 5000

ENTRYPOINT ["bash"]
CMD ["main.sh"]
