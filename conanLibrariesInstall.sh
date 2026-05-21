#!/bin/bash
python3 -m venv .venv
source ./.venv/bin/activate
pip install --upgrade pip
pip install conan
conan profile detect
conan install conan/ --build=missing --settings=build_type=Debug
conan install conan/ --build=missing --settings=build_type=Release