FROM python:3.9.18

ENV DASH_DEBUG_MODE False
WORKDIR /app
COPY app/requirements.txt requirements.txt
ADD . /app
RUN set -ex && \
    pip install -r requirements.txt
EXPOSE 8050
RUN pip freeze
CMD ["gunicorn", "-b", "0.0.0.0:8050", "--reload", "index:server"]