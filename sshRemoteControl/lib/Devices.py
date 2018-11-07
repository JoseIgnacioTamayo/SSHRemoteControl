"""Class representing an RemoteControl Device.

Author: Jose Ignacio Tamayo Segarra
Date: Nov 2018

"""

import paramiko
import time
import sys
import paramiko.ssh_exception as ParamikoExcept
from socket import error as SocketError

# Development log
# paramiko.common.logging.basicConfig(level=paramiko.common.INFO)
_debug = False
_bufferSize = 1024  # Buffer for SSH connection
listOfDeviceTypes = ("ciscoios", "ciscowlc", "linux")


def createDevice(hostname, typeClass=""):
    """Return a Device object, created for the hostname.

    Parameters:
    * hostname: Ip or hostname to connect to via SSH
    * typeClass: A class of device. If "" or not in 'Devices.listOfDevices',
        the default Device is created. This is a case-insensitive string.

    """
    if typeClass.lower() == "ciscoios":
        return DeviceCiscoIOS(hostname)
    elif typeClass.lower() == "ciscowlc":
        return DeviceCiscoWLC(hostname)
    elif typeClass.lower() == "linux":
        return DeviceLinux(hostname)
    else:
        return Device(hostname)


class Device(object):
    """Represents a remote controlled device connected with SSH.

    The Device class is a generic that interacts witht the Activity module.
    Any specific device must inherit from this Device class and
        implement the methods login() and super().

    Source:
    http://jessenoller.com/blog/2009/02/05/ssh-programming-with-paramiko-completely-different,
    http://stackoverflow.com/questions/25101619/reading-output-of-top-command-using-paramiko

    Example:
        aDevice = Device('localhost', type = Devices.DeviceCisco)
        aDevice.connect()
        aDevice.super() #if needed
        aDevice.run({"","",""},outfile)
        aDevice.logout()
    """

    def __init__(self, hostname):
        """Build."""
        self.hostname = hostname
        self.SSHClient = paramiko.SSHClient()
        self.RemoteShell = None
        self.username = ""
        self.password = ""

    def connect(self, username, password):
        """Brings up the SSH connection, if possible, using the credentials.

        No command is typed once the SSH session is open.
        Returns True if connection ok, False if not.
        """
        self.username = username
        self.password = password
        try:
            self.SSHClient.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
            self.SSHClient.connect(
                self.hostname,
                username=username,
                password=password,
                allow_agent=False,
                look_for_keys=False)
            self.RemoteShell = self.SSHClient.invoke_shell()
            return True
        except (ParamikoExcept.SSHException, SocketError) as e:
            if _debug:
                sys.stderr.write(
                    "Device.connect to '%s' caused Exception %s"
                    % (self.hostname, e))
            return False

    def run(self, commands, outfile):
        r"""Run a list of commands and writes the output to a file.

        File must be already opened when passed.

        Returns True if all commands were sent ok, False if not.

        Parameters:
        * commands: a list of strings witht the commands.
            No need to have "\n" at the end.
        * outfile: a file pointer to write data to.
            This file must have been opened and accepting input.

        """
        cmd = ""
        try:
            while self.RemoteShell.recv_ready():
                data = self.RemoteShell.recv(_bufferSize).decode("utf-8")
                outfile.write(data)
            for cmd in commands:
                if self.RemoteShell.send(cmd + "\n") == 0:
                    raise IOError
                time.sleep(2)
                while self.RemoteShell.recv_ready():
                    data = self.RemoteShell.recv(_bufferSize).decode("utf-8")
                    outfile.write(data)
            return True
        except (ParamikoExcept.SSHException, SocketError, UnicodeDecodeError) as e:
            if _debug:
                sys.stderr.write(
                    "Device.run: Command '%s' caused exception %s"
                    % (cmd, e))
            return False

    def superuser(self, password):
        """Do nothingself.

        The Default device does not have an ENABLE mechanism.

        This is to be implemented in the Child classes.

        Return True always.
        """
        return True

    def login(self):
        """Do nothing.

        The Default device does not have an Login mechanism,
            the SSH connection should be enough.
        This is to be implemented in the Child classes.

        Returns True always.
        """
        return True

    def logout(self):
        """Do Nothing.

        The default Device does not send any command,
            just closes the SSH session via TCP close.

        The session might not be availabe for logout if any 'close' or 'logout'
        was among the executed commands.
        """
        try:
            self.RemoteShell.close()
            self.SSHClient.close()
            return True
        except (ParamikoExcept.SSHException, SocketError) as e:
            if _debug:
                sys.stderr.write("Device.logout: Exception %s" % e)


