import subprocess
import sys
import os

import common


_TOOLS_DIR = os.path.join(common._HOME_DIR, "tools")


def test_waf_perf():
    waf_perf = os.path.join(_TOOLS_DIR, "waf_perf.py")
    with common.HTTPServerInstance():
        packet_file = os.path.join(common._DATA_DIR, "packet.txt")
        assert(subprocess.check_call(
            [
                "python3", waf_perf, 
                "-s", "localhost:" + str(common._PORT), 
                "-p", packet_file,
                "-t", "1",
            ]
        ) == 0)
