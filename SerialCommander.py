#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from os import path
from pathlib import Path
from functools import partial
import argparse
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
	trayMenu = None

	def __init__(self, parent=None):
		pixmap = QPixmap()
		pixmap.loadFromData(parent.ICON_BYTES)
		QSystemTrayIcon.__init__(self, QIcon(pixmap), parent)
		self.activated.connect(parent.OnShow)
		self.CreateMenuItems(parent)

	def CreateMenuItems(self, parent):
		if(self.trayMenu == None):
			self.trayMenu = QMenu(parent)

		self.trayMenu.clear()
		for command in parent.commands:
			commandAction = QAction(command['title'], parent)
			commandAction.triggered.connect(partial(parent.SendCommand, command))
			self.trayMenu.addAction(commandAction)

		self.trayMenu.addSeparator()
		exitAction = QAction('Exit', parent)
		exitAction.triggered.connect(parent.OnQuit)
		exitAction = self.trayMenu.addAction(exitAction)

		self.setContextMenu(self.trayMenu)

class SerialCommanderMainWindow(QMainWindow):
	PRODUCT_NAME      = "SerialCommander"
	PRODUCT_VERSION   = "0.1.0"
	PRODUCT_WEBSITE   = "https://georg-sieber.de"
	ICON_BASE64       = b"iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAACdeAAAnXgHPwViOAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAABAxJREFUeJztm89LI2cYx7/zTqajCQ0mInMQdik5qIkuDZ6Cp72UUhAvuxTW7gp7rJRC+0e0wrLbi9seSouLRJSiqLB4ixfJHzCK9SClsBeR1NR2m8aZd9JDJm4StuvmnWfmtfT9QEgm75tnnvk+z/tj3nkDKBQKxf8YLUS71LYb/osUSicZgHcA9BUKhcTExMS7nueR2GeMNWzb/qNcLr8E8DeACwAehW0qAVgymRwoFotf5HK5+6lU6gaR3Q7Ozs5+3d/ffzY7O/vN+fl5FQQiUAigJZPJVKlUWslkMh8Q2LuS4+PjncnJyXsAqgjYLBiBP+by8vLnUV08AGQymQ+3trY+Q7PJBYJEgPHx8fsEdnoim83OAegLaicW8PeaZVnmwMDAze6Cer3+V0DbHZimGW8/TqfTNy3LMk9OTjQEaAZBBUA+n48zxjoyiXPuWpZ1C8BZV/X2Pqfb6TeVpSqVys+6rl/6yxjT8/l8fGdnR9R1AAQCvIEqgN/8z615gem/uwAcvLpQDYDh+9MAUEfnuB/WfCVUAToYGRlJLC0tPfU8j52enj6fmZlZQ1MEAIhtbm7eHRoa+ogx5s3NzX16dHT0ZxR+RSaA67r9o6OjnwCAbds1AOtoEyCdTt/OZrP3/LpfAohEAIpR4K3gnLOuz+1prb2mPBIiO9F1RbQJtDoto1qt9v9LnX4AidZBrVa7rOe6ru6Xt7Kgz/+uvW77sPfac/jnjqPZlNo71bdGVABje3v7weDg4G3HcRLdhYwxViqVnsRiMbf1neM4l7O24eHhwu7u7re6rnMA4JzrlmW93ypfWVl5ZBjGRevYdd1Y91ALAAsLC18ZhvGyUqmUpqenn6F5k9QTosNLvFwu/zA2Nvax4O9JOTw8XC0UCg8B9Dz5Eu0DNM/zrk3/4fsiFMxrcxGyUALIdkA2SgDZDshGCSDbAdkoAWQ7IBslgGwHZCMsgKZp5M/pRAnii6gAnuu6v4uelBrfF6HHZKICXKyvr3/HOe/5/psazrmzsbHxPQTWAgDx9QANQGJvb+/HXC53R9AGCQcHBz9NTU09RHMRteemIJoBDQC11dXVr2VmAefcWVtbe4TmQohQPxDkgYP0LAgafSDYMCg1CyiiDwR/5CQtCyiiDwSfCEnJAqroA0Q7RBBxFlBFH6CZCkeaBZTRB+geO0eWBZTRB+huhiLJAuroA7QbD0LPAuroA7S3w6FmQRjRB+i3noSWBWFEH6BfEGkAqBWLxcfEduHbJI0+EM6KkGfb9gtqo75Nkv3B7YSyJMYYI18tCsMmoNYElQBKANkOyCYUAUzT5P8Fm0B4e3CN+fn59+r1un511asxTZMvLi7+glc7S8kI809TlPYbXe8KhUKhoOAfZeezVYbuDMMAAAAASUVORK5CYII="
	ICON_BYTES        = QByteArray.fromBase64(ICON_BASE64)

	trayIcon = None

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

		{'title':'BENQ Projector: ON', 'description':'Turn projector on.', 'data':'0d 2a 70 6f 77 3d 6f 6e 23 0d', 'type':'hex', 'port':None, 'baud':None},
		{'title':'BENQ Projector: OFF', 'description':'Turn projector off.', 'data':'0d 2a 70 6f 77 3d 6f 66 66 23 0d', 'type':'hex', 'port':None, 'baud':None},
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
		removeCommandAction.triggered.connect(self.OnRemoveCommand)
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

		splitter = QSplitter(Qt.Horizontal)
		splitter.addWidget(self.listBox)
		splitter.addWidget(self.textField)
		splitter.setStretchFactor(1, 2)

		hbox.addWidget(splitter)

		widget = QWidget(self)
		widget.setLayout(hbox)
		self.setCentralWidget(widget)

		# Icon Selection
		pixmap = QPixmap()
		pixmap.loadFromData(self.ICON_BYTES)
		self.setWindowIcon(QIcon(pixmap))

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
		self.trayIcon = SerialCommanderTrayIcon(self)
		self.trayIcon.show()

		# Load Initial
		self.RefreshCommandList()
		self.UpdatePortAndBaudText()

	def UpdatePortAndBaudText(self):
		self.portAction.setText('Port: '+str(self.serialPort))
		self.baudAction.setText('Baud: '+str(self.serialBaud))

	def RefreshCommandList(self):
		self.listBox.clear()
		for command in self.commands: self.listBox.addItem(command['title'])
		self.listBox.setCurrentRow(0)
		self.trayIcon.CreateMenuItems(self)

	def OnRemoveCommand(self):
		if(len(self.listBox.selectedItems()) == 0): return
		del self.commands[self.listBox.currentRow()]
		self.RefreshCommandList()

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
	parser = argparse.ArgumentParser()
	parser.add_argument('--hidden', action='store_true', help='Only show tray icon (use this parameter if you want to add this program to your auto start)')
	args = parser.parse_args()

	app = QApplication(sys.argv)
	window = SerialCommanderMainWindow()

	pixmap = QPixmap()
	pixmap.loadFromData(window.ICON_BYTES)
	app.setWindowIcon(QIcon(pixmap))

	if(not args.hidden): window.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
