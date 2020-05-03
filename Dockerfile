FROM python:alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod -R 777 /usr/src/app

EXPOSE $PORT

CMD [ "python", "./server.py" ]