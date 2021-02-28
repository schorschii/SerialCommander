#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from os import path
from pathlib import Path
from functools import partial
import json
import glob
import time
import platform
import serial
import sys

class SixledsAboutWindow(QDialog):
	def __init__(self, *args, **kwargs):
		super(SixledsAboutWindow, self).__init__(*args, **kwargs)
		self.InitUI()

	def InitUI(self):
		self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
		self.buttonBox.accepted.connect(self.accept)

		self.layout = QVBoxLayout(self)

		labelAppName = QLabel(self)
		labelAppName.setText(self.parentWidget().PRODUCT_NAME + " v" + self.parentWidget().PRODUCT_VERSION)
		labelAppName.setStyleSheet("font-weight:bold")
		labelAppName.setAlignment(Qt.AlignCenter)
		self.layout.addWidget(labelAppName)

		labelCopyright = QLabel(self)
		labelCopyright.setText(
			"<br>"
			"© 2021 <a href='https://github.com/schorschii'>Georg Sieber</a>"
			"<br>"
			"<br>"
			"GNU General Public License v3.0"
			"<br>"
			"<a href='"+self.parentWidget().PRODUCT_WEBSITE+"'>"+self.parentWidget().PRODUCT_WEBSITE+"</a>"
			"<br>"
		)
		labelCopyright.setOpenExternalLinks(True)
		labelCopyright.setAlignment(Qt.AlignCenter)
		self.layout.addWidget(labelCopyright)

		labelDescription = QLabel(self)
		labelDescription.setText(
			"""SerialCommander GUI allows you to send pre-defined commands over a serial port, e.g. to control digital projectors or to communicate with your arduino."""
		)
		labelDescription.setStyleSheet("opacity:0.8")
		labelDescription.setFixedWidth(350)
		labelDescription.setWordWrap(True)
		self.layout.addWidget(labelDescription)

		self.layout.addWidget(self.buttonBox)

		self.setLayout(self.layout)
		self.setWindowTitle("About")

class SerialCommanderTrayIcon(QSystemTrayIcon):
	TRAYICON_BASE64 = b"iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAdhwAAHYcBj+XxZQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAFGSURBVGiB7ZgxbsMwDEW/a6+BhcBjzpAzpFOvlLUXaA/UoblC5s4dHRDoakAZ4gBth9SflKoY5ttshBQ/vyw7BBxn2VSaoL7vN3VdvwJ4ArAy1vAF4K2qqn3bth9sMC1gLP4IYM3G/sFpGIZt13WfTNADu8rY+dTFA8C6aZoXNogWgMu2yQWdu1Es8mPPhxBUz9EVEYnfLls2XuPAXZFcgIjEX129ed+KO1Ca2QuYfILk2L+3mHq6zd4BF1AaF1AaF1AaF1AaF1AaRsAhVxGWtSYLiDE+q0pRwKxF/Z8VkXcAO7YgkkMI4XHqj6ln4D9cYNegJwqZXaC6DyhOoZwuaHKrZjqZXKC7DyjfAzlc0OZUT9USu6DqPmB4E6d0wZLLOtdM4YK6+4DxWyiFC9YcJgcA+7zIOt1e1NfoXeICSjN7AY6zdM4ms3HuqN4SwgAAAABJRU5ErkJggg=="

	def __init__(self, parent=None):
		pixmap = QPixmap()
		pixmap.loadFromData(QByteArray.fromBase64(self.TRAYICON_BASE64))
		QSystemTrayIcon.__init__(self, QIcon(pixmap), parent)
		self.activated.connect(parent.OnShow)
		self.CreateMenuItems(parent)

	def CreateMenuItems(self, parent):
		menu = QMenu(parent)

		for command in parent.commands:
			commandAction = QAction(command['title'], parent)
			commandAction.triggered.connect(partial(parent.SendCommand, command))
			menu.addAction(commandAction)

		menu.addSeparator()
		exitAction = QAction('Exit', parent)
		exitAction.triggered.connect(parent.OnQuit)
		exitAction = menu.addAction(exitAction)

		self.setContextMenu(menu)

