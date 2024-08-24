PYTHON = python3.12

build:
	$(PYTHON) -m build -n

install: build
	$(PYTHON) -m pip install --user --force-reinstall --break-system-packages dist/faustroll-*-py3-none-any.whl
