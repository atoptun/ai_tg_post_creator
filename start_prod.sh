#!/bin/bash

docker compose -f compose.yml -f compose.prod.yml up -d --build --scale celery_worker=4
