#!/bin/sh

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

basepath=$(cd `dirname $0`; pwd)
echo "Send custom traffics"
echo "command: $basepath/../wb/wb -F $basepath/packets/test-2-packets.pkt -c 20 -t 5 10.0.1.44:12701"
$basepath/../wb/wb -F $basepath/packets/test-2-packets.pkt -c 20 -t 5 10.0.1.44:12701
