all: chromedriver venv build

chromedriver: bin/chromedriver

bin/chromedriver:
	wget --continue https://chromedriver.storage.googleapis.com/2.43/chromedriver_linux64.zip
	unzip chromedriver_linux64.zip -d bin/

venv:
	virtualenv venv --no-site-packages
	venv/bin/pip install -r requirements.txt

build: mfakeys.py
	venv/bin/pyinstaller --onefile --add-binary "bin/chromedriver:bin" mfakeys.py

clean:
	rm -rf bin/ build/ dist/ venv/ *.pyc *.spec *.zip
