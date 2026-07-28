import argparse
from pathlib import Path


# Читает простые пары KEY=VALUE из .env, не требуя NumPy или других библиотек компьютерного зрения.
def load_env_file(env_path):
    values = {}
    with Path(env_path).open("r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", maxsplit=1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


# Превращает число из .env в безопасный литерал C без возможности вставить произвольный код.
def c_number(value, key, is_float=False):
    try:
        number = float(value) if is_float else int(value)
    except ValueError as error:
        raise ValueError(f"{key} в .env должен быть числом") from error
    return f"{number}f" if is_float else str(number)


# Создаёт заголовок C с настройками Pico, который подключается только во время сборки прошивки.
def generate_header(env_path, output_path):
    values = load_env_file(env_path)
    integer_keys = (
        "MOTOR_MAX_PWM",
        "PICO_MOTOR_WRAP",
        "PICO_MOTOR_FREQ_HZ",
        "PICO_SERVO_WRAP",
        "PICO_ESC_MIN_PULSE",
        "PICO_ESC_MAX_PULSE",
        "PICO_ESC1_TARGET_PULSE",
        "PICO_ESC2_TARGET_PULSE",
        "PICO_COMMAND_TIMEOUT_MS",
        "PICO_CALIBRATE_ESC_ON_BOOT",
        "PICO_UART_BAUDRATE",
        "PICO_PIN_TX",
        "PICO_PIN_RX",
        "PICO_PIN_LED",
        "PICO_PIN_BUTTON",
        "PICO_PIN_SERVO1",
        "PICO_PIN_SERVO2",
        "PICO_PIN_MOTOR_LEFT",
        "PICO_PIN_MOTOR_RIGHT",
        "PICO_PIN_BATTERY",
    )
    float_keys = ("PICO_SERVO_DIVIDER",)
    missing = [key for key in (*integer_keys, *float_keys) if key not in values]
    if missing:
        raise KeyError("В .env отсутствуют настройки Pico: " + ", ".join(missing))

    lines = ["#ifndef GENERATED_ENV_H", "#define GENERATED_ENV_H", ""]
    for key in integer_keys:
        lines.append(f"#define CFG_{key} {c_number(values[key], key)}")
    for key in float_keys:
        lines.append(f"#define CFG_{key} {c_number(values[key], key, is_float=True)}")
    lines.extend(["", "#endif"])

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


# Принимает пути к .env и создаваемому заголовку для CMake.
def main():
    parser = argparse.ArgumentParser(description="Генерация заголовка Pico из корневого .env")
    parser.add_argument("--env", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    generate_header(args.env, args.output)


if __name__ == "__main__":
    main()
