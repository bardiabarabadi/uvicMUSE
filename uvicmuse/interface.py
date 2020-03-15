
import time
import subprocess 
from os import getpid
from multiprocessing import Process
import sys
import pygatt
from kivy.lang import Builder
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivy.config import Config
Config.set('graphics', 'width', '750')
Config.set('graphics', 'height', '600')
from kivy.uix.image import Image
from kivy.graphics import *
from kivy.uix.checkbox import CheckBox
from kivy.uix.switch import Switch
from kivy.uix.recycleview import RecycleView
from uvicmuse import muse
from uvicmuse import helper
from functools import partial




def is_data_valid(data, timestamps):
    if timestamps == 0.0:
        return False

    for i in range(data.shape[0] - 1):
        if data[i] == 0.0:
            return False
    return True

def find_muse(name=None):
    muses = list_muses()
    if name:
        for muse in muses:
            if muse['name'] == name:
                return muse
    elif muses:
        return muses[0]


def list_muses(backend='bgapi', interface=None):
    backend = helper.resolve_backend(backend)

    if backend == 'gatt':
        interface = interface or 'hci0'
        adapter = pygatt.GATTToolBackend(interface)
    elif backend == 'bluemuse':
        return
    else:
        adapter = pygatt.BGAPIBackend(serial_port=interface)

    adapter.start()
    print('Searching for Muses, this may take up to 10 seconds...                                 ')
    devices = adapter.scan(timeout=10.5)
    adapter.stop()
    muses = []

    for device in devices:
        if device['name'] and 'Muse' in device['name']:
            muses = muses + [device]

    if (muses):
        for muse in muses:
            print('Found device %s, MAC Address %s' %
                  (muse['name'], muse['address']))
    else:
        print('No Muses found.')

    return muses


class UVicMuse(FloatLayout):

	def __init__(self, **kwargs):
		super(UVicMuse,self).__init__(**kwargs)

		self.muses = []
		self.sock = None
		self.muse = None
		self.did_connect = False
		self.udp_address = ""
		self.connected_address = ""
		self.backend = 'bgapi'

		#create labels and buttons
		self.img = Image(source = 'logo.png')
		self.list_label1 = Label(text = "", color = (0,0,0,1), font_size = 17)
		self.list_label2 = Label(text = "", color = (0,0,0,1), font_size = 17)
		self.status_label = Label(text = "Press Search to Look For Muse", color = (.05,.5,.95,1), font_size = 14)
		self.port_label = Label(text = "Port", color = (.3,.3,1,1), font_size = 14)
		self.host_label = Label(text = "Host", color = (.3,.3,1,1), font_size = 14)
		self.canvas.add(Rectangle(size=(570, 250), pos = (25,225), color = (1,1,1,1)))
		self.search_button = Button(text = "Search", size_hint=(.15, .08),pos_hint={'x':0.82, 'y':.65}, background_color = (.05,.5,.95,1), on_release = self.search_logic, on_press = self.update_status_search)
		self.start_stream_button = Button(text = "Start Stream", size_hint=(.15, .08),pos_hint={'x':0.82, 'y':.55}, background_color = (.05,.5,.95,1))
		self.stop_stream_button = Button(text = "Stop Stream", size_hint=(.15, .08),pos_hint={'x':0.82, 'y':.45}, background_color = (.05,.5,.95,1))


		self.connect_button1 = Button(text = "Connect", size_hint=(.112, .059),pos_hint={'x':.56, 'y':.725}, background_color = (.05,.5,.95,1))
		self.connect_button1.bind(on_press = partial(self.update_status_connect, 'connect1'), on_release = partial(self.connect, 'connect1'))

		self.disconnect_button1 = Button(text = "Disconnect", size_hint=(.112, .059),pos_hint={'x':.68, 'y':.725}, background_color = (.05,.5,.95,1))
		self.disconnect_button1.bind(on_press = partial(self.update_status_connect, 'disconnect1'), on_release = partial(self.connect, 'disconnect1'))

		self.connect_button2 = Button(text = "Connect", size_hint=(.112, .059),pos_hint={'x':.56, 'y':.59}, background_color = (.05,.5,.95,1))
		self.connect_button2.bind(on_press = partial(self.update_status_connect, 'connect2'), on_release = partial(self.connect, 'connect2'))

		self.disconnect_button2 = Button(text = "Disconnect", size_hint=(.112, .059),pos_hint={'x':.68, 'y':.59}, background_color = (.05,.5,.95,1))
		self.disconnect_button2.bind(on_press = partial(self.update_status_connect, 'disconnect2'), on_release = partial(self.connect, 'disconnect2'))



		self.showConfig_button = Button(text = "Show Configuration", font_size = 12, size_hint=(.17, .05),pos_hint={'x':0.03, 'y':.22}, background_color = (.05,.5,.95,1))
		self.hideConfig_button = Button(text = "Hide Configuration", font_size = 12, size_hint=(.17, .05),pos_hint={'x':.22, 'y':.22}, background_color = (.05,.5,.95,1))
		self.LSL_checkbox = CheckBox(active = False)
		self.EEG_checkbox = CheckBox(active = True)
		self.PPG_checkbox = CheckBox(active = False)
		self.ACC_checkbox = CheckBox(active = True) 
		self.GYRO_checkbox = CheckBox(active = True)
		self.lowpass_checkbox = CheckBox(active = False) 
		self.highpass_checkbox = CheckBox(active = True)


		#add widgets
		self.add_widget(self.img)
		self.add_widget(self.search_button)
		self.add_widget(self.start_stream_button)
		self.add_widget(self.stop_stream_button)
		self.add_widget(self.status_label)

		self.add_widget(self.port_label)
		self.add_widget(self.host_label)

		#positions
		self.img.pos = (0,220)
		self.status_label.pos = (-250, -90)
		self.port_label.pos = (-320, -150)
		self.host_label.pos = (-225, -150)

		#logic
	def update_status_connect(self,button, event):
		if(button) == 'connect1':
			self.status_label.text = "Connecting to " + str(self.muses[0]['name'] + "       ")
		if(button) == 'disconnect1':
			self.status_label.text = "Disconnecting from " + str(self.muses[0]['name'] + "       ")
		if(button) == 'connect2':
			self.status_label.text = "Connecting to " + str(self.muses[1]['name'] + "       ")
		if(button) == 'disconnect2':
			self.status_label.text = "Disconnecting from " + str(self.muses[1]['name'] + "       ")



	def connect(self, button, event):
		if(button) == "connect1":
			print("connect1")
		if(button) == "disconnect1":			#change to actually connect and disconenct
			print("disconnect1")
		if(button) == "connect2":
			print("connect2")
		if(button) == "disconnect2":
			print("disconnect2")						


	def update_status_search(self, event,):
		self.status_label.text = "Searching For Muse, Please Wait"

	def search_logic(self,event):
		self.muses = list_muses()
		devices = (len(self.muses))
		if(devices) == 1:
			self.status_label.text = " 1 device was found                            "
		else:
			self.status_label.text = str(devices) + " devices were found                        "
		if(devices) == 1:
			self.add_widget(self.list_label1)
			self.list_label1.pos = (-170, 150)
			self.list_label1.text = str(self.muses[0]['name']) + ", Mac Address " + str(self.muses[0]['address'])
			self.add_widget(self.connect_button1)
			self.add_widget(self.disconnect_button1)
		if(devices) == 2:		
			self.add_widget(self.list_label1)
			self.list_label1.pos = (-170, 150)
			self.list_label1.text = str(self.muses[0]['name']) + ", Mac Address " + str(self.muses[0]['address'])			
			self.add_widget(self.connect_button1)
			self.add_widget(self.disconnect_button1)
			self.add_widget(self.list_label2)
			self.list_label2.pos = (-170, 70)
			self.list_label2.text = str(self.muses[1]['name']) + ", Mac Address " + str(self.muses[1]['address'])			
			self.add_widget(self.connect_button2)
			self.add_widget(self.disconnect_button2)

	



