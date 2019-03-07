FROM node

RUN mkdir -p /usr/src/app/
WORKDIR /usr/src/app/

COPY web/package.json .
COPY web/yarn.lock .

RUN yarn install

FROM python:3.7
RUN mkdir -p /usr/src/app/web

COPY . /usr/src/app/web

WORKDIR /usr/src/app/web/

RUN pip install --no-cache-dir -e .

COPY --from=0 /usr/src/app/node_modules /usr/src/app/web/web/static

CMD ["python", "run_app.py"]
