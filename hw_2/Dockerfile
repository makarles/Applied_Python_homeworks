FROM python:3.13

WORKDIR /app

ENV PYTHONPATH=/app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot/bot.py"]