class app1(App):
    def build(self):
        return UVicMuse()
if __name__=="__main__":
     app1().run()





		# self.LSL_label = Label(text = "LSL", color = (.3,.3,1,1), font_size = 14)
		# self.EEG_label = Label(text = "EEG", color = (.3,.3,1,1), font_size = 14)
		# self.PPG_label = Label(text = "PPG", color = (.3,.3,1,1), font_size = 14)
		# self.ACC_label = Label(text = "ACC", color = (.3,.3,1,1), font_size = 14)
		# self.GYRO_label = Label(text = "GYRO", color = (.3,.3,1,1), font_size = 14)

		# self.lowpass_label = Label(text = "Lowpass Filter", color = (.3,.3,1,1), font_size = 14)
		# self.highpass_label = Label(text = "Highpass Filter", color = (.3,.3,1,1), font_size = 14)

		# self.lowpass_cutoff = Label(text = "Cutoff:", color = (.3,.3,1,1), font_size = 14)
		# self.highpass_cutoff = Label(text = "Cutoff:", color = (.3,.3,1,1), font_size = 14)

		# self.add_widget(self.LSL_label)
		# self.add_widget(self.EEG_label)
		# self.add_widget(self.PPG_label)
		# self.add_widget(self.ACC_label)
		# self.add_widget(self.GYRO_label)

		# self.add_widget(self.LSL_checkbox)
		# self.add_widget(self.EEG_checkbox)
		# self.add_widget(self.PPG_checkbox)
		# self.add_widget(self.ACC_checkbox)
		# self.add_widget(self.GYRO_checkbox)

		# self.add_widget(self.lowpass_label)
		# self.add_widget(self.highpass_label)

		# self.add_widget(self.lowpass_checkbox)
		# self.add_widget(self.highpass_checkbox)

		# self.add_widget(self.lowpass_cutoff)
		# self.add_widget(self.highpass_cutoff)

		# self.add_widget(self.test_switch)
		# self.add_widget(self.test_switch2)





		# self.LSL_label.pos = (-120, -150)
		# self.EEG_label.pos = (-20, -150)
		# self.PPG_label.pos = (80, -150)
		# self.ACC_label.pos = (180, -150)
		# self.GYRO_label.pos = (280, -150)


		# self.LSL_checkbox.pos = (-122, -170)
		# self.EEG_checkbox.pos = (-22, -170)
		# self.PPG_checkbox.pos = (82, -170)
		# self.ACC_checkbox.pos = (182, -170)
		# self.GYRO_checkbox.pos = (282, -170)

		# self.lowpass_label.pos = (-188, -230)
		# self.highpass_label.pos = (112 , -230)

		# self.lowpass_checkbox.pos = (-122, -230)
		# self.highpass_checkbox.pos = (182, -230)

		# self.lowpass_cutoff.pos = (-200,-250)
		# self.highpass_cutoff.pos = (100,-250)

		# self.test_switch2.pos = (-100, 100)