FROM python:alpine

WORKDIR /app

# Gunicorn + Dependencies installieren
RUN pip install --no-cache-dir gunicorn

# App requirements installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY app.py .

# Environment Defaults
ENV MEDIA_ROOT=/media
ENV GLOBAL_COVER_PATH=/cover/global_cover.jpg
ENV PORT=8095

# Expose Port
EXPOSE 8095

# Gunicorn Start
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8095", "--workers=2", "--threads=2", "--log-level", "debug"]
