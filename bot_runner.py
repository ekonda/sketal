import subprocess
import logging
import signal
import os

"""
File for keeping bot running. If bot dies - it will be restarted.
Keep in mind, that not all logs will be shown in bot_runner's terminal.
"""

if __name__ == "__main__":
    cmd = "python3.6 -u bot.py"
    p = None

    try:
        while True:
            logging.info(f"Running programm (\"{cmd}\").")

            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)

            for line in p.stdout:
                logging.info(str(line, "utf8").rstrip())

            try:
                os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except Exception:
                import traceback
                traceback.print_exc()

            logging.info("Programm died.")

    except (KeyboardInterrupt, SystemExit):
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)

        except Exception:
            import traceback
            traceback.print_exc()

        logging.info("Turning runner off...")
