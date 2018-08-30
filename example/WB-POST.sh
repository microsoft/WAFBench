#!/bin/sh

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

basepath=$(cd `dirname $0`; pwd)
echo "Doing AB-like POST testing"
echo "command: wb -t 10 -c 10 -p packets/requestbody2kb.json -T application/json 10.0.1.44:12701"
wb -t 10 -c 10 -p packets/requestbody2kb.json -T application/json 10.0.1.44:12701