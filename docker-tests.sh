#!/bin/bash
DF=docker-compose-test.yml
docker-compose -f $DF up -d
docker-compose -f $DF run tests
docker-compose -f $DF kill