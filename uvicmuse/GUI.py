import socket
import struct

from pylsl import StreamInfo
import pygatt
from functools import partial


from tkinter import ttk, font, messagebox
import tkinter as tk

from tkinter import *
from PIL import ImageTk, Image
import pygubu








class UVicMuse:

    def __init__(self, master):
        self.master = master
        self.log = "Welcome to UVicMUSE"
        self.muses = []
        self.sock = None
        self.muse = None
        self.did_connect = False
        self.udp_address = ()
        self.connected_address = ""
        self.backend = 'bgapi'  # TODO: Get this from user
        self.prv_ts = 0
        # 1: Create a builder
        self.builder = pygubu.Builder()

        # 2: Load an ui file
        self.builder.add_from_file('./interface2.ui')

        self.mainwindow = self.builder.get_object('Toplevel_1')
        self.refresh_btn = self.builder.get_object('Refresh')
        self.frame_list = self.builder.get_object("Frame_list")
        self.log_msg = self.builder.get_object("Label_2")
        self.img_lbl = self.builder.get_object("img_label")

        self.address_entry = self.builder.get_object("address_entry")
        self.port_entry = self.builder.get_object("port_entry")
        self.UDP_send_btn = self.builder.get_object("UDP_send_btn")
        self.UDP_stop_btn = self.builder.get_object("UDP_stop_btn")

        self.connect_btn = self.builder.get_object("Connect")
        self.disconnect_btn = self.builder.get_object("Disconnect")

        self.img = Image.open('./logo.png')
        self.image = self.img.resize((372, 102))
        self.background_image = ImageTk.PhotoImage(self.image)
        self.img_lbl.configure(image=self.background_image)

        list_font = font.Font(family='Helvetica', size=12)  # , weight='bold')

        self.frame_list.yScroll = tk.Scrollbar(self.frame_list, orient=tk.VERTICAL)
        self.frame_list.yScroll.grid(row=0, column=1, sticky=tk.N + tk.S)

        self.frame_list.xScroll = tk.Scrollbar(self.frame_list, orient=tk.HORIZONTAL)
        self.frame_list.xScroll.grid(row=1, column=0, sticky=tk.E + tk.W)

        self.frame_list.listbox = tk.Listbox(self.frame_list, font=list_font,
                                             xscrollcommand=self.frame_list.xScroll.set,
                                             yscrollcommand=self.frame_list.yScroll.set)
        self.frame_list.listbox.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
        self.frame_list.xScroll['command'] = self.frame_list.listbox.xview
        self.frame_list.yScroll['command'] = self.frame_list.listbox.yview

        self.frame_list.listbox.config(width=70, height=15)
        self.frame_list.listbox.pack()

        self.frame_list.listbox.insert(END, " Refresh to get a list of MUSEs ")

      

        self.UDP_stop_btn.configure(state=DISABLED)
        self.UDP_stop_btn.update_idletasks()

        self.UDP_send_btn.configure(state=DISABLED)
        self.UDP_send_btn.update_idletasks()

        self.disconnect_btn.configure(state=DISABLED)
        self.disconnect_btn.update_idletasks()

        self.connect_btn.configure(state=DISABLED)
        self.connect_btn.update_idletasks()

        
        self.master.resizable(True, True)

    

root = Tk()
my_gui = UVicMuse(root)
root.mainloop()