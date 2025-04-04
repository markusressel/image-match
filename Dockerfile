FROM python:3.10

ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION="2.1.2"
ENV PIP_DISABLE_PIP_VERSION_CHECK=on

RUN apt-get update && apt-get install -y libblas-dev liblapack-dev gfortran

RUN pip install --upgrade pip
RUN pip install numpy scipy

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY image_match ./image_match
COPY poetry.lock pyproject.toml README.md ./


RUN pip install "poetry==$POETRY_VERSION" \
 && POETRY_VIRTUALENVS_CREATE=false poetry install \
 && pip uninstall -y poetry \
