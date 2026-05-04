FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py migrate.py ./

CMD python migrate.py --db-host database --db-user taskuser --db-password taskpass --db-name task_tracker && \
    python app.py --db-host database --db-user taskuser --db-password taskpass --db-name task_tracker --port 5000 --host 0.0.0.0