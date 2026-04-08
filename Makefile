UV ?= uv

.PHONY: init sync run send show-config test build

init:
	$(UV) venv
	$(UV) sync

sync:
	$(UV) sync

run:
	$(UV) run tafeltennis run

send:
	$(UV) run tafeltennis send-now

show-config:
	$(UV) run tafeltennis show-config

test:
	$(UV) run python -m unittest discover -s tests -v

build:
	$(UV) build
