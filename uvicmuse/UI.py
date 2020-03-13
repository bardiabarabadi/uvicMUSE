\
import time
import subprocess 
from os import getpid
from multiprocessing import Process
import sys

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





class UVicMuse(FloatLayout):

	def __init__(self, **kwargs):
		super(UVicMuse,self).__init__(**kwargs)

		#create labels and buttons
		self.img = Image(source = 'logo.png')
		self.list_label = Label(text = "Muse Name: Muse-C052", color = (0,0,0,1), font_size = 17)
		self.status_label = Label(text = "Status: ", color = (0,0,0,1), font_size = 14)
		self.port_label = Label(text = "Port", color = (.3,.3,1,1), font_size = 14)
		self.host_label = Label(text = "Host", color = (.3,.3,1,1), font_size = 14)
		self.LSL_label = Label(text = "LSL", color = (.3,.3,1,1), font_size = 14)
		self.EEG_label = Label(text = "EEG", color = (.3,.3,1,1), font_size = 14)
		self.PPG_label = Label(text = "PPG", color = (.3,.3,1,1), font_size = 14)
		self.ACC_label = Label(text = "ACC", color = (.3,.3,1,1), font_size = 14)
		self.GYRO_label = Label(text = "GYRO", color = (.3,.3,1,1), font_size = 14)

		self.lowpass_label = Label(text = "Lowpass Filter", color = (.3,.3,1,1), font_size = 14)
		self.highpass_label = Label(text = "Highpass Filter", color = (.3,.3,1,1), font_size = 14)

		self.lowpass_cutoff = Label(text = "Cutoff:", color = (.3,.3,1,1), font_size = 14)
		self.highpass_cutoff = Label(text = "Cutoff:", color = (.3,.3,1,1), font_size = 14)
		


		


		self.canvas.add(Rectangle(size=(570, 250), pos = (25,225), color = (1,1,1,1)))
		self.canvas.add(Rectangle(size=(570, 25), pos = (25,185), color = (1,1,1,1)))

		self.canvas.add(Rectangle(size=(60, 20), pos = (25,120), color = (1,1,1,1)))
		self.canvas.add(Rectangle(size=(75, 20), pos = (115,120), color = (1,1,1,1)))


		

		self.search_button = Button(text = "Search", size_hint=(.15, .08),pos_hint={'x':0.82, 'y':.65}, background_color = (.05,.5,.95,1))
		self.start_stream_button = Button(text = "Start Stream", size_hint=(.15, .08),pos_hint={'x':0.82, 'y':.55}, background_color = (.05,.5,.95,1))
		self.stop_stream_button = Button(text = "Stop Stream", size_hint=(.15, .08),pos_hint={'x':0.82, 'y':.45}, background_color = (.05,.5,.95,1))
		self.connect_button = Button(text = "Connect", size_hint=(.112, .059),pos_hint={'x':.56, 'y':.725}, background_color = (.05,.5,.95,1))
		self.disconnect_button = Button(text = "Disconnect", size_hint=(.112, .059),pos_hint={'x':.68, 'y':.725}, background_color = (.05,.5,.95,1))

		# self.showConfig_button = Button(text = "Show Configuration", font_size = 12, size_hint=(.17, .05),pos_hint={'x':0.03, 'y':.22}, background_color = (.05,.5,.95,1))
		# self.hideConfig_button = Button(text = "Hide Configuration", font_size = 12, size_hint=(.17, .05),pos_hint={'x':.22, 'y':.22}, background_color = (.05,.5,.95,1))

		self.LSL_checkbox = CheckBox(active = False)
		self.EEG_checkbox = CheckBox(active = True)
		self.PPG_checkbox = CheckBox(active = False)
		self.ACC_checkbox = CheckBox(active = True) 
		self.GYRO_checkbox = CheckBox(active = True)

		self.lowpass_checkbox = CheckBox(active = False) 
		self.highpass_checkbox = CheckBox(active = True)
		
		self.test_switch = Switch()
		self.test_switch2 = Switch()


		#add widgets
		self.add_widget(self.img)
		self.add_widget(self.list_label)
		self.add_widget(self.search_button)
		self.add_widget(self.start_stream_button)
		self.add_widget(self.stop_stream_button)
		self.add_widget(self.status_label)
		self.add_widget(self.connect_button)
		self.add_widget(self.disconnect_button)
		# self.add_widget(self.showConfig_button)
		# self.add_widget(self.hideConfig_button)
		self.add_widget(self.port_label)
		self.add_widget(self.host_label)
		self.add_widget(self.LSL_label)
		self.add_widget(self.EEG_label)
		self.add_widget(self.PPG_label)
		self.add_widget(self.ACC_label)
		self.add_widget(self.GYRO_label)

		self.add_widget(self.LSL_checkbox)
		self.add_widget(self.EEG_checkbox)
		self.add_widget(self.PPG_checkbox)
		self.add_widget(self.ACC_checkbox)
		self.add_widget(self.GYRO_checkbox)

		self.add_widget(self.lowpass_label)
		self.add_widget(self.highpass_label)

		self.add_widget(self.lowpass_checkbox)
		self.add_widget(self.highpass_checkbox)

		self.add_widget(self.lowpass_cutoff)
		self.add_widget(self.highpass_cutoff)

		self.add_widget(self.test_switch)
		self.add_widget(self.test_switch2)

		
		
		#positions
		self.img.pos = (0,220)
		self.list_label.pos = (-250,160)
		self.status_label.pos = (-320, -103)
		self.port_label.pos = (-320, -150)
		self.host_label.pos = (-225, -150)
		self.LSL_label.pos = (-120, -150)
		self.EEG_label.pos = (-20, -150)
		self.PPG_label.pos = (80, -150)
		self.ACC_label.pos = (180, -150)
		self.GYRO_label.pos = (280, -150)


		self.LSL_checkbox.pos = (-122, -170)
		self.EEG_checkbox.pos = (-22, -170)
		self.PPG_checkbox.pos = (82, -170)
		self.ACC_checkbox.pos = (182, -170)
		self.GYRO_checkbox.pos = (282, -170)

		self.lowpass_label.pos = (-188, -230)
		self.highpass_label.pos = (112 , -230)

		self.lowpass_checkbox.pos = (-122, -230)
		self.highpass_checkbox.pos = (182, -230)

		self.lowpass_cutoff.pos = (-200,-250)
		self.highpass_cutoff.pos = (100,-250)

		self.test_switch2.pos = (-100, 100)



class app1(App):
    def build(self):
        return UVicMuse()
if __name__=="__main__":
     app1().run()
