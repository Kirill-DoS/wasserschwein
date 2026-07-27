FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-ml.txt requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements-ml.txt

COPY . .

# Контейнер предназначен для проверки GPU и экспериментов YOLO, а не для доступа к камере/HC-06.
CMD ["python3", "check_gpu.py"]
