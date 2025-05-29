ARG basev=base

FROM ubuntu:noble AS clam_base

ENV DEBIAN_FRONTEND=noninteractiv

RUN apt-get update --fix-missing

RUN apt-get update
RUN apt-get install -y clamav \
    clamav-daemon \
    clamav-freshclam \
    cron \
    pipx

RUN touch /var/log/freshclam.log
RUN chmod 600 /var/log/freshclam.log
RUN chown clamav /var/log/freshclam.log

COPY clamav_config/freshclam.conf /etc/clamav/freshclam.conf
RUN chmod 0600 /etc/clamav/freshclam.conf
RUN chown clamav /etc/clamav/freshclam.conf

COPY clamav_config/clamd.conf /etc/clamav/clamd.conf
RUN chmod 0600 /etc/clamav/clamd.conf
RUN chown clamav /etc/clamav/clamd.conf

RUN mkdir /opt/clamav
COPY clamdb/bytecode.cvd /opt/clamav/bytecode.cvd
COPY clamdb/daily.cld /opt/clamav/daily.cld
COPY clamdb/main.cvd /opt/clamav/main.cvd
RUN chown -R clamav /opt/clamav/

RUN mkdir /var/run/clamav
RUN touch /var/run/clamav/clamd.ctl
RUN chown clamav /var/run/clamav/clamd.ctl

FROM clam_base AS clam_cron

COPY clamav_config/freshclam_cron /etc/cron.d/freshclam
RUN chmod 0500 /etc/cron.d/freshclam
RUN crontab /etc/cron.d/freshclam
RUN touch /var/log/cron.log
CMD cron

FROM clam_${basev} AS final

ENV PYTHONPATH=/app
ENV CLAMD_CONN=socket
ENV PATH=${PATH}:/root/.local/bin

EXPOSE 8080

RUN pipx install uv
RUN uv python install 3.9

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN mkdir /app

COPY --chown=clamav /scancan /app 
COPY --chown=clamav pyproject.toml /app
COPY --chown=clamav uv.lock /app
COPY --chown=clamav LICENSE /app
COPY --chown=clamav README.md /app
WORKDIR /app

RUN uv sync -p 3.9 --frozen

COPY --chown=clamav --chmod=0500 "./entrypoint.sh" "/entrypoint.sh"

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT [ "/entrypoint.sh" ]
