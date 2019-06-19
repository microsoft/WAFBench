#!/usr/bin/env python3

import sys
import glob
import argparse
import os
import re
import subprocess
import csv
import collections
import time

command = "wb -c {connection} -s 3600 -t {time_limit} -2 2 -F {packet_file} {server} "


def extract_latency(stdout):
    latency = collections.OrderedDict()

    average_rps = re.search(b"Requests per second:\s*(\d+(?:.\d+)?)", stdout)
    if average_rps:
        latency["average(ms)"] = 1000 / float(average_rps.group(1))
    else:
        latency["average(ms)"] = None

    mean_latency = re.search(b"Total:\s*\d+\s*(\d+)", stdout)
    if mean_latency:
        latency["mean(ms)"] = float(mean_latency.group(1)) / 1000
    else:
        latency["mean(ms)"] = None

    _99_latency = re.search(b"\s*99%\s*(\d+)", stdout)
    if _99_latency:
        latency["99th(ms)"] = float(_99_latency.group(1)) / 1000
    else:
        latency["99th(ms)"] = None

    _90_latency = re.search(b"\s*90%\s*(\d+)", stdout)
    if _90_latency:
        latency["90th(ms)"] = float(_90_latency.group(1)) / 1000
    else:
        latency["90th(ms)"] = None
    
    return latency

def test(path, server, time_limit, connection, output):
    packet_files = []
    if os.path.isdir(path):
        hostname = re.search(r"^(?:https?://)?([^?/]+)", server).group(1)
        for file in glob.glob(os.path.join(path, "*.txt")):
            _file = "".join(os.path.splitext(file)[:-1]) + ".pkt"
            with open(file, "rb") as src_fd:
                with open(_file, "wb") as dst_fd:
                    content = src_fd.read().decode("utf-8")
                    content = re.sub(r"Host: (\S+)", "Host: " +
                                     hostname, content, count=1, flags=re.I)
                    content = str(len(content.encode("utf-8"))) + "\n" + content
                    dst_fd.write(content.encode("utf-8"))
            packet_files.append(_file)
    elif os.path.isfile(path):
        packet_files = [path]
    packet_files = sorted(packet_files)
    process_count = 0
    with open(output, "w") as fd:
        fd = csv.writer(fd)
        for file in packet_files:
            packet_name = re.search(r"([^/]+).pkt$", file).group(1)
            error = ""
            _command = command.format(time_limit=time_limit,
                               packet_file=file, server=server, connection=connection)
            print(_command)
            proc = subprocess.Popen(
                _command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
            latency = {}
            try:
                if proc.wait(timeout=(time_limit * 2)) == 0:
                    latency = extract_latency(proc.communicate()[0])
                else:
                    error = proc.communicate()[1]
            except subprocess.TimeoutExpired:
                error = "Process timeout"
            sys.stderr.write(str(error) + "\n")
            if process_count == 0:
                titles = ["id", "packet_name"] + list(latency.keys())
                fd.writerow(titles)
            process_count += 1
            print("%s %s rps [%s/%s]" % (packet_name, latency, process_count, len(packet_files)))
            values = [process_count, packet_name] + list(latency.values())
            fd.writerow(values)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='''
            Test the performance or latency of target server.
            E.G. 
                waf_perf.py -p packet.txt -s localhost:80 -c 1
                waf_perf.py -p packet.txt -s localhost:80 -c 4000
            ''')
    parser.add_argument("-p", "--path", help="packets path", required=True)
    parser.add_argument("-s", "--server", help="target server", required=True)
    parser.add_argument("-t", "--time_limit", help="time limit",type=int, default=60)
    parser.add_argument("-o", "--output", help="output file",type=str, default="output.csv")
    parser.add_argument("-c", "--connection", help="connection",type=int, default=1)
    args = parser.parse_args()
    test(args.path, args.server, args.time_limit, args.connection, args.output)
