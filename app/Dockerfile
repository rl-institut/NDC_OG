FROM python:3.9.18

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENV DASH_DEBUG_MODE False
WORKDIR /app
COPY app/requirements.txt requirements.txt
ADD app/ /app
RUN set -ex && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
EXPOSE 8050
RUN pip freeze
CMD ["gunicorn", "-b", "0.0.0.0:8050", "index:server"]