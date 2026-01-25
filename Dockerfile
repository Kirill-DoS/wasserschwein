# FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# # Устанавливаем системные зависимости
# RUN apt-get update && apt-get install -y \
#     python3.10 \
#     python3-pip \
#     python3.10-venv \
#     libgl1-mesa-glx \
#     libglib2.0-0 \
#     wget \
#     git \
#     && rm -rf /var/lib/apt/lists/*

# # Устанавливаем рабочую директорию
# WORKDIR /app

# # Копируем файлы проекта
# COPY requirements.txt .
# COPY app.py .

# # Устанавливаем Python зависимости
# RUN pip3 install -r requirements.txt

# # Создаем папки для входных/выходных данных
# RUN mkdir -p /app/input /app/output

# # Команда по умолчанию
# CMD ["python3", "app.py"]

FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Копируем все файлы
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir ultralytics opencv-python-headless torch torchvision

CMD ["python", "app.py"]