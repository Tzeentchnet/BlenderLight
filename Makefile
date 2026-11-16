PYTHON ?= python
BLENDER ?= blender
ADDON_DIR ?= io_scene_lwo
DIST_DIR ?= dist

.PHONY: all lint test package

all: lint test

test:
	"$(BLENDER)" --background --factory-startup --python scripts/validate_blender52.py

lint:
	$(PYTHON) -m flake8 $(ADDON_DIR) scripts/validate_blender52.py

package:
	"$(BLENDER)" --command extension build --source-dir $(ADDON_DIR) --output-dir $(DIST_DIR)
