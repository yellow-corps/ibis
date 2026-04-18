#!/bin/sh

coverage run && coverage report && pylint . && black --check --diff .
