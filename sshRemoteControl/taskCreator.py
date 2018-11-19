"""taskCreator

This makes a Task file to be run with sshRemoteControl,
taking input from the console.

The file ending determines the format to write, either XML or JSON.
Other extensions are NOT considered.

Example:

    python3 taskCreator.py <Task file>
    python3 taskCreator.py -e|--encrypt
    python3 taskCreator.py -h|--help

"""

import os
import sys
import os.path
from getpass import getpass
from lib import Activity, Devices


def banner():
    """Print a banner on STDOUT about how to call this program."""
    print("""
Usage:

    taskCreator.py <file>
        <file> is the XML or JSON file to write.
        It must end in either .xml or .json

    taskCreator.py -e|--encrypt
        Takes a password on STDIN and retuns it encrypted.
        Used to manually edit Task files.

    taskCreator.py -h|--help

by Ignacio Tamayo (c) 2018. tamayo_j@minet.net
""")


def execute():
    """Run main Routine.

    1) Checks the 2 arguments passed from the command line
    2) If there is an argument, it is interpreted as a destinatino filename and
        the Task creation is tried.

    Returns 0 if all was OK, <>0 as ERRORCODE value.
    """
    if len(sys.argv) is not 2:
        print("ERR: Wrong number of arguments")
        banner()
        return 7
    elif len(sys.argv) == 2:
        try:
            if sys.argv[1].lower() in ("-h", "--help"):
                banner()
                return 0
            elif sys.argv[1].lower() in ("-e", "--encrypt"):
                return printEncrypt()
            else:
                return makeTask(sys.argv[1])
        except KeyboardInterrupt:
            return 99
    else:
        print("ERR: Invalid arguments")
        banner()
        return 8


def printEncrypt():
    """Takes a password on STDIN and retuns it encrypted.

        Used to manually edit Task files.
    """
    try:
        user = input('Username: ')
        passwd = getpass('Password: ')
        print("Encrypted Password = %s" %
              Activity.xor_crypt_string(passwd, user))
        return 0
    except EOFError:
        print("ERR: Unable to encrypt password text")
        return 21


def makeTask(filename):
    """Create the Task file from STDIN input.

    Given a filename to write to, a Task is created from console input
        and the output filename is writen.

    Returns: 0 if the task was run (not the result of the task execution),
        <>0 if there was an error.

    The matching between the file format and the actual file is not checked,
    it is assumed by the extension.

    Parameters:
    * filename: A filename that describes the Task, in XML or JSON format.
        It must be an absolute path. It must end in .xml or .json.

    """
    filename, file_extension = os.path.splitext(filename)
    anActivity = Activity.Activity()
    if file_extension.lower() not in (".xml", ".json"):
        print("ERR: Invalid file '%s'" % filename)
        return 13
    # Ask the user the Task Values and put them in the Task
    print("\nBEWARE: Case sEnSiTIVe input!\n")
    if not fillFromCLI(anActivity):
        print("ERR: Activity not created")
        return 16
    # The user created a good TASK
    if file_extension.lower() == ".xml":
        if not anActivity.writeToXML(sys.argv[1]):
            print("ERR: Unable to write from XML file")
            return 11
    elif file_extension.lower() == ".json":
        if not anActivity.writeToJSON(sys.argv[1]):
            print("ERR: Unable to write from JSON file")
            return 12
    anActivity.printSummary()
    print("End")


def inputYesNo(mesg):
    """Print the message, if STDIN input is Y|Ye|Yes, returns True."""
    text = input(mesg)
    if text.lower() == "y" or text.lower() == "ye" or text.lower() == "yes":
        return True
    else:
        return False


def fillFromCLI(anActivity):
    """Via STDIN/STDOUT, the values of the activity are filled.

    Case Senstive!

    Returns True if the Activity was created, False else.

    Parameters:
    * anActivity: The activity to fill data.

    """
    try:
        anActivity.name = input('Activity Name: ')
        anActivity.description = input('Description: ')
        anActivity.user = input('Login User: ')
        anActivity.password = getpass('Login Password: ')
        inputList = list(Devices.listOfDeviceTypes)
        inputList.append("[default]")
        aDeviceType = input(
            'Device Type %s: ' % inputList)
        if aDeviceType not in Devices.listOfDeviceTypes:
            anActivity.deviceType = ""
        else:
            anActivity.deviceType = aDeviceType
            if inputYesNo('Need Super User ? ([No]/Yes) '):
                anActivity.superuserNeeded = True
                anActivity.superuserPassword = getpass(
                    'Super Password: ')
        print(
            "Insert the target devices, one by one. End by an empty hostname")
        h = input('Hostname: ')
        while h and h != "":
            anActivity.targets.append(h)
            h = input('Hostname: ')
        print("Insert the commands, one by one. End by an empty command")
        c = input('Command: ')
        while c and c != "":
            anActivity.commands.append(c)
            c = input('Command: ')
        if inputYesNo('Output to a file instead of console text? ([No]/Yes) '):
            anActivity.outputDir = input('Output Directory: ')
            if inputYesNo('Single output file ? ([No]/Yes) '):
                anActivity.singleFile = True
        if inputYesNo('Log to a file instead of console text? ([No]/Yes) '):
            anActivity.logDir = input('Log Directory: ')
        print("")
        return True
    except EOFError:
        return False


if __name__ == "__main__":
    execute()

"""taskCreator

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
