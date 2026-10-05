PYTHON ?= python

.PHONY: data-core data-docs data-geoai data-all data-check turkiye-ingest turkiye-eda test

data-docs:
	$(PYTHON) scripts/download_external_data.py nepal-docs

data-core:
	$(PYTHON) scripts/download_turkiye.py
	$(PYTHON) scripts/download_external_data.py nepal-geid
	$(PYTHON) scripts/download_external_data.py nepal-shakemap
	$(PYTHON) scripts/download_external_data.py nepal-docs
	$(PYTHON) scripts/download_external_data.py rc616
	$(PYTHON) scripts/download_rc616_shakemaps.py

data-geoai:
	$(PYTHON) scripts/download_external_data.py turkiye-context

data-all: data-core data-geoai

data-check:
	$(PYTHON) scripts/check_data.py
	$(PYTHON) scripts/inspect_turkiye.py
	$(PYTHON) scripts/inspect_external_data.py

turkiye-ingest:
	$(PYTHON) -m src.data.turkiye

turkiye-eda: turkiye-ingest
	$(PYTHON) -m src.data.turkiye_eda

test:
	$(PYTHON) -m pytest -q
