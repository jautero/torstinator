#!/usr/bin/python2.5
# -*- coding: utf-8 -*-


import audioop
import time
import ConfigParser
import os
import urllib2, cookielib, re
from time import strftime
import sys


try:
	import pyaudio 
except ImportError:
	print "You need to have pyaudio library (http://people.csail.mit.edu/hubert/pyaudio/)"
	sys.exit(1)
# http://docs.python.org/library/logging.html
import logging

sqlite_enabled = False

try:
	import sqlite3
	sqlite_enabled = True
except ImportError:
	pass

twitter_enabled = False
try:
	import twitter
	twitter_enabled = True
except ImportError:
	pass

version = 0.9

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s\t%(levelname)s\t%(message)s')



def sendSms(username,password,sender,recipients,sms):
	# sendSMS function was ripped from SaunaSMS software
	##############################################################################
	# This is a very quick and dirty SaunaSMS
	##############################################################################
	# This script will contact oma.saunalahti.fi and provides the sms service
	##############################################################################
	#    SaunaSMS is a small quick and dirty script which will provide a free sms service for Saunalahti (http://www.saunalahti.fi) customers.
	#
	#    Copyright (C) 2008 Juhapekka Piiroinen
	#
	#    This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either 
	#    version 3 of the License, or (at your option) any later version.
	#
	#    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
	#    See the GNU General Public License for more details.
	#
	#    You should have received a copy of the GNU General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.
	#############################################################################
	# Contact: juhapekka.piiroinen@gmail.com Version: 0.3
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
	con = None
	day = None
	sender = None
	to = None
	config = None
	log_limit = None
	use_sqlite = False
	use_screenlog = True
	use_twitter = False
	twitter_limit = None
	twitter_username = ""
	twitter_password = ""
	use_sms = False
	sms_limit = None
	sms_username = ""
	sms_password = ""
	sms_from = ""
	sms_to = ""

	twitapi = None

	def __init__(self):
		logging.debug("Initializing")
		database_name = "noise_archive/noise.%s.db" % strftime("%Y-%m-%d")
		self.day = strftime("%d")
		try:
			self.config = ConfigParser.ConfigParser()
			self.config.readfp(open('Torstinator.cfg'))
		except IOError:
			logging.critical("Config file not found, please take copy of Torstinator.cfg.sample and rename it as Torstinator.cfg")
			sys.exit(2)
		self.log_limit = self.config.getint('Logging','noise_limit')
		self.use_sqlite = self.config.getboolean('Logging','use_sqlite')
		self.use_screenlog = self.config.getboolean('Logging','use_screenlog')
		self.use_twitter = self.config.getboolean('Twitter','use_twitter')
		self.twitter_limit = self.config.getint('Twitter','noise_limit')
		self.twitter_username = self.config.get('Twitter','username')
		self.twitter_password = self.config.get('Twitter','password')
		self.sms_limit = self.config.getint('SMS','noise_limit')
		self.use_sms = self.config.getboolean('SMS','use_sms')
		self.sms_username = self.config.get('SMS','username')
		self.sms_password = self.config.get('SMS','password')
		self.sms_from = self.config.get('SMS','from')
		self.sms_to = self.config.get('SMS','to')

		logging.info("Torstinator %.2f" % version)
		logging.info("Limit: %d" % self.log_limit)
		logging.info("Twitter: %d (limit: %d)" % (self.use_twitter, self.twitter_limit))
		logging.info("sqlite: %d" % (self.use_sqlite))
		logging.info("sms: %d (limit: %d)" % (self.use_sms, self.sms_limit) )
		logging.info("Log to screen: %d" % self.use_screenlog)

		if twitter_enabled and self.use_twitter:
			logging.info("Twitter initialized")
			self.twitapi = twitter.Api(username=self.twitter_username,password=self.twitter_password)


		if sqlite_enabled and self.use_sqlite:
			logging.debug("Connecting to database")
			if not os.path.isfile(database_name):
				logging.warning("Database file not found")
				self.con = sqlite3.connect(database_name,isolation_level=None)
				c = self.con.cursor()
				c.execute('''create table noise (datetime text, noise real);''')
			else:
				logging.debug("Database file found")
				self.con = sqlite3.connect(database_name,isolation_level=None)
				logging.debug("Database connected")

	def alert(self, noise):
		msg = "Noise level exceeded limits, amount %d, limit %d" 
		if self.use_screenlog and noise > self.log_limit:
			msg = msg % (noise, self.log_limit)
			logging.info(msg)

		if self.use_twitter and twitter_enabled and noise > self.twitter_limit and self.twitter_username != "" and self.twitter_password != "":
			msg = msg % (noise, self.twitter_limit)
			status = self.twitapi.PostUpdate(self.twitter_username, self.twitter_password, msg)
			logging.info("Alerted via twitter")

		if self.use_sms and noise > self.sms_limit and self.sms_username != "" and self.sms_password != "" and self.sms_to != "" and self.sms_from != "":
			msg = msg % (noise, self.sms_limit)
			sendSms(self.sms_username,self.sms_password,self.sms_from,self.sms_to,msg)
			logging.info("Alerted via SMS")


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
			logging.critical("Failed to open microphone")
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
				if self.use_screenlog:
					logging.info('Noise %d' % (level))

				if sqlite_enabled and self.use_sqlite:
					self.con.execute('INSERT INTO noise VALUES (?,?);',t)
				
				self.alert(level)

			except KeyboardInterrupt:
				print("Interrupted by ctrl-c")
				break
		logging.debug("Closing session")
		stream.close()
		p.terminate()

T = Torstinator()
logging.debug("Setting limits")
logging.debug("Entering monitor mode")

T.monitor()
