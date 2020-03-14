import kivy
from kivy.app import App 
from kivy.uix.floatlayout import FloatLayout
from kivy.config import Config
from kivy.properties import ObjectProperty 


Config.set('graphics', 'width', '750')
Config.set('graphics', 'height', '600')

# from kivy.core.window import window  To set background to white
# Window.clearcolor = (1, 1, 1, 1)


class Mainscreen(FloatLayout):

	def Search(self):
		print("Searching")


class UIApp(App):
	def build(self):
		return Mainscreen()

	



if __name__ == "__main__":
	UIApp().run()



   

