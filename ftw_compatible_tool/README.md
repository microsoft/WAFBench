# FTW-Compatible Tool

FTW-Compatible Tool is a component of the [WAFBench](../README.md), which supports [FTW](https://github.com/fastly/ftw)(Framework for Testing WAFs) format YAML for WAF correctness testing. As FTW, it uses the OWASP Core Ruleset V3 as a baseline.

## Installation

### Dependencies

* **Python2** to run those script
* **FTW** python module to interpret YAML file

Python2 installation is as follows:

```bash
sudo yum install python           # Install python2
sudo yum install python-pip       # Install python2 pip
sudo pip install --upgrade pip    # Update pip
sudo pip install ftw              # Install the ftw library
```

## How to use FTW-compatible tools

### White-box Test

White-box test is to test the target server by checking whether 
the specific rule is matched in its ModSecurity error log.

1  Modify ModSecurity configuration

Add this rule into the head of modsecurity_init.conf, and  restart the Web server.

```
SecRule REQUEST_HEADERS:Host "magic-(\w*)" \
    "phase:1,\
    id:010203,\
    t:none,\
    deny,\
    msg:'delimiter-%{matched_var}'"
```

2  Enter the interactive mode of FTW-compatible tools, and run the following commands:  

2.1. Load test cases

```
load example.yaml   # or a folder containing multiple test cases
```

2.2. Generate PKT files

```
gen
```

2.3. Start testing the target server
```
start hostname:port
```

2.4. Import target server's ModSecurity error log
```
import error.log
```

2.5. Report failed cases
```
report
```
2.6. Finish the test and exit
```
exit
```

### Black-box Test

Black-box test is to test the target server that cannot get the ModSecurity log. FTW-Compatible Tool will compare the HTTP status code returned by target server with the expected HTTP status code set in test cases.

Black-box test does not require modifying ModSecurity configuration or importing any log file. It's recommended to run black-box test in batch mode:

```shell
python ./ftw_compatible_tool/main.py -d test.db -x "load example.yaml | gen | start hostname:port | report | exit"
```

### ftw_compatible_tool help

```bash
python ./ftw_compatible_tool/main.py -h
```

### Result database description

|Filed_name   |Description    |
|-------------|--------------|
|traffic_id| Unique ID of test record|
|test_title| Title of test case|
|meta|Whole content of test case|
|file|Full path of case file|
|input|Information for generating PKT file|
|output|Expected response from target server|
|request|Lite HTTP request for target server|
|raw_request|Complete HTTP request for target server, including the *Connection* field|
|raw_response|Complete response from target server|
|raw_log|ModSecurity error log of target server (optional, for white-box test only)|
|testing_result|Whether target server functions as expected|
|duration_time|Time spent on single test|

### Example

#### Interactive mode

```bash
python ./ftw_compatible_tool/main.py -i -d test.db

Input command : load example.yaml
Input command : gen
Input command : start hostname:port
Input command : import error.log
Input command : report
Input command : exit
```

#### Batch mode
```bash
python ./ftw_compatible_tool/main.py -d test.db -x "load example.yaml | gen | start hostname:port | report | exit"
```

