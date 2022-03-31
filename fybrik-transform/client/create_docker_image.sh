#!/bin/sh

docker build --tag demo_client:latest .
kind load docker-image demo_client:latest
kubectl run my-shell --rm -i --tty --image demo_client:latest --image-pull-policy=IfNotPresent -- bash
