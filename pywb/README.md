 [WB Home Page](../README.md)

# pywb

`pywb` is an enhanced interface for `wb`. It is more friendly to use and easier for developing.

## Features

## Prerequisites

Some software or libraries may be necessary for have been listed in [WB Home Page](../README.md), and another requisite is that `wb`(Version >= 1.2.1) need be installed.

### Synopsis

```
./main.py [options] [http[s]://]hostname[:port]/path
```

### Options

**options** are compatible with [wb](../wb/README.md).


***ENHANCE OPTION***

- -F supports *.yaml and *.pkt and directories that include these kinds of file. Meanwhile, you can set -F multiple times to send multiple packets saved in different files at once.
- -u and -p will automatically identify the file type that wants to be sent by its ext, and modify the Content-Type. These options support almost all of the types that are mentioned by MIME.

### Example

```
# post a json file, automatically infer the Content-Type
./main.py  10.0.1.131:18080  -p ../example/packets/requestbody2kb.json  -t 5 -c 20

# send packets in a specified directory
./main.py  10.0.1.131:18080  -F ../example/packets/  -t 5 -c 20

# send packets in multiple files
./main.py  10.0.1.43:18080 -t 5 -c 20 -k -F ../example/packets/test-2-packets.yaml -F ../example/packets/test-2-packets.pkt
# or
./main.py  10.0.1.43:18080 -t 5 -c 20 -k -F ../example/packets/test-2-packets.yaml ../example/packets/test-2-packets.pkt
```

### Develop
Two interfaces are provided to developers to customize new features. 
```
# optionparser.py
class OptionParser(object):
    """ OptionParser is an abstract class and defines the interfaces.
        All of option parser need inherit this class.
    """

    def do(self, arguments):
        """ Do the action

        Arguments:
            - arguments: a list, the arguments what this action need

        Return is a interger that means the number of this action need
        """
        return 0

    def dump(self):
        """ Dump the new options for wb

        Return a list of string, the options that will be passed to wb
            it's a parameters list. if the space-separated string is inserted
            into the return list, it'll be as just one parameter to pass to wb
        """
        return []

    def help(self):
        """ Help document for this action

        Return is a string of help document for option bound by this instance
        """
        return " "


# outputfilter.py
class OutputFilter(object):
    """ Process the output of wb
        Line by line to process the output of wb.
        It's not recommended to modify the line, because it maybe
        conflict with other filters

    Arguments:
        line: a line of string end with '\n' from the output of wb,
            the concrete content depends on the runtime of wb.

    Return is a string. If the return is None, this filter will be a
        terminator, which means that all of the filters after this will
        lose the information of this line.
    """
    def __call__(self, line):
        return line


#######################
#EXAMPLE OPTION PARSER#
#######################


import pywb


# IMPLEMENT import command
# import previous command that save in the file pywb.ini (-t 5 -c 20 10.0.1.43:18080)
# by -x pywb.ini
class ExecuteINI(pywb.OptionParser):
    def do(self, options):
        #options[0] will be the file path
        command = ""
        with open(options[0], 'r') as fd:
            command = fd.readline()
            #remove newline char
            command = command.strip()
        #split command into a list
        self.__command = command.split(' ')
        #return 1 to tell pywb, this parser only eat one argument
        return 1
    def dump(self):
        #return all of commands that will pass to wb
        print self.__command
        return self.__command
    def help(self):
        return "   -x FILE      will import some arguments that were saved in FILE as the arguments of wb"

#execute wb
pywb.execute(["-x", "pywb.ini"], customized_options={ "-x":ExecuteINI()})



#######################
#EXAMPLE FILTER       #
#######################

import pywb

# IMPLEMENT logger
# to save all of output from wb 
class logger(pywb.OutputFilter):
    def __init__(self, log_file):
        self.__log_file = log_file
    def __call__(self, line):
        #ignore those lines only include spaces
        import re
        with open(self.__log_file, 'a') as fd:
            #save log into file
            fd.write(line)
        return line

pywb.execute([], customized_filters=[logger("log")])

```
