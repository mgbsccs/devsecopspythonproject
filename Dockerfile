FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 5002

ENV FLASK_ENV=production

CMD ["python", "show_blocked.py"]
