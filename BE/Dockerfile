FROM python:3.13-slim AS build-stage

WORKDIR /install

COPY requirements_BE.txt .

RUN pip install --no-cache-dir -r requirements_BE.txt


FROM python:3.13-slim AS final-stage

WORKDIR /app

COPY --from=build-stage /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=build-stage /usr/local/bin/ /usr/local/bin/

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

COPY BE/ /app/BE

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

WORKDIR /app/BE

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]