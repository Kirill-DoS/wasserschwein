cmake_minimum_required(VERSION 3.12)

# Подключаем Pico SDK (путь берется из переменной окружения)
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

# Название проекта (не влияет на имя выходного файла)
project(wasserschwein)

# Инициализация SDK
pico_sdk_init()

# Создаем исполняемый файл из main.c и называем его "arcanoid__main_file"
add_executable(arcanoid_main_file src/main.cpp src/arcanoid.cpp src/constants.h)

pico_enable_stdio_uart(arcanoid_main_file 0)
pico_enable_stdio_usb(arcanoid_main_file 1)

# Генерируем .uf2, .hex, .bin
pico_add_extra_outputs(arcanoid_main_file)

# Подключаем стандартную библиотеку Pico
target_link_libraries(arcanoid_main_file pico_stdlib hardware_uart hardware_pwm hardware_clocks)

pico_add_extra_outputs(arcanoid_main_file)