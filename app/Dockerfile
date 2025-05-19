FROM python:3.13.1-slim-bookworm

WORKDIR /app/

RUN python3 -m venv /opt/.venv

ENV PATH="/opt/.venv/bin:$PATH"

COPY . /app/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

ENV FLASK_APP=app.py

RUN flask db init
RUN flask db migrate -m "first_migration"
RUN flask db upgrade

CMD ["gunicorn","-b 0.0.0.0","app:create_app()"]