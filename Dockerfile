FROM python:3.10

RUN mkdir /app/

COPY . /app/

WORKDIR /app/

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

CMD ["bash", "/app/start.sh"]