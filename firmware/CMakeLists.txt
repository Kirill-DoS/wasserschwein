cmake_minimum_required(VERSION 3.12)

# Путь передаёт Makefile из корневого .env; отдельные скрытые настройки не используются.
if(NOT DEFINED PICO_SDK_PATH OR PICO_SDK_PATH STREQUAL "")
    message(FATAL_ERROR "Не задан PICO_SDK_PATH. Укажите путь к Pico SDK в корневом .env.")
endif()
include("${PICO_SDK_PATH}/external/pico_sdk_import.cmake")
# Название проекта (не влияет на имя выходного файла)
project(wasserschwein)

set(CMAKE_C_STANDARD 11)

# Создаём заголовок с настройками Pico из единого корневого .env перед компиляцией.
find_package(Python3 COMPONENTS Interpreter REQUIRED)
set(WASSERSCHWEIN_ENV_FILE "${CMAKE_CURRENT_SOURCE_DIR}/../.env")
set(WASSERSCHWEIN_GENERATED_DIR "${CMAKE_CURRENT_BINARY_DIR}/generated")
set(WASSERSCHWEIN_GENERATED_HEADER "${WASSERSCHWEIN_GENERATED_DIR}/generated_env.h")
if(NOT EXISTS "${WASSERSCHWEIN_ENV_FILE}")
    message(FATAL_ERROR "Не найден .env. Скопируйте ../.env.example в ../.env и заполните настройки.")
endif()
file(MAKE_DIRECTORY "${WASSERSCHWEIN_GENERATED_DIR}")
add_custom_command(
    OUTPUT "${WASSERSCHWEIN_GENERATED_HEADER}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${WASSERSCHWEIN_GENERATED_DIR}"
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../tools/generate_firmware_env.py"
            --env "${WASSERSCHWEIN_ENV_FILE}" --output "${WASSERSCHWEIN_GENERATED_HEADER}"
    DEPENDS "${WASSERSCHWEIN_ENV_FILE}" "${CMAKE_CURRENT_SOURCE_DIR}/../tools/generate_firmware_env.py"
    COMMENT "Создание настроек Pico из .env"
    VERBATIM
)
add_custom_target(generate_pico_env DEPENDS "${WASSERSCHWEIN_GENERATED_HEADER}")

# Инициализация SDK
pico_sdk_init()

# Создаем исполняемый файл из main.c и называем его "arcanoid__main_file"
add_executable(arcanoid_main_file
    src/main.c
    src/arcanoid.c
    src/uart.c
)
add_dependencies(arcanoid_main_file generate_pico_env)

pico_enable_stdio_uart(arcanoid_main_file 1)
pico_enable_stdio_usb(arcanoid_main_file 1)

# Подключаем стандартную библиотеку Pico
target_link_libraries(arcanoid_main_file
    pico_stdlib
    hardware_uart
    hardware_pwm
    hardware_clocks
    hardware_adc
)

target_include_directories(arcanoid_main_file PRIVATE "${WASSERSCHWEIN_GENERATED_DIR}")

# Генерируем .uf2, .hex, .bin
pico_add_extra_outputs(arcanoid_main_file)
#