class SerialCommanderMainWindow(QMainWindow):
	PRODUCT_NAME      = "SerialCommander"
	PRODUCT_VERSION   = "0.1.0"
	PRODUCT_WEBSITE   = "https://georg-sieber.de"

	configPath = str(Path.home())+'/.SerialCommander.json'
	config = {}

	serialConn  = None
	serialPorts = []
	serialPort  = None
	serialBaud  = 9600
	commands = [
		{'title':'Arduino LEDcontrol: OFF', 'description':'Turn LEDs off.', 'data':'00 00 00', 'type':'hex', 'port':None, 'baud':600},
		{'title':'Arduino LEDcontrol: RED', 'description':'Turn LEDs red.', 'data':'ff 00 00', 'type':'hex', 'port':None, 'baud':600},
		{'title':'Arduino LEDcontrol: GREEN', 'description':'Turn LEDs green.', 'data':'00 ff 00', 'type':'hex', 'port':None, 'baud':600},
		{'title':'Arduino LEDcontrol: BLUE', 'description':'Turn LEDs blue.', 'data':'00 00 ff', 'type':'hex', 'port':None, 'baud':600},

		{'title':'NEC Projector: ON', 'description':'Turn projector on.', 'data':'02 00 00 00 00 02', 'type':'hex', 'port':None, 'baud':38400},
		{'title':'NEC Projector: OFF', 'description':'Turn projector off.', 'data':'02 01 00 00 00 03', 'type':'hex', 'port':None, 'baud':38400},
	]

	def __init__(self, *args, **kwargs):
		super(SerialCommanderMainWindow, self).__init__(*args, **kwargs)
		self.serialPorts = self.GetSerialPorts()
		if(len(self.serialPorts) > 0): self.serialPort = self.serialPorts[0]
		self.LoadSettings()
		self.InitUI()

	def GetSerialPorts(self):
		if platform.system() == 'Windows':
			ports = ['COM%s' % (i + 1) for i in range(10)]
		elif platform.system() == 'Linux':
			ports = glob.glob('/dev/tty[A-Za-z]*')
		elif platform.system() == 'Darwin':
			ports = glob.glob('/dev/tty.*')
		else:
			raise EnvironmentError('Unsupported platform')
		result = []
		for port in ports:
			if("bluetooth" in port): continue # macOS
			try:
				s = serial.Serial(port)
				s.close()
				result.append(port)
			except(OSError, serial.SerialException):
				pass
		return result

	def LoadSettings(self):
		if(not path.isfile(self.configPath)): return

		with open(self.configPath) as f:
			self.config = json.load(f)

		if('DEFAULT' in self.config):
			if('port' in self.config['DEFAULT']): self.serialPort = self.config['DEFAULT']['port']
			if('baud' in self.config['DEFAULT']): self.serialBaud = int(self.config['DEFAULT']['baud'])

		if('COMMANDS' in self.config):
			self.commands = []
			for command in self.config['COMMANDS']:
				self.commands.append(command)

	def SaveSettings(self):
		if(not 'DEFAULT' in self.config): self.config['DEFAULT'] = {}
		self.config['DEFAULT']['port'] = self.serialPort
		self.config['DEFAULT']['baud'] = self.serialBaud

		self.config['COMMANDS'] = []
		for command in self.commands:
			self.config['COMMANDS'].append(command)

		with open(self.configPath, 'w') as json_file:
			json.dump(self.config, json_file, indent=4)

	def InitUI(self):
		# Menubar
		mainMenu = self.menuBar()

		# File Menu
		fileMenu = mainMenu.addMenu('&File')

		selectPortAction = QAction('Select Serial &Port...', self)
		selectPortAction.setShortcut('Ctrl+P')
		selectPortAction.triggered.connect(self.OnSelectSerialPort)
		fileMenu.addAction(selectPortAction)
		selectPortAction = QAction('Select &Baudrate...', self)
		selectPortAction.setShortcut('Ctrl+B')
		selectPortAction.triggered.connect(self.OnSelectSerialBaud)
		fileMenu.addAction(selectPortAction)

		fileMenu.addSeparator()
		addCommandAction = QAction('&Send Command...', self)
		addCommandAction.setShortcut('ENTER')
		addCommandAction.triggered.connect(self.OnSelectSerialPort)
		fileMenu.addAction(addCommandAction)

		fileMenu.addSeparator()
		addCommandAction = QAction('&Add Command...', self)
		addCommandAction.setShortcut('INS')
		addCommandAction.triggered.connect(self.OnSelectSerialPort)
		fileMenu.addAction(addCommandAction)
		removeCommandAction = QAction('&Remove Command', self)
		removeCommandAction.setShortcut('DEL')
		removeCommandAction.triggered.connect(self.OnSelectSerialBaud)
		fileMenu.addAction(removeCommandAction)

		fileMenu.addSeparator()
		addCommandAction = QAction('&Import Commands...', self)
		addCommandAction.setShortcut('Ctrl+I')
		addCommandAction.triggered.connect(self.OnSelectSerialPort)
		fileMenu.addAction(addCommandAction)
		removeCommandAction = QAction('&Export Commands...', self)
		removeCommandAction.setShortcut('Ctrl+E')
		removeCommandAction.triggered.connect(self.OnSelectSerialBaud)
		fileMenu.addAction(removeCommandAction)

		fileMenu.addSeparator()
		quitAction = QAction('&Quit', self)
		quitAction.setShortcut('Ctrl+Q')
		quitAction.triggered.connect(self.OnQuit)
		fileMenu.addAction(quitAction)

		# Help Menu
		editMenu = mainMenu.addMenu('&Help')

		aboutAction = QAction('&About', self)
		aboutAction.setShortcut('F1')
		aboutAction.triggered.connect(self.OnOpenAboutDialog)
		editMenu.addAction(aboutAction)

		# Statusbar
		self.statusBar = self.statusBar()

		# Window Content
		hbox = QHBoxLayout()

		self.textField = QTextEdit()
		font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
		font.setPointSize(14)
		self.textField.setFont(font)
		self.listBox = QListWidget()
		self.listBox.doubleClicked.connect(self.OnSendCommand)
		#self.listBox.currentTextChanged.connect(self.OnCommandChanged)
		for command in self.commands: self.listBox.addItem(command['title'])
		self.listBox.setCurrentRow(0)

		splitter = QSplitter(Qt.Horizontal)
		splitter.addWidget(self.listBox)
		splitter.addWidget(self.textField)
		splitter.setStretchFactor(1, 2)

		hbox.addWidget(splitter)

		widget = QWidget(self)
		widget.setLayout(hbox)
		self.setCentralWidget(widget)

		# Icon Selection
		#if(getattr(sys, 'frozen', False)):
		#	# included via pyinstaller (Windows & macOS)
		#	self.PRODUCT_ICON_PATH = sys._MEIPASS
		#self.iconPath = path.join(self.PRODUCT_ICON_PATH, self.PRODUCT_ICON)
		#if(path.exists(self.iconPath)):
		#	self.icon = QIcon(self.iconPath)
		#	self.setWindowIcon(self.icon)

		# Toolbar
		toolbar = QToolBar(self)
		self.addToolBar(toolbar)
		self.portAction = QAction('Port...', self)
		self.portAction.triggered.connect(self.OnSelectSerialPort)
		toolbar.addAction(self.portAction)
		self.baudAction = QAction('Baud...', self)
		self.baudAction.triggered.connect(self.OnSelectSerialBaud)
		toolbar.addAction(self.baudAction)
		toolbar.addSeparator()
		self.sendAction = QAction('Send Command', self)
		self.sendAction.triggered.connect(self.OnSendCommand)
		toolbar.addAction(self.sendAction)

		# Window Settings
		self.setMinimumSize(520, 400)
		self.setWindowTitle(self.PRODUCT_NAME+" v"+self.PRODUCT_VERSION)

		# Tray Icon
		trayIcon = SerialCommanderTrayIcon(self)
		trayIcon.show()

		# Load Initial
		self.UpdatePortAndBaudText()

	def UpdatePortAndBaudText(self):
		self.portAction.setText('Port: '+str(self.serialPort))
		self.baudAction.setText('Baud: '+str(self.serialBaud))

	def SetupConnection(self, serialPort, serialBaud, message=True):
		if(self.serialConn != None and self.serialConn.is_open):
			self.serialConn.close()
			print('Closed Port')
		try:
			self.serialConn = serial.Serial(serialPort, serialBaud)
			print('Opened Port '+str(self.serialConn.port)+' @ '+str(self.serialConn.baudrate)+' @ '+str(self.serialConn.parity)+' @ '+str(self.serialConn.stopbits)+' @ '+str(self.serialConn.bytesize))
			return True
		except Exception as e:
			if(message):
				messageText = "Cannot send data. Please check if serial port »"+self.serialPort+"« is correct and if you have privileges to use this port (add your user to group dialout via »usermod -a -G dialout USERNAME« and log in again).\n\n"+str(e)
				if(platform.system() == 'Windows' or platform.system() == 'Darwin'):
					messageText = "Cannot send data. Please check if serial port »"+self.serialPort+"« is correct.\n\nIf the error persists, please use the command line tool to examine the error.\n\n"+str(e)
				QMessageBox.critical(self, "Connection Error", messageText)
			return False

	def OnSendCommand(self):
		if(len(self.listBox.selectedItems()) == 0): return
		command = self.commands[self.listBox.currentRow()]
		self.SendCommand(command)

	def SendCommand(self, command):
		targetPort = command['port'] if command['port'] != None else self.serialPort
		targetBaud = command['baud'] if command['baud'] != None else self.serialBaud
		if(self.serialConn == None or self.serialConn.port != targetPort or self.serialConn.baudrate != targetBaud):
			print('Setup New Connection...')
			if(not self.SetupConnection(targetPort, targetBaud)): return
		try:
			if(command['type'] == 'hex'):
				print('Send(HEX): '+command['data'].replace(' ', ''))
				self.serialConn.write(bytearray.fromhex(command['data'].replace(' ', '')))
		except Exception as e:
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Critical)
			msg.setWindowTitle('Error sending data')
			msg.setText('Could not send data of command »'+str(command['title'])+'«.')
			msg.setInformativeText(str(e))
			msg.setDetailedText(str(command['data']))
			msg.setStandardButtons(QMessageBox.Ok)
			retval = msg.exec_()

	def OnSelectSerialPort(self, e):
		item, ok = QInputDialog.getItem(self, "Port Selection", "Please select serial port which should be used to communicate with the device.", self.serialPorts, 0, False)
		if ok and item:
			self.serialPort = item
			self.UpdatePortAndBaudText()

	def OnSelectSerialBaud(self, e):
			item, ok = QInputDialog.getInt(self, "Change Baudrate", "Please enter the baudrate you want to use.", self.serialBaud, 600, 2000000)
			if ok:
				self.serialBaud = item
				self.UpdatePortAndBaudText()

	def OnOpenAboutDialog(self, e):
		dlg = SixledsAboutWindow(self)
		dlg.exec_()

	def OnShow(self):
		self.show()

	def OnQuit(self, e):
		self.SaveSettings()
		sys.exit()

	def closeEvent(self, event):
		self.hide()
		event.ignore()

def main():
	app = QApplication(sys.argv)
	window = SerialCommanderMainWindow()
	window.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
