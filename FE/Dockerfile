FROM python:3.13-slim as builder
WORKDIR /install

COPY requirements_FE.txt .
RUN pip install --no-cache-dir -r requirements_FE.txt



FROM python:3.13-slim AS final

WORKDIR /app


COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY FE/ /app/FE

EXPOSE 8501

WORKDIR /app/FE

# Lệnh khởi động Streamlit
CMD ["streamlit", "run", "Overview.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
