BLENDER_VERSION ?= 5.2
BLENDER_ADDON ?= io_scene_lwo
BLENDER ?= blender

default:
	@echo $(BLENDER_VERSION)
	$(MAKE) flake8
	$(MAKE) test

all: default

test:
	"$(BLENDER)" --background --factory-startup --python scripts/validate_blender52.py

# get:
# # 	python3 scripts.old/get_blender.py 3.6.21
# # 	python3 scripts.old/get_blender.py 3.5
# 	python3 scripts.old/get_blender.py 3.3
# # 	python3 scripts.old/get_blender.py 3.2
# # 	python3 scripts.old/get_blender.py 3.0
# # 	python3 scripts.old/get_blender.py 2.82

flake8:
	@flake8 $(BLENDER_ADDON) --count --show-source --statistics

lint:
	pyflakes io_scene_lwo
	ruff check io_scene_lwo

mypy:
	mypy io_scene_lwo

format:
	black io_scene_lwo

checks: format lint mypy

GIT_TAG?=2.0.0
GIT_TAGX:=$(shell echo "$(GIT_TAG)" | sed 's/\./, /g')
VERSION_FILE?=`find . -name version.py`
release:
	echo "Release v${GIT_TAG}"
# 	@grep -Po '\d\.\d\.\d' cocotbext/jtag/version.py
	git tag v${GIT_TAG} || { echo "make release GIT_TAG=${GIT_TAG}"; git tag ; exit 1; }
	sed -i '/^version/c\
version = "${GIT_TAG}"' io_scene_lwo/blender_manifest.toml
	sed -i '/\"version/c\
    "version": (${GIT_TAGX}),' io_scene_lwo/__init__.py
	sed -i '/\"blender/c\
    "blender": (5, 2, 0),' io_scene_lwo/__init__.py
	sed -i '/expect_version = (1/c\
    expect_version = (${GIT_TAGX})'  tests/basic/test_version.py
	git add io_scene_lwo/blender_manifest.toml io_scene_lwo/__init__.py tests/basic/test_version.py
	git commit --allow-empty -m "Update to version ${GIT_TAG}"
	git tag -f v${GIT_TAG}
	git push && git push --tags
# 	sed -i '/^version/c\
# version = "${GIT_TAG}"
# ' io_scene_lwo/blender_manifest.toml

xx:	
	sed -i '/^version/c\
version = "${GIT_TAG}"' io_scene_lwo/blender_manifest.toml
	sed -i '/\"version/c\
    "version": (${GIT_TAGX}),' io_scene_lwo/__init__.py
	sed -i '/\"blender/c\
    "blender": (5, 2, 0),' io_scene_lwo/__init__.py
	sed -i '/expect_version = (1/c\
    expect_version = (${GIT_TAGX})'  tests/basic/test_version.py
# 	sed -i 'expect_version//c\
#     expect_version = (${GIT_TAGX}),' tests/basic/test_version.py
