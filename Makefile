PYTHON ?= python

.PHONY: data-core data-geoai data-all data-check

data-core:
	$(PYTHON) scripts/download_external_data.py nepal-geid
	$(PYTHON) scripts/download_external_data.py nepal-shakemap
	$(PYTHON) scripts/download_external_data.py nepal-metadata
	$(PYTHON) scripts/download_external_data.py rc616
	$(PYTHON) scripts/download_rc616_shakemaps.py

data-geoai:
	$(PYTHON) scripts/download_external_data.py turkiye-context

data-all: data-core data-geoai

data-check:
	$(PYTHON) scripts/check_data.py
	$(PYTHON) scripts/inspect_external_data.py
