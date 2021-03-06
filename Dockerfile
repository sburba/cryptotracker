FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

WORKDIR /app/

RUN curl -sSL -o /usr/bin/wait-for-it \
    https://raw.githubusercontent.com/vishnubob/wait-for-it/c096cface5fbd9f2d6b037391dfecae6fde1362e/wait-for-it.sh \
    && chmod +x /usr/bin/wait-for-it

# Install Poetry
# TODO: In a real app we would want to pin the poetry version to avoid breaking changes
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock /app/

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --no-dev ; fi"

COPY . /app
ENV PYTHONPATH=/app