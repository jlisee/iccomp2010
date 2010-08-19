#! /bin/bash

protoc --proto_path=dep/ssl-vision/src/shared/proto --python_out=src/proto dep/ssl-vision/src/shared/proto/*.proto