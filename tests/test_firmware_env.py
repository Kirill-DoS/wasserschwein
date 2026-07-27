import tempfile
import unittest
from pathlib import Path

from tools.generate_firmware_env import generate_header


class FirmwareEnvTest(unittest.TestCase):
    # Проверяет, что шаблон .env содержит все обязательные для Pico настройки и создаёт C-заголовок.
    def test_template_generates_complete_header(self):
        root_dir = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as temporary_dir:
            header_path = Path(temporary_dir) / "generated_env.h"
            generate_header(root_dir / ".env.example", header_path)
            header = header_path.read_text(encoding="utf-8")

        self.assertIn("#define CFG_MOTOR_MAX_PWM 255", header)
        self.assertIn("#define CFG_PICO_COMMAND_TIMEOUT_MS 400", header)
        self.assertIn("#define CFG_PICO_SERVO_DIVIDER 125.0f", header)


if __name__ == "__main__":
    unittest.main()
