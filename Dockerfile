FROM python:3.8-alpine
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories \
    && apk update\
    && apk add --no-cache  py3-pandas py3-numpy \
    && apk add --no-cache --virtual .build-deps gcc musl-dev
ENV PYTHONPATH=/usr/lib/python3.8/site-packages
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt\
    && apk del .build-deps
WORKDIR /app
COPY . /app
CMD ["python3","/app/bot.py"]