class DeviceCiscoIOS(Device):
    """Device specific for Cisco IOS switches and routers."""

    def superuser(self, password):
        """Enable mechanism.

        Returns True if at the end there is the '#' in the prompt.

        Parameters:
        * password: Plain text password

        """
        result = False
        try:
            while self.RemoteShell.recv_ready():
                self.RemoteShell.recv(_bufferSize).decode("utf-8")
            self.RemoteShell.send("enable \n")
            data = ""
            time.sleep(1)
            while self.RemoteShell.recv_ready():
                data = self.RemoteShell.recv(_bufferSize).decode("utf-8")
            if data.find("Password:") != -1:
                self.RemoteShell.send(password + "\n")
                data = ""
                time.sleep(1)
                while self.RemoteShell.recv_ready():
                    data = self.RemoteShell.recv(_bufferSize).decode("utf-8")
                if data.find("#") != -1:
                    result = True
        except ParamikoExcept.SSHException as e:
            if _debug:
                sys.stderr.write("DeviceCiscoIOS.superuser: Exception %s" % e)
        return result

    def logout(self):
        """Send the 'end' and 'exit' commands before closing the SSH session.

        Returns False if there were any errors while loging out.
        """
        try:
            while self.RemoteShell.recv_ready():
                self.RemoteShell.recv(_bufferSize).decode("utf-8")
            self.RemoteShell.send("end \n")
            time.sleep(1)
            self.RemoteShell.send("exit \n")
            time.sleep(1)
            super(DeviceCiscoIOS, self).logout()
            return True
        except (ParamikoExcept.SSHException, SocketError) as e:
            if _debug:
                sys.stderr.write("DeviceCiscoIOS.logout Exception %s" % e)
            return False

    def login(self):
        """Send commands just after login.

        The command 'terminal lenght 0' is sent just after connecting,
        to have all the output placed on Screen.

        Returns True if connection is ok, False if not.
        """
        try:
            while self.RemoteShell.recv_ready():
                self.RemoteShell.recv(_bufferSize).decode("utf-8")
            self.RemoteShell.send("terminal length 0 \n")
            time.sleep(1)
            return True
        except (ParamikoExcept.SSHException, SocketError) as e:
            if _debug:
                sys.stderr.write("DeviceCiscoIOS.login Exception %s" % e)
            return False


class DeviceCiscoWLC(Device):
    """Device specific for Cisco WLC.

    Has an extra login prompt after the SSH is opened.

    By default, when loging out, the changes are NOT saved.
    If the changes are to be saved, put these commands in the list:

        <commands>
        end
        save config
        y
    """

    def logout(self):
        """Send the 'end' and 'exit' commands before closing the SSH session.

        To the 'Save config?' question, the answer given is NO.

        Returns the result of Device.logout(). False if there were any errors.
        """
        try:
            self.RemoteShell.send("end \n")
            time.sleep(1)
            self.RemoteShell.send("exit \n")
            time.sleep(1)
            data = ""
            while self.RemoteShell.recv_ready():
                data = self.RemoteShell.recv(_bufferSize).decode("utf-8")
            if data.find("save?") != -1:
                self.RemoteShell.send("No \n")
                time.sleep(1)
            super(DeviceCiscoWLC, self).logout()
            return True
        except (ParamikoExcept.SSHException, SocketError) as e:
            if _debug:
                sys.stderr.write("DeviceCiscoWLC.logout Exception %s" % e)
            return False

    def login(self):
        """Send the credentials again, because there is this crazy login.

        Returns True if at the end there is the correct prompt '>',
            False if not.
        """
        try:
            self.RemoteShell.send(self.username + "\n")
            time.sleep(1)
            while self.RemoteShell.recv_ready():
                self.RemoteShell.recv(_bufferSize).decode("utf-8")
            self.RemoteShell.send(self.password + "\n")
            time.sleep(1)
            while self.RemoteShell.recv_ready():
                data = self.RemoteShell.recv(_bufferSize).decode("utf-8")
            if data.find(">") == -1:
                return False
            self.RemoteShell.send("config paging disable \n")
            time.sleep(1)
            return True
        except (ParamikoExcept.SSHException, SocketError) as e:
            if _debug:
                sys.stderr.write("DeviceCiscoWLC.login Exception %s" % e)
            return False


class DeviceLinux(Device):
    """Device specific for Linux using 'su'."""

    def superuser(self, password):
        """Send 'su' command and expects 'Password:' as reply.

        Then inputs the Root password and checks that the prompt
            contains 'root' string.
        Returns True if after the 'su', the prompt sais 'root'. False if not.

        Parameters:
        * password:  Clear text root password

        """
        try:
            while self.RemoteShell.recv_ready():
                self.RemoteShell.recv(_bufferSize).decode("utf-8")
            self.RemoteShell.send("su \n")
            data = ""
            time.sleep(1)
            while self.RemoteShell.recv_ready():
                data = self.RemoteShell.recv(_bufferSize).decode("utf-8")
            if data.find("Password:") != -1:
                self.RemoteShell.send(password + "\n")
                data = ""
                time.sleep(1)
                while self.RemoteShell.recv_ready():
                    data = self.RemoteShell.recv(_bufferSize).decode("utf-8")
                if data.find("root") != -1:
                    return True
            return False
        except (ParamikoExcept.SSHException, UnicodeDecodeError) as e:
            if _debug:
                sys.stderr.write("DeviceLinux.superuser Exception %s" % e)
            return False

    def logout(self):
        """Type 'logout' command before exiting the SSH Session.

        Returns False if there were any errors.
        """
        try:
            self.RemoteShell.send("logout \n")
            time.sleep(1)
            super(DeviceLinux, self).logout()
            return True
        except (ParamikoExcept.SSHException, SocketError) as e:
            if _debug:
                sys.stderr.write("DeviceLinux.logout Exception %s" % e)
            return False
