FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update --fix-missing
RUN apt-get install -y software-properties-common

RUN add-apt-repository -y ppa:deadsnakes/ppa

RUN apt-get update
RUN apt install -y python3.9 \ 
    python3-pip \
    net-tools \
    dnsutils

RUN ln -sf /usr/bin/python3.9 /usr/bin/python3

RUN mkdir /app

COPY /src /app 
COPY pyproject.toml /app
COPY LICENSE /app

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:/app


RUN pip3 install poetry==1.1.5
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

EXPOSE 80
EXPOSE 4321

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]