#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
""" Torstinator.py - The ultimate Python bark detector """

import sys
import os
import time
from time import strftime

import ConfigParser
import urllib2
import cookielib
import wave
import audioop


try:
    import pyaudio 
except ImportError:
    print "You need to have pyaudio library ", \
	"(http://people.csail.mit.edu/hubert/pyaudio/)"
    sys.exit(1)
# http://docs.python.org/library/logging.html
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s\t%(levelname)s\t%(message)s')

__sqliteenabled__ = False

try:
    import sqlite3
    __sqliteenabled__ = True
except ImportError:
    logging.warning("Could not import sqlite module")    
    pass

# I have problems with py25 + pyaudio + twitter lib, 
# so this is mainly for my own hacks, sorry
sys.path.append('/opt/local/lib/python2.5/site-packages/')
########


__twitterenabled__ = False
try:
    import twitter
    __twitterenabled__ = True
except ImportError:
    logging.warning("Could not import twitter module")
    pass


__author__ = 'Tero Heino'
__version__ = 1.0



def send_sms(username, password, sender, recipients, sms):
    """ sendSMS function was ripped from SaunaSMS software
    #############################################################
    # This is a very quick and dirty SaunaSMS
    ##############################################################################
    # This script will contact oma.saunalahti.fi and provides the sms service
    ##############################################################################
    #    SaunaSMS is a small quick and dirty script which will provide a free sms 
    #    service for Saunalahti (http://www.saunalahti.fi) customers.
    #
    #    Copyright (C) 2008 Juhapekka Piiroinen
    #
    #    This program is free software: you can redistribute it and/or modify it 
    #    under the terms of the GNU General Public License as published by the 
    #    Free Software Foundation, either 
    #    version 3 of the License, or (at your option) any later version.
    #
    #    This program is distributed in the hope that it will be useful, but 
    #    WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY 
    #    or FITNESS FOR A PARTICULAR PURPOSE.  
    #    See the GNU General Public License for more details.
    #
    #    You should have received a copy of the GNU General Public License along 
    #    with this program.  If not, see <http://www.gnu.org/licenses/>.
    #############################################################################
    # Contact: juhapekka.piiroinen@gmail.com Version: 0.3
    #############################################################################
    """
    multiple = 0
    msgs = []
    try:
        if len(sms)>160:
            multiple = len(sms)/160 + 1
            last = 0
            for i in range(0, multiple):
                msgs.append(sms[i*160:i*160+160])
                last = i
        else:
            msgs.append(sms)
    except:
        print "Unexpected error while splitting sms message:", sys.exc_info()[0]

    for sms in msgs:
        url = None
        details = None
        cookie = None
        opener = None
        site = None
        tmp = None
        try:
            url = 'https://oma.saunalahti.fi/settings/smsSend'
            details = r"username="+username+\
                      r"&login=SisÃ¤Ã¤n&password="+password
            cookie = cookielib.CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
            opener.addheaders = [('Referer', \
                        'https://oma.saunalahti.fi/settings/'),
                       ('Content-Type', \
                        'application/x-www-form-urlencoded'),
                       ('User-Agent', \
                        'Mozilla/5.0 (Windows; U; Windows NT 5.1; '+ \
                        'en-US; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')]
            site = opener.open(url, details)
            tmp = site.read()
            site.close()
            details = "sender=" + sender + \
                    "&recipients=" + recipients + \
                    "&text=" + sms + \
                    "&size=" + str(len(sms)) + \
                    "&send=LÃ¤hetÃ¤"
            site = opener.open(url, details)
            tmp = site.read()
            site.close()
        except:
            print "Unexpected error while sending sms from send_sms function:",\
                   sys.exc_info()[0]


