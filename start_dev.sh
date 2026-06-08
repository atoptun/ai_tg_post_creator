#!/bin/bash

docker compose -f compose.yml -f compose.dev.yml up --build --watch
