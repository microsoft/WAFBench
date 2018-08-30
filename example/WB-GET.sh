#!/bin/sh

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

basepath=$(cd `dirname $0`; pwd)
echo "Doing AB-like GET testing"
echo "command: wb -t 10 -c 20 10.0.1.44:12701"
wb -k -t 10 -c 20 10.0.1.44:12701