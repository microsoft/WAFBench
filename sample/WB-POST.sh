#!/bin/sh
basepath=$(cd `dirname $0`; pwd)
echo "Doing AB-like POST testing"
echo "command: wb -t 10 -c 10 -p requestbody2kb.json 10.0.1.44:12701"
wb -t 10 -c 10 -p requestbody2kb.json 10.0.1.44:12701

