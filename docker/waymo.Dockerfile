# syntax=docker/dockerfile:1.7
FROM python:3.10-slim@sha256:cdbf8193cee2e31639ea8ea85ffdd8fa5cce98ee9abfde96ea5f329490048831

ARG PIP_VERSION=26.1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=2

WORKDIR /workspace

COPY requirements/waymo-linux.txt /tmp/waymo-linux.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade "pip==${PIP_VERSION}" \
    && pip install --default-timeout=1000 --retries=10 -r /tmp/waymo-linux.txt

COPY pyproject.toml README.md /workspace/
COPY src /workspace/src
RUN pip install --no-cache-dir -e .

CMD ["python", "-m", "driverx", "--help"]
