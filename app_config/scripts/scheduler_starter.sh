#!/bin/bash

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
    HOST=cache
    ;;
  "local")
    DIR=/Users/shreyaspatil/rss_reader
    HOST=localhost
    ;;
esac
VENV=$DIR/.venv/bin/activate

cd $DIR
source $VENV

exec rqscheduler -H ${HOST} -p 6379 -d 0 -v -i 5