FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu20.04

# Устанавливаем Python 3.11 и системные зависимости для OpenCV
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl-dev \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/python3.11 /usr/bin/python

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
# Устанавливаем torch с CUDA 11.8
RUN pip install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu118
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "cheks.py"]