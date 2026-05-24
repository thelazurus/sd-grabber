FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY grabber/ grabber/

RUN mkdir -p data

EXPOSE 8001

CMD ["uvicorn", "grabber.main:app", "--host", "0.0.0.0", "--port", "8001"]
