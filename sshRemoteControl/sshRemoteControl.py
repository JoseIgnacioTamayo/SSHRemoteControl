"""sshRemoteControl.

Script to deliver several commands and obtain output from
    several network devices via SSH.

The Task to perform is described in a JSON File or XML File, given as input.
Please read through the description of the Task to understand
    all the possibilities.

This tool is designed to be run as a crontab job, or independently.

:Example:

    python3 sshRemoteControl.py  <XML file>
    python3 sshRemoteControl.py  <JSON file>
    python3 sshRemoteControl.py  -h
"""

import os
import sys
import os.path
from lib.Activity import Activity


def banner():
    """Print a banner on STDOUT about how to call this program."""
    print("""
Usage:
    sshRemoteControl.py <file>
        <file> is the XML or JSON task file.
        It must end in either .xml or .json

    sshRemoteControl.py -h|--help

by Ignacio Tamayo (c) 2018. tamayo_j@minet.net
""")


def execute():
    """Run main Routine.

    1) Checks the arguments passed from the command line
    2) If there is a task to run as argument, run it

    Returns the ErrorCode of the execution (<>0 if OK)

    The local directories are ./output and ./logs
    This functions expects parameters in 'sys.argv'
    """
    if len(sys.argv) is not 2:
        print("ERR: Wrong number of arguments")
        banner()
        return 7
    elif len(sys.argv) == 2:
        if sys.argv[1].lower() in ("-h", "--help"):
            banner()
            return 0
        else:
            filename = os.path.abspath(sys.argv[1])
            if os.path.exists(filename):
                # If the Path passed as argument is a valid path to file
                return runTask(filename)
            else:
                print("ERR: Invalid file '%s'" % filename)
                banner()
                return 8
    else:
        print("Invalid arguments")
        banner()
        return 3


def runTask(filename):
    """Given a Task described in a File, the Task is run.

    Returns 0 if the task was run (not the result of the task execution),
    <> if there was an error.

    The matching between the file format and the actual file is not checked,
        it is assumed.

    Parameters:
    * filename: A filename that describes the Task, in XML or JSON format.
      It must be an absolute path. It must end in .xml or .json.

    """
    if not os.path.exists(filename):
        return 9
    filename, file_extension = os.path.splitext(filename)

    anActivity = Activity()

    if file_extension.lower() in (".xml", ".json"):
        if file_extension.lower() == ".xml":
            if not anActivity.loadFromXML(sys.argv[1]):
                print("ERR: Unable to load from XML file")
                return 11
        else:
            if not anActivity.loadFromJSON(sys.argv[1]):
                print("ERR: Unable to load from JSON file")
                return 12
        try:
            anActivity.check()
        except ValueError as e:
            print("ERR: Activity file is not valid: %s" % e)
            return 13
    else:
        print("ERR: Invalid file extension")
        return 13

    anActivity.printSummary()

    print("Running...")
    try:
        anActivity.run()
    except KeyboardInterrupt:
        return 99
    return 0


if __name__ == "__main__":
        execute()

"""
sshRemoteControl

Copyright (c) 2018 Jose Ignacio Tamayo Segarra

Permission is hereby granted, free of charge,
to any person obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH
THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
