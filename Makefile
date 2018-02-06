python36 = command -v python3.6
python3 = command -v python3

pythonrun = ""

ifeq (python36, '')
	ifeq (python3, '')
		pythonrun = "python"
	else
		pythonrun = "python3"
	endif
else
	pythonrun = "python3.6"
endif

all:
	$(pythonrun) bot.py

test:
	$(pythonrun) tests/tests.py

clean:
	find . -name "*.pyc" -type f -delete
	find . -name "__pycache__" -type d -delete
	-rm "tempcaptcha.png"
	-rm "logs.txt"
	-rm "log.txt"
