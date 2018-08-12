
from grovepi import *
from grove_rgb_lcd import *
from time import sleep
from math import isnan
import grovepi

import random
import time
import sys

import requests

dht_sensor_port = 3 # connect the DHt sensor to port 3
dht_sensor_type = 0 # use 0 for the blue-colored sensor and 1 for the white-colored sensor
gas_sensor = 0

#
import iothub_client
# pylint: disable=E0611
from iothub_client import IoTHubClient, IoTHubClientError, IoTHubTransportProvider, IoTHubClientResult
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue

# The device connection string to authenticate the device with your IoT hub.
# Using the Azure CLI:
# az iot hub device-identity show-connection-string --hub-name {YourIoTHubName} --device-id MyNodeDevice --output table
CONNECTION_STRING = "HostName=agentOfChange-iotHub.azure-devices.net;DeviceId=sensor1;SharedAccessKey=KZVR9mk0GmScCdH5qYTHnApaS4SU3SRwLoPJh44WVxc="

# Using the MQTT protocol.
PROTOCOL = IoTHubTransportProvider.MQTT
MESSAGE_TIMEOUT = 10000

# Define the JSON message to send to IoT Hub.
TEMPERATURE = 20.0
HUMIDITY = 60
MSG_TXT = "{\"temperature\": %.2f,\"humidity\": %.2f,\"water_leak\": %d,\"gas_sensor_val\": %.2f,\"latitude\":40.7343436,\"longitude\":-73.9909269,\"device_id\":0}"

def send_confirmation_callback(message, result, user_context):
    print ( "IoT Hub responded to message with status: %s" % (result) )

def iothub_client_init():
    # Create an IoT Hub client
    client = IoTHubClient(CONNECTION_STRING, PROTOCOL)
    return client

def send_message(message_text):
    print(message_text)
    
def iothub_client_telemetry_sample_run(client,temperature,humidity,water_leak,gas_sensor_val):

    try:
        #print ( "IoT Hub device sending periodic messages, press Ctrl-C to exit" )

        # Build the message with simulated telemetry values.
        #temperature = TEMPERATURE + (random.random() * 15)
        #humidity = HUMIDITY + (random.random() * 20)
        msg_txt_formatted = MSG_TXT % (temperature, humidity, water_leak, gas_sensor_val)
        message = IoTHubMessage(msg_txt_formatted)

        # Add a custom application property to the message.
        # An IoT hub can filter on these properties without access to the message body.
        prop_map = message.properties()
        if temperature > 30:
                prop_map.add("temperatureAlert", "true")
        else:
                prop_map.add("temperatureAlert", "false")

        # Send the message.
        print( "Sending message: %s" % message.get_string() )
        client.send_event_async(message, send_confirmation_callback, None)
    
    except IoTHubError as iothub_error:
        print ( "Unexpected error %s from IoTHub" % iothub_error )
        return
    except KeyboardInterrupt:
        print ( "IoTHubClient sample stopped" )

#
water_sensor = 7
grovepi.pinMode(gas_sensor,"INPUT")
grovepi.pinMode(water_sensor,"INPUT")

# set green as backlight color
# we need to do it just once
# setting the backlight color once reduces the amount of data transfer over the I2C line
setRGB(0,255,0)

post_msg_water = False

post_msg_smoke = False

client = iothub_client_init()

while True:
	try:
                # Get sensor value
                sensor_value = grovepi.analogRead(0)

                # Calculate gas density - large value means more dense gas
                density = (float)(sensor_value / 1024)

                #print("sensor_value =", sensor_value, " density =", density)
                water_sensor_val= grovepi.digitalRead(water_sensor)

		[ temp,hum ] = dht(dht_sensor_port,dht_sensor_type)

		t = str(temp)
		h = str(hum)
                g = str(sensor_value)
                

        # instead of inserting a bunch of whitespace, we can just insert a \n
        # we're ensuring that if we get some strange strings on one line, the 2nd one won't be affected
               
                if(water_sensor_val == 1):
                 water_leak = 0
                 if (post_msg_water == True):
                  send_message("Water Leak alert has been resolved.")
                 post_msg_water = False
                else:
                 water_leak = 1
                 if (post_msg_water == False):
                  send_message("Water Leak Detected!")
                  post_msg_water = True

        # Check Smoke Sensor Value
        
                if(float(g) < 100):
                 if (post_msg_smoke == True):
                  send_message("Gas Leak alert has been resolved.")
                 post_msg_smoke = False
                else:
                 if (post_msg_smoke == False):
                  send_message("Gas Leak Detected!")
                  post_msg_smoke = True


            # Check temp value
                                
                if (t != "nan" and h != "nan"):
                 iothub_client_telemetry_sample_run(client, float(t),float(h),water_leak, float(g))       
		 setText_norefresh("Temp:" + t + "C\n" + "Hum :" + h + "% Gas "+g)

                sleep(1)



	except (IOError, TypeError) as e:
		print(str(e))
		# and since we got a type error
		# then reset the LCD's text
		setText("")

	except KeyboardInterrupt as e:
		print(str(e))
                print(" exit ")
		# since we're exiting the program
		# it's better to leave the LCD with a blank text
		setText("")
		break

	# wait some time before re-updating the LCD
	#sleep(5)
