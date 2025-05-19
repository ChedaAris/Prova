FROM python:3.13.1-slim-bookworm

WORKDIR /app/

RUN python3 -m venv /opt/.venv

ENV PATH="/opt/.venv/bin:$PATH"

COPY requirements.txt /app/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

COPY . /app/

RUN flask db init
RUN flask db migrate -m "first_migration"
RUN flask db upgrade

CMD ["gunicorn","-b 0.0.0.0","app:app"]