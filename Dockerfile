FROM ubuntu:noble AS clam_base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update --fix-missing && \
    apt-get install -y clamav clamav-daemon clamav-freshclam cron pipx && \
    rm -rf /var/lib/apt/lists/*

RUN touch /var/log/freshclam.log
RUN chmod 600 /var/log/freshclam.log
RUN chown clamav /var/log/freshclam.log

COPY clamav_config/freshclam.conf clamav_config/clamd.conf /etc/clamav/
RUN chmod 0600 /etc/clamav/freshclam.conf /etc/clamav/clamd.conf && \
    chown clamav /etc/clamav/freshclam.conf /etc/clamav/clamd.conf

RUN mkdir /opt/clamav
COPY clamdb/bytecode.cvd /opt/clamav/bytecode.cvd
COPY clamdb/daily.cvd /opt/clamav/daily.cvd
COPY clamdb/main.cvd /opt/clamav/main.cvd
RUN chown -R clamav /opt/clamav/

RUN mkdir /var/run/clamav
RUN touch /var/run/clamav/clamd.ctl
RUN chown clamav /var/run/clamav/clamd.ctl
