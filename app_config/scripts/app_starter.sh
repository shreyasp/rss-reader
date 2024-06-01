#!/bin/bash

# check if env is set
NAME=rss_reader
if [ -z "$APP_ENV" ]; then
  echo "needs to set environment var 'APP_ENV'"
  exit 1
fi

# if set the pick appropriate directory
DIR=""
case ${APP_ENV} in
  "docker")
    DIR=/app
    ;;
  "local")
    DIR=/Users/shreyaspatil/rss_reader
    ;;
esac

# bootstrap the application
VENV=$DIR/.venv/bin/activate
LOG_LEVEL=error

cd $DIR
source $VENV

# run migrations
alembic upgrade head

# start the application
exec uvicorn \
  rss_reader.main:app \
  --host 0.0.0.0 \
  --port 8000