EXECUTABLE=ip_seeker
TO_DELETE_FILES=.DS_Store $(EXECUTABLE).spec
TO_DELETE_FOLDERS=build

# Crossplatform specs
APP_NAME=$(MAIN_PROJ_NAME).exe
SEP='\'
MAKEDIR=md
DELETE_FOLDER=RD /S/Q
DELETE_FILE=DEL /F
COPY=copy
ARCHIVE=tar.exe -a -c -f
OPEN=start
OS=$(shell uname)

ifeq ($(OS), Linux)
	OPEN=xdg-open
	MAKEDIR=mkdir -p
	SEP=/
	DELETE_FOLDER=rm -rf
	DELETE_FILE=rm -f
	COPY=cp
	ARCHIVE=tar -cvf
	APP_NAME=$(MAIN_PROJ_NAME)
endif

ifeq ($(OS), Darwin)
	OPEN=open
	MAKEDIR=mkdir -p
	SEP=/
	DELETE_FOLDER=rm -rf
	DELETE_FILE=rm -f
	COPY=cp
	ARCHIVE=tar -cvf
	APP_NAME=$(MAIN_PROJ_NAME).app
endif

.PHONY: all install 

all: install

depedencies:
	pip3 install -r requirements.txt

install: uninstall clean depedencies
	python3 -m PyInstaller --noconfirm --onefile --console --name $(EXECUTABLE) ip_seeker.py

uninstall:
	$(DELETE_FOLDER) dist


clean:
	$(DELETE_FOLDER) $(TO_DELETE_FOLDERS)
	$(DELETE_FILE) $(TO_DELETE_FILES)
