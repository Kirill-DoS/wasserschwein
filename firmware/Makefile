# Makefile для сборки проекта Raspberry Pi Pico
PROJECT_NAME = arcanoid_main_file
ENV_FILE = ../.env

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
endif

ifeq ($(strip $(PICO_SDK_PATH)),)
$(error Не найден PICO_SDK_PATH. Скопируйте .env.example в .env и укажите путь к Pico SDK)
endif

ifeq ($(strip $(PICO_MOUNT_POINT)),)
$(error Не найден PICO_MOUNT_POINT. Укажите точку монтирования Pico в .env)
endif

BUILD_DIR = build
all:
	mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake "-DPICO_SDK_PATH=$(PICO_SDK_PATH)" ..
	cd $(BUILD_DIR) && make -j4

fast:
	cd $(BUILD_DIR) && make -j4

clean:
	rm -rf $(BUILD_DIR)

deploy:
	@test -f $(BUILD_DIR)/$(PROJECT_NAME).uf2 || (echo "Сначала выполните make all" && false)
	cp $(BUILD_DIR)/$(PROJECT_NAME).uf2 $(PICO_MOUNT_POINT)/
	sync

help:
	@echo "Доступные цели:"
	@echo "  make all    - Полная сборка"
	@echo "  make fast   - Быстрая пересборка"
	@echo "  make clean  - Очистка"
	@echo "  make deploy - Сборка и копирование"
	@echo "  make help   - Справка"
