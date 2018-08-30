#!/bin/sh

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

basepath=$(cd `dirname $0`; pwd)
echo "Doing AB-like POST testing"
echo "command: ../pywb/main.py -p packets/requestbody2kb.json  -c 20 -t 5 10.0.1.43:18080"
../pywb/main.py -p packets/requestbody2kb.json  -c 20 -t 5 10.0.1.43:18080
