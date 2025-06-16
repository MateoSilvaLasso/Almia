FROM selenium/standalone-chrome:latest

WORKDIR /app
COPY . .

# Asegúrate de que tienes chromedriver en PATH
ENV PATH=$PATH:/usr/local/bin

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "10000"]
