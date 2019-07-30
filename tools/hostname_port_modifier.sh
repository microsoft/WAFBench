#!/bin/bash

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


script_dir=$(cd $(dirname $(readlink -f $0));pwd -P)

if [[ "$#" -lt 2 ]];
then
    echo "Modify Hostname and Port for testcases"
    echo "  $0 {url} {testcases_dir}"
    echo "E.G. $0 'https://www.microsoft.com:80/'"
    exit 1
fi

url=$1
testcases_dir=$2

url_pattern="(https?://)?([^:/]+)(:([0-9]+))?.*"
if [[ ${url} =~ ${url_pattern} ]];
then
    hostname=${BASH_REMATCH[2]}
    port=${BASH_REMATCH[4]}
    if [[ ${hostname} ]];
    then
        echo "Hostname: ${hostname}"
        find . -name '*.yaml' | xargs sed -i -E $'s/^(\\s*[Hh]ost:\\s+)[\'"]?.+[\'"]?/\\1 '${hostname}'/g'
    fi
    if [[ ${port} ]];
    then
        echo "Port: ${port}"
        find . -name '*.yaml' | xargs sed -i -E $'s/^(\\s*[Pp]ort:\\s+)[\'"]?.+[\'"]?/\\1 '${port}'/g'
    fi
else
    echo "${target_server} is not a valid server."
    exit 1
fi