class Torstinator:
    """ Class for doing all the work of Torstinator - The bark detector"""
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
    use_recording = False
    recording_limit = None
    recording_time = None

    def __init__(self):
        """ Constructor, set the defaults, read config etc """
        logging.debug("Initializing")

        database_name = "noise_archive/noise.%s.db" % \
                        strftime("%Y-%m-%d")
        self.day = strftime("%d")
        try:
            self.config = ConfigParser.ConfigParser()
            self.config.readfp(open('Torstinator.cfg'))
        except IOError:
            logging.critical("Config file not found, please take ", \
                             "copy of Torstinator.cfg.sample and ", \
                             "rename it as Torstinator.cfg")
            sys.exit(2)
        self.log_limit = self.config.getint('Logging', 'noise_limit')
        self.use_sqlite = self.config.getboolean('Logging', 'use_sqlite')
        self.use_screenlog = self.config.getboolean('Logging', 'use_screenlog')

        self.use_twitter = self.config.getboolean('Twitter', 'use_twitter')
        self.twitter_limit = self.config.getint('Twitter', 'noise_limit')
        self.twitter_username = self.config.get('Twitter', 'username')
        self.twitter_password = self.config.get('Twitter', 'password')

        self.use_recording = self.config.getboolean('Record', 'use_recording')
        self.recording_limit = self.config.getint('Record', 'noise_limit')
        self.recording_time = self.config.getint('Record', 'record_time')

        self.use_sms = self.config.getboolean('SMS', 'use_sms')
        self.sms_limit = self.config.getint('SMS', 'noise_limit')
        self.sms_username = self.config.get('SMS', 'username')
        self.sms_password = self.config.get('SMS', 'password')
        self.sms_from = self.config.get('SMS', 'from')
        self.sms_to = self.config.get('SMS', 'to')

        logging.info("Torstinator %.2f" % __version__)
        logging.info("sqlite: %d" % (self.use_sqlite))
        logging.info("Log to screen: %d (limit: %d)" % (self.use_screenlog, \
                                                        self.log_limit))
        logging.info("Twitter: %d (limit: %d)" % (self.use_twitter, \
                                                  self.twitter_limit))
        logging.info("sms: %d (limit: %d)" % (self.use_sms, self.sms_limit) )
        logging.info("record: %d (limit: %d, length: %d seconds)" % \
                                             (self.use_recording, \
                                              self.recording_limit, \
                                              self.recording_time) )

        if os.path.isdir("noise_archive"):
            logging.debug("noise_archive folder found")
        else:
            os.mkdir("noise_archive")
            logging.info("created archive folder for sqlite files")

        if os.path.isdir("record_archive"):
            logging.debug("record_archive folder found")
        else:
            os.mkdir("record_archive")
            logging.info("created archive folder for wave record files")

        if __sqliteenabled__ and self.use_sqlite:
            logging.debug("Connecting to database")
            if not os.path.isfile(database_name):
                logging.warning("Database file not found")
                self.con = sqlite3.connect(database_name, \
                                           isolation_level = None)
                cursor = self.con.cursor()
                cursor.execute('create table noise (datetime ', \
                               'text, noise real);')
            else:
                logging.debug("Database file found")
                self.con = sqlite3.connect(database_name, \
                                           isolation_level = None)
                logging.debug("Database connected")

    def alert(self, noise):
        """ process alerts """
        msg = 'Noise level exceeded limits, amount %d, limit %d'

        # if self.use_screenlog and noise > self.log_limit:
        #     msg = msg % (noise, self.log_limit)
        #     logging.info(msg)

        if self.use_twitter and \
                __twitterenabled__ and \
                noise > self.twitter_limit and \
                self.twitter_username != "" and \
                self.twitter_password != "":
            msg = msg % (noise, self.twitter_limit)
            try:
                api = twitter.Api(username=self.twitter_username, \
                                  password=self.twitter_password)
                status = api.PostUpdate(msg)
                logging.info("Alerted via twitter (%s)", status)
            except:
                print "Unexpected error while twittering:", sys.exc_info()[0]
                pass

        if self.use_sms and \
               noise > self.sms_limit and \
               self.sms_username != "" and \
               self.sms_password != "" and \
               self.sms_to != "" and \
               self.sms_from != "":
            msg = msg % (noise, self.sms_limit)
            try:
                send_sms(self.sms_username, self.sms_password, \
                        self.sms_from, self.sms_to, msg)
                logging.info("Alerted via SMS")
            except:
                print "Unexpected error while sending sms:", sys.exc_info()[0]
                pass

    def monitor(self):
        """ monitoring loop """
        logging.debug("Monitoring")
        samples = 44100
        stream = None
        try:
            logging.debug("Setting up PyAudio")
            paudio = pyaudio.PyAudio()
            logging.debug("Setting up audiostream")
            stream = paudio.open(format = pyaudio.paInt16,
                            channels = 1,
                            rate = samples,
                            input = True,
                    frames_per_buffer = samples)

        except:
            print "Unexpected error:", sys.exc_info()[0]
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
                data = stream.read(samples)
                level = int(audioop.max(data, 2))
                barktime = int(time.time())

                self.alert(level)

                if self.use_recording and level > self.recording_limit:
                    logging.info("Recording some noise")
                    all = []
                    all.append(data)
                    for i in range(0, samples / samples * self.recording_time):
                        streamdata = stream.read(samples)
                        all.append(streamdata)
                        logging.info("Recording.. %d" % (i+1))
                    streamdata = ''.join(all)
                    filename = 'record_archive/%s.wav' % \
                               strftime("%Y-%m-%d_%H%M%S")
                    wavefile = wave.open(filename, 'wb')
                    wavefile.setnchannels(1)
                    wavefile.setsampwidth(paudio.get_sample_size(\
                                          pyaudio.paInt16))
                    wavefile.setframerate(samples)
                    wavefile.writeframes(streamdata)
                    wavefile.close()
    
                
                if self.use_screenlog:
                    logging.info('Noise %d' % (level))

                if __sqliteenabled__ and self.use_sqlite:
                    self.con.execute('INSERT INTO noise VALUES (?,?);', \
                                     (barktime, level))
                
            except IOError:
                logging.warning("PyAudio failed to read device, skipping")
                pass

            except KeyboardInterrupt:
                logging.info("Interrupted by ctrl-c")
                break
        logging.debug("Closing session")
        stream.close()
        paudio.terminate()

T = Torstinator()
logging.debug("Setting limits")
logging.debug("Entering monitor mode")

T.monitor()
