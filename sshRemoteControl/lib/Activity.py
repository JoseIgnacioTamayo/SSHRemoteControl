"""Class representing an RemoteControl Activity.

Author: Jose Ignacio Tamayo Segarra
Date: Nov 2018

"""

import sys
import os
import json
import re
import codecs
from . import Devices
from lxml import etree
from datetime import datetime
from itertools import cycle


_debug = False


class Activity(object):
    """Representation of a set of Commands to be executed in a set of Devices.

    By DEFAULT:
        No Superuser is needed
        No Output directory, output goes to STDOUT
        No Log directory, log messages go to STDOUT
        Default Device Type

    The Passwords are stored in the Files in HEX-encoded XOR-encrypted Strings.

    The Activity.name text is used to create the filenames of
        the log and output files.

    Properties:
        * name: A short Name of the task, used to create the output file.
            NO Spaces, no Special characters.
        * description: a longuer description for the tasks,
            can have spaces and special characters. No CR/LR.
        * user: Clear text user.
        * password: HEX XOR-encrypted password.
        * superuserPassword:  HEX XOR-encrypted password.
        * superuserNeeded: True if the Activity needs to execute
            the superuser() method on the devices.
        * targets: List of IPs/Hostnames to apply the commands into.
        * commands: List of text commands to send over SSH and store
            the output in the output file(s).
        * outputDir: Directory where to store the output file(s).
        * logDir: Directory where to store the log file.
        * logFilename: Filename constructed from the Activity.name
            and the current date.
        * outputFilename: Filename constructed from the Activity.name
            and the current date.
        * logFile: If no logDir is set, this is STDERR.
        * outputFile: If no logDir is set, this is STDOUT.
        * singleFile: True is all the output of all the targets are appended
            to a single output file.
        * deviceType: Text of the list Devices.listOfDeviceTypes that
            indicates which type of Device to use.
    """

    name = ""
    description = ""
    user = ""
    password = ""
    superuserPassword = ""
    superuserNeeded = False
    targets = []
    commands = []
    outputDir = None
    logDir = None
    logFilename = ""
    outputFilename = ""
    logFile = sys.stderr
    outputFile = sys.stdout
    singleFile = False
    deviceType = ""

    def loadFromXML(self, filename):
        """Load the Activity values from the XML File.

        This does not check for valid values, see the .check() method.

        Returns True if loading ok, False if not.
        Errors/Exceptions are written to STDERR.

        Parameters:
        * filename: Path to the XML file to read

        """
        try:
            tree = etree.parse(filename)
            root = tree.getroot()
            self.name = root.attrib['name']
            self.user = root.find('login').get('user')
            self.password = root.find('login').get('password')
            self.password = xor_decrypt_string(self.password, self.user)
            if root.find('desc') is not None:
                self.description = root.find('desc').text
            if root.find('superuserPassword') is not None:
                self.superuserNeeded = True
                self.superuserPassword = root.find(
                    'superuserPassword').get('password')
                self.superuserPassword = xor_decrypt_string(
                    self.superuserPassword, self.user)
            if root.find('output') is not None:
                self.outputDir = root.find('output').get('dir')
                if root.find('output').get('singleFile').lower() == 'yes':
                    self.singleFile = True
            if root.find('log') is not None:
                self.logDir = root.find('log').get('dir')
            self.targets = []
            self.commands = []
            if root.find('devices').get('type') is not None:
                self.deviceType = root.find('devices').get('type')
            for host in root.find('devices'):
                self.targets.append(host.text)
            for cmd in root.find('commands'):
                self.commands.append(cmd.text)
            return True
        except (etree.ParseError, KeyError) as e:
            sys.stderr.write(
                "Activity-Load: Elements missing from the XML file\n")
            if _debug:
                sys.stderr.write("Activity-Load Exception %s" % e)
            return False

    def writeToXML(self, filename):
        """Write the Activity values to the XML File.

        Returns True if loading ok, False if not.
        Errors/Exceptions are written to STDERR.

        Parameters:
        * filename: Path to the XML file to read

        """
        try:
            ActivityRoot = etree.Element('activity', {'name': self.name})
            if self.description:
                d = etree.SubElement(ActivityRoot, 'desc')
                d.text = self.description
            etree.SubElement(
                ActivityRoot,
                'login',
                {
                    'user': self.user,
                    'password': xor_crypt_string(self.password, self.user)
                })
            if self.superuserNeeded:
                etree.SubElement(
                    ActivityRoot,
                    'superuserPassword',
                    {
                        'password': xor_crypt_string(
                            self.superuserPassword,
                            self.user)
                    })
            if self.deviceType:
                dev = etree.SubElement(
                    ActivityRoot,
                    'devices',
                    {'type': self.deviceType})
            else:
                dev = etree.SubElement(ActivityRoot, 'devices')
            for t in self.targets:
                h = etree.SubElement(dev, 'hostname')
                h.text = t
            cmd = etree.SubElement(ActivityRoot, 'commands')
            for c in self.commands:
                line = etree.SubElement(cmd, 'cmd')
                line.text = c
            if self.outputDir:
                etree.SubElement(
                    ActivityRoot,
                    'output',
                    {
                        'dir': self.outputDir,
                        'singleFile': ('Yes' if self.singleFile else 'No')
                    })
            if self.logDir:
                etree.SubElement(ActivityRoot, 'log', {'dir': self.logDir})
            tree = etree.ElementTree()
            tree._setroot(ActivityRoot)
        except etree.ParseError as e:
            sys.stderr.write(
                "Activity-Write: Some elements are missing to the XML file\n")
            if _debug:
                sys.stderr.write("Activity-Write Exception %s" % e)
            return False
        try:
            totalPath = os.path.abspath(filename)
            directory = os.path.dirname(totalPath)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            tree.write(totalPath, pretty_print=True)
            return True
        except (IOError, OSError) as e:
            sys.stderr.write(
                "Activity-Write: Errors trying to write to '%s': %s\n" % (
                    totalPath, e
                ))
            return False

    def writeToJSON(self, filename):
        """See writeToXML."""
        data = dict()
        data['name'] = self.name
        data['desc'] = self.description
        data['login'] = self.user
        data['password'] = xor_crypt_string(self.password, self.user)
        if self.superuserNeeded:
            data['superuserPassword'] = xor_crypt_string(
                self.superuserPassword,
                self.user)
        if self.deviceType:
            data['type'] = self.deviceType
        data['devices'] = self.targets
        data['commands'] = self.commands
        if self.outputDir:
            data['outputDir'] = self.outputDir
            if self.singleFile:
                data['singleFile'] = True
        if self.logDir:
            data['logDir'] = self.logDir
        try:
            totalPath = os.path.abspath(filename)
            directory = os.path.dirname(totalPath)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            with open(filename, 'w') as outfile:
                json.dump(
                    data,
                    outfile,
                    ensure_ascii=True,
                    indent=4,
                    separators=(',', ': '))
            return True
        except (IOError, ValueError, OSError) as e:
            sys.stderr.write(
                "Activity-Write: Errors trying to write to '%s'\n" % (
                    totalPath, e
                ))
            return False

    def loadFromJSON(self, filename):
        """See also loadFromXML."""
        try:
            with open(filename) as data_file:
                data = json.load(data_file)
        except (KeyError, ValueError, OSError) as e:
            sys.stderr.write(
                "Activity-Load: Elements are missing from the JSON file\n")
            if _debug:
                sys.stderr.write("Activity-Load Exception %s" % e)
            return False
        self.name = data['name']
        self.user = data['login']
        self.password = data['password']
        self.password = xor_decrypt_string(self.password, self.user)
        self.targets = data['devices']
        self.commands = data['commands']
        try:
            self.deviceType = data['type']
            self.outputDir = data['outputDir']
            self.singleFile = data['singleFile']
            self.logDir = data['logDir']
        except KeyError:
            pass
        try:
            self.superuserPassword = data['superuserPassword']
            self.superuserPassword = xor_decrypt_string(
                self.superuserPassword,
                self.user)
            self.superuserNeeded = True
        except KeyError:
            pass
        return True

    def check(self):
        """Check that the Activity has valid values.

        Prevents problems that could arise on execution.
        Errors are raised as ValueError exceptions.

        Checks Activity.name, proper DeviceType, valid output directory,
            writable logFile, targets>0, commands>0.

        If the outpuDir does not exist, this methd will try to create it.
        """
        if self.name == "":
            raise ValueError("Missing name")
        if self.outputDir:
            try:
                testMakeDir(self.outputDir)
            except Exception:
                raise ValueError("Failed output directory" + self.outputDir)
        if self.logDir:
            try:
                testMakeDir(self.logDir)
            except Exception:
                raise ValueError("Failed log directory " + self.logDir)
        if len(self.targets) == 0:
            raise ValueError("No target devices found")
        if len(self.commands) == 0:
            raise ValueError("No commands found")
        if self.deviceType:
            if self.deviceType not in Devices.listOfDeviceTypes:
                raise ValueError("Invalid device type " + self.deviceType)

    def printSummary(self):
        """Print some basic info about the Activity to STDOUT."""
        print("-------------Activity-------------------")
        print("\tName: %s " % self.name)
        print("\tUser: %s " % self.user)
        if self.superuserNeeded:
            print("\tSuperuser: YES ")
        if self.deviceType:
            print("\tDevice type: %s " % self.deviceType)
        print("\tDevices: %d " % len(self.targets))
        if self.singleFile:
            print("\tOutput File: %s " % os.path.join(
                self.outputDir, timestampedFilename(self.name+"_OUT")))
        elif self.outputDir:
            print("\tOutput Folder: %s  " % self.outputDir)
        if self.logDir:
            print("\tLog File: %s  " % os.path.join(
                self.logDir, timestampedFilename(self.name+"_LOG")))
        print("----------------------------------------")

    def printCredentials(self):
        """Print the credentials used in the Activity to STDOUT."""
        print("--------------Credentials-------------------")
        print("\tUser: " + self.user)
        print("\tPassword: " + self.password)
        if self.superuserNeeded:
            print("\tPowerPassword: " + self.superuserPassword)
        print("--------------------------------------------")

    def run(self):
        """Run the activity.

        Errors are placed in the LogFile of the Activity.
        """
        self.outputFilename = timestampedFilename(self.name+"_OUT")
        self.logFilename = timestampedFilename(self.name+"_LOG")
        self._openLogFile()
        if self.singleFile:
            self._openOutputFile(self.outputFilename)
        for hostname in self.targets:
            aDevice = Devices.createDevice(hostname, self.deviceType)
            if not aDevice.connect(self.user, self.password):
                self._writeLogFile(
                    "Unable to connect to " + hostname
                    + ". Test with a local SSH session.")
                continue
            self._writeLogFile("Connected to " + hostname)
            if not aDevice.login():
                self._writeLogFile(
                    "Unable to login to " + hostname
                    + ". \t Test with the default Device type.")
                continue
            if self.superuserNeeded:
                if not aDevice.superuser(self.superuserPassword):
                    self._writeLogFile("Unable to superuser at "+hostname)
                    continue
                else:
                    self._writeLogFile("Superuser at "+hostname)
            if not self.singleFile:
                self._openOutputFile(timestampedFilename(hostname))
            self._writeOutputFile(
                "\n----------------%s--------------\n" % hostname)
            if not aDevice.run(self.commands, self.outputFile):
                self._writeLogFile("ERROR while running the commmands")
            if not aDevice.logout():
                self._writeLogFile("ERROR while logging out")
            self._writeOutputFile(
                "\n--------------------------------------------------\n")
            if not self.singleFile:
                self._closeOutputFile()
            self._writeLogFile("Finished commands at " + hostname)
        self._writeLogFile("Finished activity")
        if self.singleFile:
            self._closeOutputFile()
        self._writeLogFile("END")
        self._closeLogFile()

    def _writeLogFile(self, msg):
        self.logFile.write(
            datetime.now().strftime('%H:%M:%S')+": " + msg + "\n")

    def _writeOutputFile(self, msg):
        self.outputFile.write(msg)

    def _openLogFile(self):
        """Ope the corresponding LogFile and keep it open.

        Either a file in the directory or STDERR.

        Raises IOError if there is a Log directory but no writing is possible.
        """
        if self.logDir:
            try:
                self.logFile = open(
                    os.path.join(self.logDir, self.logFilename),
                    'w')
            except OSError:
                sys.stderr.write(
                    "Activity: Unable to create log file '%s \n"
                    % self.logFilename)
                raise IOError
        else:
            self.logFile = sys.stderr

    def _openOutputFile(self, filename):
        """Open the corresponding OutputFile and leave it open.

        Either a file in the output or STDOUT.

        Raises IOError if there is a directory but no writing is possible.
        """
        if self.outputDir:
            try:
                self.outputFile = open(
                    os.path.join(self.outputDir, filename),
                    'w')
            except OSError:
                sys.stderr.write(
                    "Activity: Unable to create output file '%s'\n"
                    % filename)
                raise IOError
        else:
            self.outputFile = sys.stdout

    def _closeLogFile(self):
        if self.logDir:
            try:
                self.logFile.close()
            except OSError:
                sys.stderr.write("Activity: Unable to close log file  \n")

    def _closeOutputFile(self):
        if self.outputDir:
            try:
                self.outputFile.close()
            except OSError:
                sys.stderr.write("Activity: Unable to close output file  \n")


