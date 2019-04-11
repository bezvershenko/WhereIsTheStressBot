FROM python:3-onbuild

WORKDIR /app
COPY . /app
RUN mkdir /app/db

RUN pip install -r requirements.txt

CMD [ "python3", "bot.py" ]
