#!/usr/bin/python2.5
# -*- coding: utf-8 -*-

# http://people.csail.mit.edu/hubert/pyaudio/
import pyaudio
# http://docs.python.org/library/logging.html
import logging

import audioop
import optparse
import time
import sqlite3
import os
import urllib2, cookielib, re
from time import strftime

version = 0.7

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s\t%(levelname)s\t%(message)s')


def sendSms(username,password,sender,recipients,sms):
	# sendSMS function was ripped from SaunaSMS software
	##############################################################################
	# This is a very quick and dirty SaunaSMS
	##############################################################################
	# This script will contact oma.saunalahti.fi and provides the sms service
	##############################################################################
	#    SaunaSMS is a small quick and dirty script which will provide a free
	#    sms service for Saunalahti (http://www.saunalahti.fi) customers.
	#
	#    Copyright (C) 2008  Juhapekka Piiroinen
	#
	#    This program is free software: you can redistribute it and/or modify
	#    it under the terms of the GNU General Public License as published by
	#    the Free Software Foundation, either version 3 of the License, or
	#    (at your option) any later version.
	#
	#    This program is distributed in the hope that it will be useful,
	#    but WITHOUT ANY WARRANTY; without even the implied warranty of
	#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	#    GNU General Public License for more details.
	#
	#    You should have received a copy of the GNU General Public License
	#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
	#############################################################################
	# Contact: juhapekka.piiroinen@gmail.com
	# Version: 0.3
	#############################################################################
	multiple = 0
	msgs = []
	if len(sms)>160:
		multiple = len(sms)/160 + 1
		last = 0
		for i in range(0,multiple):
			msgs.append(sms[i*160:i*160+160])
			last = i
	else:
		msgs.append(sms)

	for i in msgs:
		sms = i
		u = 'https://oma.saunalahti.fi/settings/smsSend'
		d = r"username="+username+r"&login=SisÃ¤Ã¤n&password="+password
		c = cookielib.CookieJar()
		o = urllib2.build_opener(urllib2.HTTPCookieProcessor(c))
		o.addheaders = [('Referer', 'https://oma.saunalahti.fi/settings/'),
					('Content-Type', 'application/x-www-form-urlencoded'),
					('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')]
		s= o.open(u, d)
		p = s.read()
		s.close()
		d = "sender="+sender+"&recipients="+recipients+"&text="+sms+"&size="+str(len(sms))+"&send=LÃ¤hetÃ¤"
		s = o.open(u,d)
		d = s.read()
		s.close()

class Torstinator:
	debug = 0
	limit = 0
	con = None
	day = None
	username = None
	password = None
	sender = None
	to = None

	def __init__(self):
		logging.info("Torstinator %.2f, Debug: %s, Limit: %d" % (version, self.debug, self.limit))
		logging.debug("Initializing")
		database_name = "noise_archive/noise.%s.db" % strftime("%Y-%m-%d")
		self.day = strftime("%d")
		logging.info("Connecting to database")
		if not os.path.isfile(database_name):
			logging.info("Database file not found")
			self.con = sqlite3.connect(database_name,isolation_level=None)
			c = self.con.cursor()
			c.execute('''create table noise (datetime text, noise real);''')
		else:
			logging.info("Database file found")
			self.con = sqlite3.connect(database_name,isolation_level=None)
			logging.info("Database connected")

					

	def monitor(self):
		logging.debug("Monitoring")
		samples = 44100
		buffer = samples
		stream = None
		try:
			logging.debug("Setting up PyAudio")
			p = pyaudio.PyAudio()
			logging.debug("Setting up audiostream")
			stream = p.open(format = pyaudio.paInt16,
                			channels = 1,
                			rate = samples,
                			input = True,
					frames_per_buffer = buffer)
		except Exception, e:
			print e
			pass

		if stream == None:
			logging.debug("Failed to open microphone")
			return
		logging.debug("Entering listen loop")
		while True:
			try:	
				curday = strftime("%d")
				if (self.day != curday):
					print("Day changed, restarting")
					break
				else:
					self.day = curday
				data = stream.read(buffer)
				level = int(audioop.max(data,2))
				barktime=int(time.time())
				t = (barktime, level)
				logging.info('Noise %d' % (level))
				self.con.execute('INSERT INTO noise VALUES (?,?);',t)
				if (level > self.limit and self.username != None and self.password != None and self.sender != None and self.to != None):

					msg = "There is noise in your livingroom (level %s)" % (level)
					# sendSms(self.username,self.password,self.sender,self.to,msg)

			except KeyboardInterrupt:
				print("Interrupted by ctrl-c")
				break
		logging.debug("Closing session")
		stream.close()
		p.terminate()

parser = optparse.OptionParser(version='Torstinator %.2f' % version)
parser.add_option('-d', '--debug', action='store_true', dest='debug', default=False, help='debug')
parser.add_option('-l', '--limit', dest='limit', default=10000, type='int', help='limit')
parser.add_option('-u', '--username', dest='username', default=None, type='str', help='saunalahti username')
parser.add_option('-p', '--password', dest='password', default=None, type='str', help='saunalahti password')
parser.add_option('-f', '--from', dest='sender', default=None, type='str', help='saunalahti sender')
parser.add_option('-t', '--to', dest='to', default=None, type='str', help='saunalahti destination')
(options, args) = parser.parse_args()
	

T = Torstinator()

logging.debug("Setting limits")
T.limit = options.limit
T.username = options.username
T.password = options.password
T.sender = options.sender
T.to = options.to
logging.debug("Entering monitor mode")
T.monitor()
