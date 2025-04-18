FROM python:3.13-rc-slim

ARG PORT=8050

WORKDIR /app

COPY . .

RUN pip install -e .

EXPOSE ${PORT}

CMD ["python", "src/main.py"]