#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import path, makedirs, rename
from pathlib import Path
from functools import partial
import argparse
import json
import glob
import time
import platform
import serial
import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class SerialCommanderAboutWindow(QDialog):
	def __init__(self, *args, **kwargs):
		super(SerialCommanderAboutWindow, self).__init__(*args, **kwargs)
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
			"© 2021-2022 <a href='https://github.com/schorschii'>Georg Sieber</a>"
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
	PRODUCT_VERSION   = "0.2.0"
	PRODUCT_WEBSITE   = "https://georg-sieber.de"
	ICON_BASE64       = b"iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAACdeAAAnXgHPwViOAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAABAxJREFUeJztm89LI2cYx7/zTqajCQ0mInMQdik5qIkuDZ6Cp72UUhAvuxTW7gp7rJRC+0e0wrLbi9seSouLRJSiqLB4ixfJHzCK9SClsBeR1NR2m8aZd9JDJm4StuvmnWfmtfT9QEgm75tnnvk+z/tj3nkDKBQKxf8YLUS71LYb/osUSicZgHcA9BUKhcTExMS7nueR2GeMNWzb/qNcLr8E8DeACwAehW0qAVgymRwoFotf5HK5+6lU6gaR3Q7Ozs5+3d/ffzY7O/vN+fl5FQQiUAigJZPJVKlUWslkMh8Q2LuS4+PjncnJyXsAqgjYLBiBP+by8vLnUV08AGQymQ+3trY+Q7PJBYJEgPHx8fsEdnoim83OAegLaicW8PeaZVnmwMDAze6Cer3+V0DbHZimGW8/TqfTNy3LMk9OTjQEaAZBBUA+n48zxjoyiXPuWpZ1C8BZV/X2Pqfb6TeVpSqVys+6rl/6yxjT8/l8fGdnR9R1AAQCvIEqgN/8z615gem/uwAcvLpQDYDh+9MAUEfnuB/WfCVUAToYGRlJLC0tPfU8j52enj6fmZlZQ1MEAIhtbm7eHRoa+ogx5s3NzX16dHT0ZxR+RSaA67r9o6OjnwCAbds1AOtoEyCdTt/OZrP3/LpfAohEAIpR4K3gnLOuz+1prb2mPBIiO9F1RbQJtDoto1qt9v9LnX4AidZBrVa7rOe6ru6Xt7Kgz/+uvW77sPfac/jnjqPZlNo71bdGVABje3v7weDg4G3HcRLdhYwxViqVnsRiMbf1neM4l7O24eHhwu7u7re6rnMA4JzrlmW93ypfWVl5ZBjGRevYdd1Y91ALAAsLC18ZhvGyUqmUpqenn6F5k9QTosNLvFwu/zA2Nvax4O9JOTw8XC0UCg8B9Dz5Eu0DNM/zrk3/4fsiFMxrcxGyUALIdkA2SgDZDshGCSDbAdkoAWQ7IBslgGwHZCMsgKZp5M/pRAnii6gAnuu6v4uelBrfF6HHZKICXKyvr3/HOe/5/psazrmzsbHxPQTWAgDx9QANQGJvb+/HXC53R9AGCQcHBz9NTU09RHMRteemIJoBDQC11dXVr2VmAefcWVtbe4TmQohQPxDkgYP0LAgafSDYMCg1CyiiDwR/5CQtCyiiDwSfCEnJAqroA0Q7RBBxFlBFH6CZCkeaBZTRB+geO0eWBZTRB+huhiLJAuroA7QbD0LPAuroA7S3w6FmQRjRB+i3noSWBWFEH6BfEGkAqBWLxcfEduHbJI0+EM6KkGfb9gtqo75Nkv3B7YSyJMYYI18tCsMmoNYElQBKANkOyCYUAUzT5P8Fm0B4e3CN+fn59+r1un511asxTZMvLi7+glc7S8kI809TlPYbXe8KhUKhoOAfZeezVYbuDMMAAAAASUVORK5CYII="
	ICON_BYTES        = QByteArray.fromBase64(ICON_BASE64)

	configPath        = str(Path.home())+'/.config/SerialCommander/commands.json'
	configPathOld     = str(Path.home())+'/.SerialCommander.json'
	config = {}

	trayIcon = None

	serialConn  = None
	serialPorts = []
	serialPort  = None
	serialBaud  = 9600
	commands = []

	def __init__(self, args):
		super(SerialCommanderMainWindow, self).__init__()

		self.serialPorts = self.GetSerialPorts()
		if(len(self.serialPorts) > 0): self.serialPort = self.serialPorts[0]

		if(args.config != None):
			self.configPath = args.config

		if(not path.isdir(path.dirname(self.configPath))):
			makedirs(path.dirname(self.configPath), exist_ok=True)
		if(path.exists(self.configPathOld)):
			rename(self.configPathOld, self.configPath)

		if(args.send_and_exit):
			self.LoadSettings(self.configPath, False)
			for command in self.commands:
				self.SendCommand(command)
			sys.exit()

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
			if('bluetooth' in port): continue # macOS
			try:
				s = serial.Serial(port)
				s.close()
				result.append(port)
			except(OSError, serial.SerialException):
				pass
		return result

	def LoadSettings(self, configPath, updateUi):
		if(not path.isfile(configPath)): return

		try:
			with open(configPath) as f:
				self.config = json.load(f)
		except Exception as e:
			print(str(e))
			if(updateUi):
				msg = QMessageBox()
				msg.setIcon(QMessageBox.Critical)
				msg.setWindowTitle('Error loading command file')
				msg.setText(str(e))
				msg.setStandardButtons(QMessageBox.Ok)
				retval = msg.exec_()

		if('DEFAULT' in self.config):
			if('port' in self.config['DEFAULT']): self.serialPort = self.config['DEFAULT']['port']
			if('baud' in self.config['DEFAULT']): self.serialBaud = int(self.config['DEFAULT']['baud'])
			if(updateUi): self.UpdatePortAndBaudText()

		if('COMMANDS' in self.config):
			self.commands = []
			for command in self.config['COMMANDS']:
				self.commands.append(command)
			if(updateUi): self.RefreshCommandList()

	def SaveSettings(self, configPath):
		if(not 'DEFAULT' in self.config): self.config['DEFAULT'] = {}
		self.config['DEFAULT']['port'] = self.serialPort
		self.config['DEFAULT']['baud'] = self.serialBaud

		self.config['COMMANDS'] = []
		for command in self.commands:
			self.config['COMMANDS'].append(command)

		with open(configPath, 'w') as json_file:
			json.dump(self.config, json_file, indent=4)

	def InitUI(self):
		# Menubar
		mainMenu = self.menuBar()

		# File Menu
		fileMenu = mainMenu.addMenu('&File')

		selectPortAction = QAction('Select Default &Port...', self)
		selectPortAction.setShortcut('Ctrl+P')
		selectPortAction.triggered.connect(self.OnSelectSerialPort)
		fileMenu.addAction(selectPortAction)
		selectPortAction = QAction('Select Default &Baudrate...', self)
		selectPortAction.setShortcut('Ctrl+B')
		selectPortAction.triggered.connect(self.OnSelectSerialBaud)
		fileMenu.addAction(selectPortAction)

		fileMenu.addSeparator()
		addCommandAction = QAction('&Send Command...', self)
		addCommandAction.setShortcut('F2')
		addCommandAction.triggered.connect(self.OnSendCommand)
		fileMenu.addAction(addCommandAction)

		fileMenu.addSeparator()
		addCommandAction = QAction('&Add Command...', self)
		addCommandAction.setShortcut('Ctrl+I')
		addCommandAction.triggered.connect(self.OnAddCommand)
		fileMenu.addAction(addCommandAction)
		removeCommandAction = QAction('&Remove Command', self)
		removeCommandAction.setShortcut('DEL')
		removeCommandAction.triggered.connect(self.OnRemoveCommand)
		fileMenu.addAction(removeCommandAction)

		fileMenu.addSeparator()
		addCommandAction = QAction('&Open Command File...', self)
		addCommandAction.setShortcut('Ctrl+O')
		addCommandAction.triggered.connect(self.OnOpenFile)
		fileMenu.addAction(addCommandAction)
		removeCommandAction = QAction('&Save Command File...', self)
		removeCommandAction.setShortcut('Ctrl+S')
		removeCommandAction.triggered.connect(self.OnSaveFile)
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

		self.controlFrame = QWidget()
		self.listBox = QListWidget()
		self.listBox.itemActivated.connect(self.OnSendCommand)
		self.listBox.currentTextChanged.connect(self.UpdateStatusBarText)

		splitter = QSplitter(Qt.Horizontal)
		splitter.addWidget(self.listBox)
		splitter.addWidget(self.controlFrame)
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
		self.setMinimumSize(580, 420)
		self.setWindowTitle(self.PRODUCT_NAME+" v"+self.PRODUCT_VERSION)

		# Tray Icon
		self.trayIcon = SerialCommanderTrayIcon(self)
		self.trayIcon.show()

		# Load Settings
		self.LoadSettings(self.configPath, True)

		# Show Note
		if(len(self.commands) == 0):
			self.statusBar.showMessage("Please open a command configuration file (File -> Open File...)")
		else:
			self.statusBar.showMessage("If you like SerialCommander please consider making a donation to support further development ("+self.PRODUCT_WEBSITE+").")

	def UpdatePortAndBaudText(self):
		self.portAction.setText('Port: '+str(self.serialPort))
		self.baudAction.setText('Baud: '+str(self.serialBaud))

	def UpdateStatusBarText(self):
		text = ''
		if(len(self.listBox.selectedItems()) != 0):
			command = self.commands[self.listBox.currentRow()]
			if('description' in command): text = command['description']
		self.statusBar.showMessage(text)

	def RefreshCommandList(self):
		# Update Listbox
		self.listBox.clear()
		for command in self.commands: self.listBox.addItem(command['title'])
		self.listBox.setCurrentRow(0)

		# Update Tray Icon
		self.trayIcon.CreateMenuItems(self)

		# Update Button Layout
		for i in reversed(self.controlFrame.findChildren(QPushButton)):
			i.deleteLater()
		for command in self.commands:
			try:
				if(not 'button' in command or command['button'] == None): continue
				commandButton = command['button']
				if(not 'x' in commandButton or not 'y' in commandButton): continue
				if(not 'w' in commandButton or not 'h' in commandButton): continue
				btn = QPushButton(commandButton['text'] if 'text' in commandButton else '')
				btn.setParent(self.controlFrame)
				btn.resize(int(commandButton['w']), int(commandButton['h']))
				btn.move(int(commandButton['x']), int(commandButton['y']))
				btn.clicked.connect(partial(self.SendCommand, command))
				if('icon' in commandButton):
					try:
						pixmap = QPixmap()
						pixmap.loadFromData(QByteArray.fromBase64(str.encode(commandButton['icon'])))
						btn.setIcon(QIcon(pixmap))
					except Exception as e: print(str(e))
				btn.show()
			except Exception as e: print(str(e))

	def OnAddCommand(self):
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)
		msg.setWindowTitle('Not implemented')
		msg.setText('Please use a text editor to edit »~/.SerialCommander.json« in order to add or modify commands.')
		msg.setDetailedText('You think this sucks? Just make a pull request :-)')
		msg.setStandardButtons(QMessageBox.Ok)
		retval = msg.exec_()

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
				cleanedData = command['data'].replace(' ', '')
				print('Send(HEX): '+cleanedData)
				self.serialConn.write(bytearray.fromhex(cleanedData))

				if(type(self.statusBar) == QStatusBar):
					self.statusBar.showMessage(str(targetPort)+' @ '+str(targetBaud)+'  =(hex)=>  '+cleanedData)
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

	def OnOpenFile(self, e):
		defaultExamplesPath = "/usr/share/SerialCommander/examples"
		defaultPath = ""
		if(path.exists(defaultExamplesPath)): defaultPath = defaultExamplesPath
		fileName, _ = QFileDialog.getOpenFileName(self, "Choose Command File", defaultPath, "SerialCommander Files (*.json);;All Files (*.*)")
		if(not fileName): return
		self.LoadSettings(fileName, True)

	def OnSaveFile(self, e):
		fileName, _ = QFileDialog.getSaveFileName(self, "Save Command File", "", "SerialCommander Files (*.json);;All Files (*.*)")
		if(not fileName): return
		self.SaveSettings(fileName)

	def OnOpenAboutDialog(self, e):
		dlg = SerialCommanderAboutWindow(self)
		dlg.exec_()

	def OnShow(self):
		self.show()

	def OnQuit(self, e):
		self.SaveSettings(self.configPath)
		sys.exit()

	def closeEvent(self, event):
		self.hide()
		event.ignore()

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--hidden', action='store_true', help='Only show tray icon (use this parameter if you want to add this program to your auto start)')
	parser.add_argument('--config', default=None, help='Use this config file')
	parser.add_argument('--send-and-exit', action='store_true', help='Send all commands from config file and exit')
	args = parser.parse_args()

	app = QApplication(sys.argv)
	window = SerialCommanderMainWindow(args)

	pixmap = QPixmap()
	pixmap.loadFromData(window.ICON_BYTES)
	app.setWindowIcon(QIcon(pixmap))

	if(not args.hidden): window.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
