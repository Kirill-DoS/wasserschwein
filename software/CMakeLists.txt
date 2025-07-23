cmake_minimum_required(VERSION 3.12)

# Подключаем Pico SDK (путь берется из переменной окружения)
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

# Название проекта (не влияет на имя выходного файла)
project(arcanoid)

# Инициализация SDK
pico_sdk_init()

# Создаем исполняемый файл из main.c и называем его "arcanoid_drive"
add_executable(arcanoid_drive drive.c)

# Подключаем стандартную библиотеку Pico
target_link_libraries(arcanoid_drive pico_stdlib hardware_pwm)
# Генерируем .uf2, .hex, .bin
pico_add_extra_outputs(arcanoid_drive)