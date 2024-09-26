FROM python:3.12.6-slim-bookworm

RUN apt update && apt install -y build-essential libmemcached-dev zlib1g-dev

WORKDIR /srv

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD [ "gunicorn", "benchmark.wsgi:application", "-b", "0.0.0.0:8000", "--threads", "8" ]
