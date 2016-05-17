import time 
import socket
import datetime
import os
import RPi.GPIO as GPIO
import SimpleHTTPServer
import SocketServer
import Adafruit_GPIO.SPI as SPI
import Adafruit_MAX31855.MAX31855 as MAX31855
import threading

# Lol colin's here

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# TCP Connection Settings
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# the commented out IP address is the one I was using to test at home
# 0.0.0.0 is the setting you want to use to grab all IP's associated with the interfaces on the Pi
# leave port as 4 digit number as computer will not automatically allocate ports in this range
# leave BUF as 1024; this defines the size of the data that you will receive

print ("\nLaunch Control Server Initialized.")

#TCP_IP = "192.168.1.127"
TCP_IP = "0.0.0.0"
#TCP_IP = "10.240.232.136"
TCP_PORT = 5000
BUF = 1024

print ("Please connect client software to: %s at port: %d \n") % (TCP_IP, TCP_PORT)
print ("Waiting to establish connection........ \n")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP,TCP_PORT))
s.listen(1)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Pin Setup
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# All pins are set to use the broadcom numbering scheme on the raspberry pi
# Refer to this wiring standard when setting up or changing pins

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

ign1 = 18        # 18 is for the first ignitor
ign2 = 27        # 27 is for the second ignitor
vnts = 22        # 22 is the pin setup for the vents
main = 23        # 23 is the pin setup for the main valves
cam = 24         # 24 is for the HACK HD camera actuation
PoE_1 = 20		 # 20 is the PoE for Data Acquisition 1
PoE_2 = 21		 # 21 is the PoE for Data Acquisition 2	

GPIO.setup(ign1,GPIO.OUT)
GPIO.setup(ign2,GPIO.OUT)
GPIO.setup(vnts,GPIO.OUT)
GPIO.setup(main,GPIO.OUT) 
GPIO.setup(cam,GPIO.OUT) 
GPIO.setup(PoE_1,GPIO.OUT)
GPIO.setup(PoE_2,GPIO.OUT)

# set all pin outputs to false initially so that they do not
# actuate anything upon the program starting

GPIO.output(ign1,False)
GPIO.output(ign2,False)
GPIO.output(vnts,False)
GPIO.output(main,False)
GPIO.output(cam,False)
GPIO.output(PoE_1,False)
GPIO.output(PoE_2,False)

b_wire = 17      # 17 is the pin for the breakwire
r_main = 13       # 13 is the pin for the MPV reed switch
r_LOX = 19       # 19 is the pin for the LOX reed switch
r_kero = 26      # 26 is the pin for the kero reed switch

