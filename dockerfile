FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./
RUN apt update
RUN apt install -y git
RUN apt install -y supervisor

RUN mkdir -p /var/log/supervisor
COPY supervisor.docker.conf /etc/supervisor/conf.d/app.ini

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000/tcp
ENV APP_MODE docker
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/app.ini"]
