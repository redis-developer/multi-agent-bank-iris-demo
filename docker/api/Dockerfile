FROM python:3.12-slim

WORKDIR /app

COPY code/python/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Source is bind-mounted at runtime (see docker-compose.yml) so edits and
# ./solve take effect with uvicorn --reload / a container restart.
COPY code/python /app

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
