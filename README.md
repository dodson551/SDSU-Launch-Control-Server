## SDSU-Launch-Control-Server

Python server code for SDSU RP LCS. Pull from this repo to update RPi w/ latest server software.

### Getting Started

The process for connecting to your RPi on Windows and Mac OSX is slightly different. 

### Windows

Download and install [Putty]. This will allow you to SSH into your RPi from your windows desktop.

[![Putty Screenshot](artwork/thumb_putty.png?raw=true)](artwork/putty.png?raw=true)

From here, enter IP or hostname of Pi and click 'Open'.

Log on to RPi using username and password. By default these are _pi_ and _raspberry_.

### Mac OSX

Run terminal and enter:
```
ssh pi@raspberrypi_hostname
```
_Where `raspberrypi_hostname` should be replaced with the IP Address of your RPi, or its hostname._

Log on to RPi using username and password. By default these are _pi_ and _raspberry_.

### Installation

Once logged on to your RPi, run this command from the home directory:
```
wget https://goo.gl/y74AJw && sudo python Launch_Control_Server.py
```
This command will install the Launch Control Server code in your home directory. The `&& sudo python Launch_Control_Server.py` will run the program after the installation is complete. 

### Usage

If you wish to run the program at any time, run this command from your home directory:
```
sudo python Launch_Control_Server.py
```
To quit the program, hit Ctrl+C to exit.

### Testing

Information on how to test here.

[Putty]: http://www.putty.org/
