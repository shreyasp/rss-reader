FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./
RUN apt update
RUN apt install -y git

RUN pip install --no-cache-dir -r requirements.txt

ENV APP_MODE prod
CMD ["uvicorn", "rss_reader.main:app", "--host", "0.0.0.0", "--port", "8000"]
