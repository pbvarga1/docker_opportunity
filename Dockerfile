FROM python:3.7

RUN mkdir -p /usr/src/app
RUN mkdir -p /usr/src/app/docs
RUN mkdir -p /usr/src/app/app
RUN mkdir -p /usr/src/app/web

COPY . /usr/src/app

WORKDIR /usr/src/app/docs

COPY docs/ /usr/src/app/docs
COPY app/ /usr/src/app/app
COPY web/ /usr/src/app/web

RUN pip install --no-cache-dir -e /usr/src/app/app
RUN pip install --no-cache-dir -e /usr/src/app/web
RUN pip install --no-cache-dir -r requirements.txt

RUN make html

FROM kyma/docker-nginx
COPY --from=0 /usr/src/app/docs/_build/html /var/www
CMD 'nginx'
