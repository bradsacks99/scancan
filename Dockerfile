ARG basev=base

FROM ubuntu:jammy AS clam_base

ENV DEBIAN_FRONTEND noninteractiv

RUN apt-get update --fix-missing

RUN apt-get update
RUN apt-get install -y clamav \
    clamav-daemon \
    clamav-freshclam \
    cron

RUN touch /var/log/freshclam.log
RUN chmod 600 /var/log/freshclam.log
RUN chown clamav /var/log/freshclam.log

COPY clamav_config/freshclam.conf /etc/clamav/freshclam.conf
RUN chmod 0600 /etc/clamav/freshclam.conf
RUN chown clamav /etc/clamav/freshclam.conf

COPY clamav_config/clamd.conf /etc/clamav/clamd.conf
RUN chmod 0600 /etc/clamav/clamd.conf
RUN chown clamav /etc/clamav/clamd.conf

FROM clam_base AS clam_cron

RUN mkdir /opt/clamav
COPY clamdb/bytecode.cvd /opt/clamav/bytecode.cvd
COPY clamdb/daily.cvd /opt/clamav/daily.cvd
COPY clamdb/main.cvd /opt/clamav/main.cvd
RUN chown -R clamav /opt/clamav/

COPY clamav_config/freshclam_cron /etc/cron.d/freshclam
RUN chmod 0500 /etc/cron.d/freshclam
RUN crontab /etc/cron.d/freshclam
RUN touch /var/log/cron.log
CMD cron

FROM clam_${basev} AS final

RUN apt-get install -y software-properties-common

RUN add-apt-repository -y ppa:deadsnakes/ppa

RUN apt-get update
RUN apt-get install -y python3.10 \
    python3-pip

RUN mkdir /app

COPY /scancan /app 
COPY pyproject.toml /app
COPY LICENSE /app

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:/app
ENV CLAMD_CONN=socket

RUN pip3 install poetry==1.7.1
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

EXPOSE 8080

COPY "./entrypoint.sh" "/entrypoint.sh"
RUN chmod 0500 /entrypoint.sh
RUN chown clamav /entrypoint.sh

USER clamav

ENTRYPOINT [ "/entrypoint.sh" ]
