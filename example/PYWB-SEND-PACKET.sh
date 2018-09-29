#!/bin/sh

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

basepath=$(cd `dirname $0`; pwd)
echo "Send customized traffics by pywb"
echo "command: $basepath/../pywb/main.py -F $basepath/packets/test-2-packets.yaml  -c 20 -t 5 10.0.1.43:18080"
$basepath/../pywb/main.py -F $basepath/packets/test-2-packets.yaml -c 20 -t 5 10.0.1.43:18080

