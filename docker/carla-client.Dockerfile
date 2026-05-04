FROM python:3.10-bullseye

ARG CARLA_PYTHON_VERSION=0.9.16

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /workspace

RUN python -m pip install --default-timeout=1000 --retries=10 \
    "carla==${CARLA_PYTHON_VERSION}"

CMD ["python", "-c", "import carla; from importlib.metadata import version; print(version('carla'))"]
