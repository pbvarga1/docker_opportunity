FROM python:3.7
RUN mkdir -p /usr/src/app
RUN mkdir -p /usr/src/app/app
WORKDIR /usr/src/app/app

COPY . /usr/src/app/app

RUN pip install --no-cache-dir -e .

CMD ["python", "run_app.py"]
