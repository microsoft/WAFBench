
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

FROM ubuntu:18.04

# Install build environment
RUN \
    apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y build-essential wget python python-pip python3 libssl-dev libexpat-dev
# Create workspace 
WORKDIR /WAFBench
COPY . /WAFBench
#  Install WAFBench
RUN \
    pip install -r requirements.txt && \
    make -C wb && make -C wb install