def timestampedFilename(baseFileName):
    """Return the .txt filename timestamped as <baseFileName>_<timestamp>.txt.

    The 'baseFileName' is cleansed to have only [-a-zA-Z0-9_] characters.
    """
    return "%s_%s.txt" % (
        re.sub(r'[^-a-zA-Z0-9_\.]+', '', baseFileName),
        datetime.now().strftime('%Y%m%d_%H%M%S'))


def testMakeDir(directory):
    """Tries to create the directory, if it does not exist already.

    Then it creates and deletes a temporary 'tmp.tmp' file.
    Raises OSError if the tests fail.
    """
    os.makedirs(directory,  exist_ok=True)
    aFile = open(os.path.join(directory, "tmp.tmp"), 'w')
    aFile.close()
    os.remove(os.path.join(directory, "tmp.tmp"))
    return True


def xor_crypt_string(plaintext, key):
    """Return the chypher of plaintext using the key.

    http://stackoverflow.com/questions/11132714/python-two-way-alphanumeric-encryption
    """
    ciphertext = ''.join(
        chr(ord(x) ^ ord(y)) for(x, y) in zip(plaintext, cycle(key)))
    return codecs.encode(ciphertext.encode("utf-8"), "hex").decode("utf-8")


def xor_decrypt_string(ciphertext, key):
    """See xor_crypt_string."""
    ciphertext = codecs.decode(ciphertext, 'hex')
    return ''.join(
        chr(x ^ ord(y)) for(x, y) in zip(ciphertext, cycle(key)))
