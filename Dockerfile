FROM python:3.11-slim

# libglib can cho opencv-python-headless doc/ghi anh dung dinh dang
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY frontend frontend

WORKDIR /app/backend
EXPOSE 7860

# Hugging Face Spaces (Docker SDK) mac dinh doi app lang nghe port 7860.
# Render/Railway... truyen cong qua bien moi truong PORT - neu co PORT thi uu tien dung PORT.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
