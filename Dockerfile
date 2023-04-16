# syntax=docker/dockerfile:1

FROM python:3.11-slim-buster

RUN apt-get update && apt-get install -y git

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080
ENV PYTHONPATH=/app/
CMD ["python", "server/main.py"]
