# Makefile для сборки проекта Raspberry Pi Pico
PROJECT_NAME = arcanoid_main_file
PICO_SDK_PATH = $(HOME)/pico/pico-sdk
BUILD_DIR = build

all:
	mkdir -p $(BUILD_DIR)
	cd $(BUILD_DIR) && cmake -DPICO_SDK_PATH=$(PICO_SDK_PATH) ..
	cd $(BUILD_DIR) && make -j4

fast:
	cd $(BUILD_DIR) && make -j4

clean:
	rm -rf $(BUILD_DIR)

deploy:
	cp $(BUILD_DIR)/$(PROJECT_NAME).uf2 /run/media/arch/RPI-RP2/

help:
	@echo "Доступные цели:"
	@echo "  make all    - Полная сборка"
	@echo "  make fast   - Быстрая пересборка"
	@echo "  make clean  - Очистка"
	@echo "  make deploy - Сборка и копирование"
	@echo "  make help   - Справка"