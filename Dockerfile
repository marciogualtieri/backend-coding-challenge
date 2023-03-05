FROM python:3.10-slim

# Install OS requirements
RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ \
    curl \
    binutils libproj-dev gdal-bin \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y

# Install Poetry
ENV POETRY_HOME=/usr/local
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV USER gistapi
ENV GROUP gistapi

RUN groupadd $USER
RUN useradd -ms /bin/bash -g $GROUP $USER
USER $USER

USER $USER
WORKDIR /home/$USER/application

COPY . .

# Install Python requirements
USER $USER
RUN poetry config virtualenvs.in-project true
RUN poetry install

# Start the app
CMD poetry run honcho start --no-prefix --no-prefix "${PROCESS:-service}"