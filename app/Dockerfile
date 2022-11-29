FROM python:3.9.5




ENV DASH_DEBUG_MODE False
WORKDIR /app
COPY requirements.txt requirements.txt
ADD . /app
RUN set -ex && \
    pip install -r requirements.txt
EXPOSE 8050
CMD ["gunicorn", "-b", "0.0.0.0:8050", "--reload", "index:server"]