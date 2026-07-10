# qt6-template developer entrypoint. Thin wrapper over cmake / conan / ctest / doxygen.
BUILD_DIR   ?= build
BUILD_TYPE  ?= Release
TOOLCHAIN   ?= conan/conan_toolchain.cmake
GENERATOR   ?= Ninja
JOBS        ?= 4
QPA         ?= offscreen

.DEFAULT_GOAL := help
.PHONY: help conan configure build run test docs docs-serve docs-clean format tidy clean

help:  ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n",$$1,$$2}'

conan:  ## Install dependencies with Conan (Debug + Release)
	conan install conan/ --build=missing --settings=build_type=Debug
	conan install conan/ --build=missing --settings=build_type=Release

configure:  ## Configure the CMake build (uses the Conan toolchain)
	@test -f $(TOOLCHAIN) || { echo "error: conan toolchain not found at $(TOOLCHAIN); run 'make conan' first" >&2; exit 1; }
	cmake . -G $(GENERATOR) -B $(BUILD_DIR) -DCMAKE_TOOLCHAIN_FILE=$(TOOLCHAIN) -DCMAKE_BUILD_TYPE=$(BUILD_TYPE)

build: configure  ## Build the project
	cmake --build $(BUILD_DIR) --config $(BUILD_TYPE) -j$(JOBS)

run: build  ## Build then run the executable
	./$(BUILD_DIR)/qt6-template

test: build  ## Run the test suite headless (QT_QPA_PLATFORM=offscreen)
	cd $(BUILD_DIR) && QT_QPA_PLATFORM=$(QPA) ctest -C $(BUILD_TYPE) -VV

docs:  ## Build the Doxygen documentation (docs/html)
	bash scripts/run_doxygen.sh

docs-serve: docs  ## Build docs then serve them on http://localhost:8000
	bash scripts/serve_doxygen.sh

docs-clean:  ## Remove generated docs
	rm -rf docs

format:  ## Format sources in place with clang-format
	@find src test -name '*.cpp' -o -name '*.h' | xargs clang-format -i

tidy:  ## Run clang-tidy over sources (needs a configured build)
	@find src -name '*.cpp' | xargs clang-tidy -p $(BUILD_DIR) --config-file=.clang-tidy

clean:  ## Remove build directories
	rm -rf $(BUILD_DIR) build-debug build-rwdi build-ubsan build-cov
