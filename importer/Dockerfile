## Base ##

FROM ubuntu:22.04 AS base

ARG DEBIAN_FRONTEND="noninteractive"

RUN apt-get update && \
    apt-get install --no-install-recommends -y python3 python3-pip python3-venv wget && \
    apt-get install --no-install-recommends -y postgresql-client && \
    apt-get clean &&  \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv

##  Runner ##

FROM base AS runner

ARG DEBIAN_FRONTEND="noninteractive"

ENV WECONNECT_USER=
ENV WECONNECT_PASSWORD=
ENV WECONNECT_INTERVAL=180
ENV DB_HOSTNAME=db
ENV DB_PORT=5432
ENV DB_USERNAME=kmstr_appl
ENV DB_PASSWORD=secure
ENV DB_SCHEMA=kmstr
ENV TIMEZONE=Europe/Zurich

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# WORKDIR /importer

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    kmstruser

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python3 -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.
USER kmstruser

WORKDIR /importer
# Copy the source code into the container.
COPY importer .

# Run the application.
CMD python3 __main__.py --username=${WECONNECT_USER} --password=${WECONNECT_PASSWORD} --interval=${WECONNECT_INTERVAL} \
    --db-hostname=${DB_HOSTNAME} --db-port=${DB_PORT} --db-username=${DB_USERNAME} --db-password=${DB_PASSWORD} \
    --db-name=${DB_NAME} --timezone=${TIMEZONE}

