
FROM python:3.8-slim-buster

# Install FFmpeg
RUN apt update && apt install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN mkdir /app
WORKDIR /app

# Create the data directory
RUN mkdir /app/data

ENV FLASK_APP run.py

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Copy projejct directory in workdir (/app)
COPY . .

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]