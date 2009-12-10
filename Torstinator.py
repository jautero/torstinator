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

version = 0.4

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s\t%(levelname)s\t%(message)s')

class Torstinator:
	debug = 0
	limit = 0
	con = None

	def __init__(self):
		logging.info("Torstinator %.2f, Debug: %s, Limit: %d" % (version, self.debug, self.limit))
		logging.debug("Initializing")
		database_name = "noise.db"
		if not os.path.exists(database_name):
			self.con = sqlite3.connect(database_name,isolation_level=None)
			self.con.execute('''create table noise (datetime text, noise real)''')
		else:
			self.con = sqlite3.connect(database_name,isolation_level=None)

					

	def monitor(self):
		logging.debug("Monitoring")
		samples = 44100
		buffer = samples
		try:
			logging.debug("Setting up PyAudio")
			p = pyaudio.PyAudio()
			logging.debug("Setting up audiostream")
			stream = p.open(format = pyaudio.paInt16,
                			channels = 1,
                			rate = samples,
                			input = True,
					frames_per_buffer = buffer)
		except e:
			print e
			pass

		logging.debug("Entering listen loop")
		while True:
			try:
				data = stream.read(buffer)
				level = float(audioop.max(data,2))
				barktime=int(time.time())
				logging.info('Noise %d' % (level))
				t = (barktime, level)
				self.con.execute('INSERT INTO noise VALUES (?,?);',t)
			except KeyboardInterrupt:
				print("Interrupted by ctrl-c")
				break
		logging.debug("Closing session")
		stream.close()
		p.terminate()

parser = optparse.OptionParser(version='Torstinator %.2f' % version)
parser.add_option('-d', '--debug', action='store_true', dest='debug', default=False, help='debug')
parser.add_option('-l', '--limit', dest='limit', default=10000, type='int', help='limit')
(options, args) = parser.parse_args()
	

T = Torstinator()

logging.debug("Setting limits")
T.limit = options.limit
logging.debug("Entering monitor mode")
T.monitor()
