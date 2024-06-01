# RSS Reader

Welcome to the RSS Reader repository! This project is a simple RSS feed reader application that allows users to aggregate and view updates from their favorite blogs and news sites.

## Table of Contents

- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Local Installation](#local-installation)
  - [Using Docker](#using-docker)
- [Usage](#usage)
- [Running Tests](#running-tests)
- [License](#license)

## Installation

You can install and run the RSS Reader either locally on your machine or using Docker. Follow the instructions below to get started.

### Prerequisites

Before you begin, ensure you have the following software installed on your machine:

- [Python 3.x](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installation/)
- [Docker](https://www.docker.com/get-started) (if you prefer to use Docker)
- [Postgres](https://www.postgresql.org/download/) (you can pick right version of postgres depending on your operating system)
- [Redis](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/) (you can pick right version of redis depending on your operating system)

### Local Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/shreyasp/rss-reader.git
   cd rss-reader
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

    To run the application update the config yaml located in `rss_reader/config/config.dev.yaml` to include the
    host, port, db_name, and password for the databsae, and host, port, db_number for redis

    If you're trying to run this project locally on MacOS, you will need to have an additional setting to be able to run redis queue
    successfully
    
    ```bash
    export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
    ```

   ```bash
   make run-dev # to start the application

   rq worker rss_reader.feeds.sync # to start the queue

   rqscheduler -H localhost -p 6379 -d 0 -v -i 5 # to start scheduler
   ```

5. **Access the application**

   The application should now be running on `http://localhost:8000`.

### Using Docker

1. **Clone the repository**

   ```bash
   git clone https://github.com/shreyasp/rss-reader.git
   cd rss-reader
   ```

2. **Build and run the Docker container using Docker Compose**

   ```bash
   docker-compose up --build
   ```

   This command will build the Docker image and start the application in a container.

3. **Access the application**

   The application should now be running on `http://localhost:8000`.

## Usage

Once the application is running, you can start adding RSS feeds to monitor. The application will periodically fetch and display the latest updates from the added feeds.

## Running Tests

To ensure the application is working correctly, you can run the tests using `pytest`. Follow the steps below to run the tests:

1. **Navigate to the project directory**

   ```bash
   cd rss-reader
   ```

2. **Run the tests using the Makefile**

   ```bash
   make test
   ```

   This command will use `pytest` to discover and run all the tests in the `test` directory.
