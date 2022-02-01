FROM python:3.9.5-slim-buster

COPY . /app
WORKDIR /app

RUN apt-get update && pip install --upgrade pip && \
	apt-get -y install libpq-dev gcc && \
	pip install psycopg2 && pip install -r requirements.txt


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /app/requirements.txt

CMD ["chmod","+775","starter.sh"]
CMD ["./starter.sh"]