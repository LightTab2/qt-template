#!/bin/bash
source ./venv/bin/activate
conan install conan/ --build=missing --settings=build_type=Debug
conan install conan/ --build=missing --settings=build_type=Release
