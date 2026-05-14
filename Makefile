SHELL := /bin/bash
SOURCES := $(notdir $(patsubst %/,%,$(wildcard sources/*/)))
UV := uv

.PHONY: help FORCE
.DEFAULT_GOAL := help

FORCE:

help:  ## Show this help
	@echo "Usage: make build-<source_id>"
	@echo ""
	@echo "Sources:"
	@printf '  %s\n' $(SOURCES)

build-%: FORCE
	$(UV) run corpus build $*
