FROM python:3.7
RUN mkdir -p /usr/src/app/web
WORKDIR /usr/src/app/web

COPY . /usr/src/app/web

RUN pip install --no-cache-dir -e .

CMD ["python", "run_app.py"]
