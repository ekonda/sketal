import subprocess
import logging

"""
File for keeping bot running. If bot dies - it will be restarted.
Keep in mind, that not all logs will be shown in bot_runner's terminal.
"""

if __name__ == "__main__":
    cmd = "python3.6 -u bot.py"

    try:
        while True:
            logging.info(f"Запуск программы (\"{cmd}\")")

            subprocess.run(cmd, shell=True)

    except (KeyboardInterrupt, SystemExit):
        logging.info(f"Завершение программы (\"{cmd}\")...")
