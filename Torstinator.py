#!/usr/bin/python2.5
# -*- coding: utf-8 -*-

# http://people.csail.mit.edu/hubert/pyaudio/
import pyaudio
# http://docs.python.org/library/logging.html
import logging

import audioop
import optparse
from time import localtime, strftime

version = 0.3
LOG_FILENAME = '%s.log' % strftime("%Y%m%d%H%M%S", localtime())
NOISE_FILENAME = '%s.noise' % strftime("%Y%m%d%H%M%S", localtime())

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s\t%(levelname)s\t%(message)s',
                    filename=LOG_FILENAME,
                    filemode='w')

class Torstinator:
	debug = False
	limit = 0
			
	def monitor(self):
		logging.info("Torstinator %.2f, Debug: %s, Limit: %d" % (version, self.debug, self.limit))
		logging.debug("Initializing")
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
			noise = ""
			try:
				data = stream.read(buffer)
				level = float(audioop.max(data,2))
				if ( level > self.limit ):
					logging.info("Detected noise, %d" % level)

				barktime=int(strftime('%s',localtime()))+(60*60*3)
				barktime_readable=strftime('%Y-%m-%d %H:%M:%S',localtime())
				print '%s %d' % (barktime_readable, level)
				f = open(NOISE_FILENAME, 'a')
				f.write("%s %d\n" % (barktime, level))
				f.close()
			except KeyboardInterrupt:
				print("Interrupted by ctrl-c")
				break
		logging.debug("Closing session")
		stream.close()
		p.terminate()

parser = optparse.OptionParser(version='Torstinator %.2f' % version)
parser.add_option('-d', '--debug', action='store_true', dest='debug', default=False, help='debug')
parser.add_option('-l', '--limit', dest='limit', default=1000, type='int', help='limit')
(options, args) = parser.parse_args()
	

T = Torstinator()

logging.debug("Setting limits")
T.limit = options.limit
logging.debug("Entering monitor mode")
T.monitor()
