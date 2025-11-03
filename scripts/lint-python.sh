#!/usr/bin/env bash

set -e
set -x

mypy .
ruff check .
ruff format . --check