GPIO.setup(b_wire,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     # this pin is setup to control the breakwire
GPIO.setup(r_main,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     # setup for the main fuel feedback signal
GPIO.setup(r_LOX,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)      # setup for the LOX feedback signal
GPIO.setup(r_kero,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     # setup for the Kerosene feedback signal

# setup for the thermocouple
# these pins should not change, recommended pins that should be used are set

CLK = 11
CS = 8
DO = 9
sensor = MAX31855.MAX31855(CLK, CS, DO)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Sensor Reading
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

def Thermo_read():

	# This function contains a simple C to F converter function as well as the loop to 
	# reed the temperatures and to send it off as data over the TCP connection

	def c_to_f(c):

		return c * 9.0 / 5.0 + 32.0

	while True:		

		temp = sensor.readTempC()
		internal = sensor.readInternalC()
		Temperature = c_to_f(temp)
		conn.send(str(Temperature))

		return

def Breakwire_read():

	# Breakwire input is read here. If the input is true, this means that the connection 
	# is intact and that the breakwire has not been broken yet.
	# The state of the breakwire is sent over the TCP connection

		if GPIO.input(b_wire) == True:
			bwire = 'Intact'
			conn.send(str(bwire))
		elif GPIO.input(b_wire) == False:
			bwire = 'Broken'
			conn.send(str(bwire))
		return

def Main_Valve_Sensor():

	# Function that reads the magnetic reed switch on board the rocket at the main fuel valves

		if GPIO.input(r_main) == True:
			main_status = 'Open'
			conn.send(str(main_status))
		elif GPIO.input(r_main) == False:
			main_status = 'Closed'
			conn.send(str(main_status))
		return

def LOX_Valve_Sensor():

	# Function that reads the magnetic reed switch on board the rocket at the LOX valve

		if GPIO.input(r_LOX) == True:
			LOX_status = 'Open'
			conn.send(str(LOX_status))
		elif GPIO.input(r_LOX) == False:
			LOX_status = 'Closed'
			conn.send(str(LOX_status))
		return

def Kero_Valve_Sensor():

	# Function that reads the magnetic reed switch on board the rocket at the Kerosene valve

		if GPIO.input(r_kero) == True:
			kero_status = 'Open'
			conn.send(str(kero_status))
		elif GPIO.input(r_kero) == False:
			kero_status = 'Closed'
			conn.send(str(kero_status))
		return

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Relay and Communication
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# All of the functions for actuating are pretty straight forward and appropriately
# named. These functions set the correct pins to high or low depending on the state at
# which we request them to be turned to. Abort controls multiple pins because this state
# requires us to close the main valve and turn the ignitor signal off while opening the 
# vents

def PoE_Switch_On():
	GPIO.output(PoE_1,True)
	GPIO.output(PoE_2,True)
	conn.send("Switching power to onboard control.")
	return

def PoE_Switch_Off():
	GPIO.output(PoE_1,False)
	GPIO.output(PoE_2,False)
	conn.send("Switching power to launch control system.")
	return

def ignitor_one_on():

	# Ignitor one has default control over both ignitors. To change this, comment out the the line of 
	# GPIO.output(27,True)

	GPIO.output(ign1,True)
	GPIO.output(ign2,True)
	conn.send("Ignitor 1 Lit") 
	return

def ignitor_one_off():

	# Ignitor one has default control over both ignitors. To change this, comment out the the line of 
	# GPIO.output(27,False)

	GPIO.output(ign1,False)
	GPIO.output(ign2,False)
	conn.send("Ignitor 1 Off")
	return

def ignitor_two_on():

	GPIO.output(ign2,True)
	conn.send("Ignitor 2 Lit")
	return

def ignitor_two_off():

	GPIO.output(ign2,False)
	conn.send("Ignitor 2 Off")
	return

def main_open():

	GPIO.output(main,True)
	conn.send("Main Valve Opened")
	return

def main_close():

	GPIO.output(main,False)
	conn.send("Main Valve Closed")
	return

def vent_open():

	GPIO.output(vnts,True)
	conn.send("Vents Opened")
	return

def vent_close():

	GPIO.output(vnts,False)
	conn.send("Vents Closed")
	return

def launch():

	GPIO.output(main,True)
	conn.send("Launch!")
	return

def abort():

	GPIO.output(ign1,False)
	GPIO.output(ign2,False)
	GPIO.output(main,False)
	GPIO.output(vnts,False)
	conn.send("Launch Aborted")
	return

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Main Loop
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# Our main loop is the listener or the TCP connection. It listens for 'data' and 
# uses this data to analyze what is being requested on the Launch Control Client. Data
# that is receieved requesting valve or ignitor actuation simply jumps into the correct
# function listed above. If sensor information is requested, new threads are started that
# use the target function specified to send sensor information back to the client software.

while True:

	conn,addr = s.accept()

	print ("Connection established.")
	print 'Connection address: ',addr
	print ("Awaiting commands... \n")

	while True:
		data = conn.recv(BUF)
		if not data: break
		
		if 'rocket_power' in data:
			print "Received data: ", data
			PoE_Switch_On()

		elif 'esb_power' in data:
			print "Received data: ", data
			PoE_Switch_Off()
		
		elif 'ign1_on' in data:
			print "Received data: ", data
			ignitor_one_on()
		
		elif 'ign1_off' in data:
			print "Received data: ", data
			ignitor_one_off()

		elif 'ign2_on' in data:
			print "Received data: ", data
			ignitor_two_on()
		
		elif 'ign2_off' in data:
			print "Received data: ", data
			ignitor_two_off()
		
		elif 'vents_open' in data:
			print "Received data: ", data
			vent_open()

		elif 'vents_close' in data:
			print "Received data: ", data
			vent_close()
		
		elif 'main_open' in data:
			print "Received data: ", data
			main_open()

		elif 'main_close' in data:
			print "Received data: ", data
			main_close()

		elif 'launch' in data:
			print "Received data: ", data
			launch()

		elif 'abort' in data:
			print "Received data: ", data
			abort()

		elif 'disconnect' in data:
			print"Received data: ", data
			conn.send("Disconnecting from server.")
			print("Connection closing... \n")
			conn.close()
			break
			
		elif 'temp_status' in data:
			try:
				thermo_trd = threading.Thread(target=Thermo_read())
				thermo_trd.start()
			except Exception, e:
				raise e

		elif 'bwire_status' in data:
			try:
		 		bwire_trd = threading.Thread(target=Breakwire_read())
				bwire_trd.start()
			except Exception, e:
				raise e

		elif 'main_status' in data:
			try:
				r_main_trd = threading.Thread(target=Main_Valve_Sensor())
				r_main_trd.start()
			except Exception, e:
				raise e

		elif 'kero_status' in data:
			try:
				r_kero_trd = threading.Thread(target=Kero_Valve_Sensor())
				r_kero_trd.start()
			except Exception, e:
				raise e

		elif 'LOX_status' in data:
			try:
				r_LOX_trd = threading.Thread(target=LOX_Valve_Sensor())
				r_LOX_trd.start()
			except Exception, e:
				raise e

	#print("connection closing... \n")
	#conn.close()
		
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# End Script
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#