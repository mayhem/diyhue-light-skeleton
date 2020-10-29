#!/usr/bin/env python3

import abc
import sys
import socket
import json
from random import seed
import math
import traceback
from time import sleep
import paho.mqtt.client as mqtt
from colorsys import hsv_to_rgb, rgb_to_hsv, rgb_to_hsv

AUTODISCOVERY_TOPIC = "homeassistant/light/example/light/config"

# Styled like an autodiscovery topic response
CONFIG = {  
    "brightness" : True,
    "xy" : True,
    "schema" : "json",
    "command_topic" : "example/set",
    "state_topic" : "example/state",
    "json_attributes_topic" : "example/state",
    "brightness_scale": 254,
    "name" : "example LED light",
    "unique_id" : "f3dfb856-1479-4094-8ded-6e252d73d24e",
    "device" : {
        "identifiers" : [ "example" ],
        "name" : "example LED light",
        "sw_version" : "0.69 beta alpha",
        "model" : "Mayhems personal silly lighting projects",
        "manufacturer" : "Mayhem & Chaos Labs"
    }
}

light_instance = None

def on_message(mqttc, user_data, msg):
    print("got message %s" % msg.topic)
    try:
        if light_instance:
            light_instance._handle_message(mqttc, msg)
    except Exception as err:
        traceback.print_exc(file=sys.stdout)


class Light(object):

    def __init__(self):
        self.state = False
        self.brightness = 0
        self.x = 0
        self.y = 0

        self.mqttc = None

    def publish(self, topic, payload):
        if not self.mqttc:
            return

        self.mqttc.publish(topic, payload)

    def publish_status(self):
        msg =  { 
                    "state" : "ON" if self.state else "OFF",
                    "brightness" : self.brightness,
                    "color" : {
                        "x" : self.x,
                        "y" : self.y
                    }
                }
        self.publish(CONFIG['state_topic'], json.dumps(msg))

    def set_state(self, state):
        self.state = state

    def set_brightness(self, brightness):
        self.brightness = brightness

    def _handle_message(self, mqttc, msg):

        payload = str(msg.payload, 'utf-8')
        print(msg.topic)

        data = json.loads(payload)
        if msg.topic != CONFIG['command_topic']:
            return

        print(data)

        if 'state' in data:
            if data['state'] == "ON":
                self.state = True
            elif data['state'] == "OFF":
                self.state = False

        if 'brightness' in data:
            self.brightness = data['brightness']

        if 'color' in data:
            self.x = data['color']['x']
            self.y = data['color']['y']

        self.publish_status()


    def setup(self):

        self.mqttc = mqtt.Client()
        self.mqttc.on_message = on_message
        self.mqttc.connect("10.1.1.2", 1883, 60)

        print("subscribe ", CONFIG['command_topic'])
        self.mqttc.subscribe(CONFIG['command_topic'], 0)
        self.publish(AUTODISCOVERY_TOPIC, json.dumps(CONFIG))
        sleep(1)
        self.publish_status()


if __name__ == "__main__":
    seed()
    a = Light()
    light_instance = a
    a.setup()
    a.set_state(True)
    try:
        a.mqttc.loop_forever()
    except KeyboardInterrupt:
        a.mqttc.disconnect()
