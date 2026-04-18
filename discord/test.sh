#!/bin/bash

docker build -f test.Containerfile -t test-discord .
docker run -it test-discord
