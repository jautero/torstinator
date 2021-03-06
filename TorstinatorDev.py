#!/usr/bin/python2.5
# -*- coding: utf-8 -*-
""" Torstinator.py - The ultimate Python bark detector """
import sys
import os

import audioop
import wave


import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s\t%(levelname)s\t%(message)s')




try:
    import pyaudio 
except ImportError:
    logging.critical("You need to have pyaudio library "+ \
	"(http://people.csail.mit.edu/hubert/pyaudio/)")
    sys.exit(1)


__author__ = 'Tero Heino'
__version__ = 1.0

SAMPLE_RATE = 44100
BUFFER_SIZE = 30


class AudioBank:
    """ AudioBank class holds the noise level and raw audio
        data """
    
    audio_data = []
    noise_levels = []

    silence = 70
    noise = 20000
    
    def __init__ (self):
        """ init """


    def push(self, newsounds, levels):
        """ push(rawsounddata, soundlevel) pushes raw data and
            noise levels to arrays for further processing """
        self.audio_data.append(newsounds)
        self.noise_levels.append(levels)
        if len(self.audio_data) > BUFFER_SIZE:
            self.audio_data.pop(0)
            self.noise_levels.pop(0)
        self.status()
        
    def buffer_size(self):
        """ buffer_size() returns the size of buffer in seconds """
        return len(self.audio_data)
    
    def get_data(self):
        """ get_data() returns raw audio data for the 
            duration of BUFFER_SIZE """
        return ''.join(self.audio_data)
    
    def noiseleveltopercentage(self, level):
        """ noiseleveltoprecentage(noiselevel) transforms
            your noise level into percentage value """
        percentage = (float(level) - float(self.silence))
        percentage = (percentage / float(self.noise)) * 100
        if percentage < 0:
            return 0
        elif percentage > 100:
            return 100
        else:
            return percentage
            
    def status(self):
        """ status() brings up a status of the data that bank 
            currently holds """
        if os.name == "posix":
            os.system('clear')
        if os.name == "nt":
            os.system('cls')

        print "| AudioBank now has %d seconds stored" % \
                    (len(self.audio_data)) 
        print "|-----------------------------------"
        print "| Max noise: %d" % max(self.noise_levels)
        average = 0
        for i in self.noise_levels:
            average += i
        average = average/len(self.noise_levels)
        print "| Average noise: %d" % average
        print "|-----------------------------------"
        for i in self.noise_levels:
            output = ""
            for level in range(0, int(self.noiseleveltopercentage(i))):
                output = output+"#"
            if i == max(self.noise_levels):
                output = output + " (MAX)"
            print "|%s" % output
            
class Torstinator:
    """ Class for doing all the work of Torstinator - The bark detector"""
    paudio = None
    stream = None
    audiobank = None
    
    def __init__(self):
        """ Constructor, set the defaults, read config etc """
        try:
            logging.debug("Setting up PyAudio")
            self.paudio = pyaudio.PyAudio()

            self.audiobank = AudioBank()
            
            logging.debug("Setting up audiostream")
            self.stream = self.paudio.open(format = pyaudio.paInt16,
                            channels = 1,
                            rate = SAMPLE_RATE,
                            input = True,
                    frames_per_buffer = SAMPLE_RATE)

        except:
            print "Unexpected error:", sys.exc_info()[0]

        if self.stream == None:
            logging.critical("Failed to open microphone")
            return
        
        self.monitor()
            
    def save_buffer(self, filename):
        """ save_buffer(filename) saves current audiobank buffer
            to hard disk """
        wavefile = wave.open(filename, 'wb')
        wavefile.setnchannels(1)
        wavefile.setsampwidth(self.paudio.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(SAMPLE_RATE)
        wavefile.writeframes(self.audiobank.get_data())
        wavefile.close()

    def monitor(self):
        """ monitor() receive data from microphone
            and act accordingly """
        while True:
            try:
                data = self.stream.read(SAMPLE_RATE)
                level = int(audioop.max(data, 2))
                self.audiobank.push(data, level)
                # logging.info("Noise: %d" % level)
            except IOError:
                logging.warning("PyAudio failed to read device, skipping")
        
            except KeyboardInterrupt:
                # self.audiobank.save_buffer("poo.wav")
                logging.info("Interrupted by ctrl-c")
                break
        


    def __del__(self):
        self.stream.close()
        self.paudio.terminate()


if __name__ == "__main__":
    T = Torstinator()


"""    def monitor(self):
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
        paudio.terminate()"""