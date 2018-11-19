# SSH Remote Control

> Ignacio Tamayo, 2018
>
> Version 1.0
>
> Date: Nov 2018

This is a Python3-based tool that connects to a set of devices via SSH and executes a set of commands, storing the output in text files.

The list of devices to connect to, connection parameters and commands to execute are described in a text file, called a **TASK**, which is the single needed input.

	python sshRemoteControl.py <TaskFile>

This tool is used for executing a set of pre-tested and well-known commands via SSH on a set of network devices, from a management station and later check the output files and log for processing.

The **TASK** file, a simple text file in JSON or XML format, contains the login credentials as encrypted text.

In order to create your own **TASK** files with the credentials appropriately encrypted, an scripts creates it from STDIN/STDOUT.

	python taskCreator.py <TaskFile>

Once created, the **TASK** files are easily maintanable, could be subject to version control (git or svn), and by text manipulation can be derived into similar scripts.
This offers an option to dealing with CSV files.

Another way to create your own **TASK** files is to take an existing one, making a copy and just changing the parameters. As the **TASK** is an structured text file, this would be easy. As per the encrypted credentials, use the previous script to obtain the encrypted text for a password:

		python taskCreator.py -encrypt

After the execution of any of the scripts above, a small summary or the **TASK** is written to *STDOUT* as:

    -------------Activity-------------------
            Name: {{name}}
            User: {{ssh user}}
            Devices type: {{device type}}
            Devices: {{number of devices}}
            {{...}}
    ----------------------------------------


> The encryption mechanism is weak, and by reading the Python source files it can be easily reversed-engineered. Do not rely on this for security, the encryption is intended for obscuring a bit the text in the **TASK** files.

## About **TASKs**

A **TASK** is a set of commands applied sequentially to a set of devices, that records the output of each device into a text file. I.e.: we need to execute some commands over SSH to discover all the OS versions and latest 10 logs of all switches in the network. And we would need this to be executed at night, not to disturb the network.

A Task has a *name*, possibly a *description*, and the *type* of device being used.

Obviously, *user*/*password* for all devices. The Task can have *superuser* option, that would trigger the device's mechanism to acquire administrative commands (`enable` in Cisco, `su` in Linux).

When the 'superuser' option is used (depends on the Device type how this is done), if the superuser fails, the execution is aborted on the device. So, if the 'superuser' password is wrong or the superuser mechanism fails, nothing is executed in the device.

The Task has a list of *devices* to connect to and execute the commands. If the connection on any device fail, the execution is not interrupted, the tool will connect to the next one on the list. The connection to the devices is sequential, so it might take some time to process long lists of devices.

The Task has *commands*. There is no need to place a **logout** or **exit** command. As the commands are executed over SSH, there is no mechanism to detect the correct execution of each command. If while running the commands the SSH connection breaks, an error is logged but no further connection is tried to the device.

Finally, the text output (text seen over the SSH connection) is left on an *output directory*. It will create one text file for each device, with the name of the device and the timestamp (i.e. `<device>_20150605_090805.txt`). Optionally, a *single text file* can be created with the output of all the devices (used for simple short commands on several devices, no need to have several very small files but a single mid-sized file). If no *output directory* is selected, the output will be shown in **STDOUT**.

In order to know what happened while running the **TASK**, a log file is left in the *log directory*, with the name of the task and the timestamp (i.e. `<task.Name>_20180708_050603.txt`). If no *log directory* is selected, the log messages will be shown in **STDOUT**.

The **TASKs** are described in a .XML or .JSON file. All the passwords are stored encrypted.

See the lib.Activity.py documentation for details.

## About the **Device Types**

A single **TASK** is executed for a single type of device. If multiple types of devices, a **Task** for each type is needed.

 * **ciscoIOS**: Sends 'terminal length 0' just after connecting, has 'enable' as superuser() mechanism, and sends 'end' and 'exit' before closing the connection.

 * **ciscoWLC**: Sends the credentials after the SSH connection, because there is another login, sends 'end' and 'exit' before closing the connection. To the 'Save config?' question, the answer given is NO.

By default, when loging out, the config changes are NOT saved. The changes are applied but will not keep after reboot.
If the changes are to be saved, put these commands in the list:

	<commands>
	end
	save config
	y

The superuser mechanism for this type of device does nothing. Even if defined in the **TASK**, it does nothing.

 * **linux**: Has 'su' as superuser() mechanism, and sends 'logout' before closing the connection.

 * Default: Does nothing of the said above, it is a simple SSH connection.

## About the output ##

Either in *STDOUT*, multiple or single output file, for each device the output is:

    ----------------{{hostname}}--------------
    {{ SSH session output }}
    --------------------------------------------------

## About the logs ##

Either in *STDOUT* or a log file, the execution events are writen as:

    Running...
    10:04:31: Connected to 192.168.176.111
    10:04:34: Superuser at 192.168.176.111
    10:04:44: Finished commands at 192.168.176.111
    10:04:44: Finished activity

# Running

## Dependencies

 * python>3.5
 * paramiko
 * lxml

## Installl Instructions

	pip install -r requirements.txt

If execution fails, re-install Paramiko and Cryptography as instructed in: http://www.paramiko.org/installing.html
For Linux-like systems, the libraries 'libxml2-dev' and 'libxslt1-dev' are needed for python to compile the 'lxml' package.

## Executing

	Usage:
	    sshRemoteControl.py <file>
	        <file> is the XML or JSON task file.
	        It must end in either .xml or .json

	    sshRemoteControl.py -h|--help


# Contributing

## Version Changelog

### 1.0

 * Uses Paramiko instead of PExpect
 * Added JSON Support
 * Added Devices classes

### TODO

 * Multiple parallel connections to devices
 * Support for YAML files
 * Support for INI files
 * Support for SSH key-based authentication
 * Support for TELNET as fallback of SSH

## License

Author: Jose Ignacio Tamayo Segarra.

This code is delivered AS IS, no warranty is provided neither support nor maintenance.

This code is free, under MIT licence [Reference](http://choosealicense.com/licenses/) [MIT](http://www.tawesoft.co.uk/kb/article/mit-license-faq).
