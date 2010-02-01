#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
""" SMS.py - Python class for sending SMS's through Saunalahti """

import sys
import urllib2
import cookielib



class SMS:
    """ SMS.py for sending SMS through Saunalahti -service """
    username = None
    password = None
    sender = None
    
    def __init__(self, username, password, sender):
        self.username = username
        self.password = password
        self.sender = sender

    def send_sms(self, recipients, sms):
        """ sendSMS function was ripped from SaunaSMS software
        # This is a very quick and dirty SaunaSMS
        # This script will contact oma.saunalahti.fi and provides the 
        # sms service
        # Copyright (C) 2008 Juhapekka Piiroinen
        #
        #   This program is free software: you can redistribute it 
        #   and/or modify it under the terms of the GNU General 
        #   Public License as published by the Free Software 
        #   Foundation, either version 3 of the License, or (at 
        #   your option) any later version.
        #
        #   This program is distributed in the hope that it will 
        #   be useful, but WITHOUT ANY WARRANTY; without even the 
        #   implied warranty of MERCHANTABILITY or FITNESS FOR A 
        #   PARTICULAR PURPOSE. See the GNU General Public License 
        #   for more details.
        #
        #   You should have received a copy of the GNU General 
        #   Public License along with this program.  If not, see 
        #   <http://www.gnu.org/licenses/>.
        #
        #   Contact: juhapekka.piiroinen@gmail.com Version: 0.3
        """
        
        username = self.username
        password = self.password
        sender = self.sender
        multiple = 0
        msgs = []
        try:
            if len(sms)>160:
                multiple = len(sms)/160 + 1
                for i in range(0, multiple):
                    msgs.append(sms[i*160:i*160+160])
            else:
                msgs.append(sms)
        except:
            print "Unexpected error while splitting sms message:"+\
                sys.exc_info()[0]
    
        for sms in msgs:
            url = None
            details = None
            cookie = None
            opener = None
            site = None
            try:
                url = 'https://oma.saunalahti.fi/settings/smsSend'
                details = r"username="+username+\
                          r"&login=SisÃ¤Ã¤n&password="+password
                cookie = cookielib.CookieJar()
                opener = urllib2.build_opener(\
                        urllib2.HTTPCookieProcessor(cookie))
                opener.addheaders = [('Referer', \
                    'https://oma.saunalahti.fi/settings/'),
                    ('Content-Type', \
                    'application/x-www-form-urlencoded'),
                    ('User-Agent', \
                    'Mozilla/5.0 (Windows; U; Windows NT 5.1; '+ \
                    'en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6')]
                site = opener.open(url, details)
                site.read()
                site.close()
                details = "sender=" + sender + \
                        "&recipients=" + recipients + \
                        "&text=" + sms + \
                        "&size=" + str(len(sms)) + \
                        "&send=LÃ¤hetÃ¤"
                site = opener.open(url, details)
                site.read()
                site.close()
            except:
                print "Unexpected error while sending sms from "+\
                    "send_sms function: "+sys.exc_info()[0]

