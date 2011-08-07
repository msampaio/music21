# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.recording.py
# Purpose:      routines for making recordings from microphone input
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
modules for audio searching that directly record from the microphone.


Requires PyAudio and portaudio to be installed (http://www.portaudio.com/download.html)


To download pyaudio for windows 64-bit go to http://www.lfd.uci.edu/~gohlke/pythonlibs/


users of 64-bit windows but 32-bit python should download the win32 port


users of 64-bit windows and 64-bit python should download the amd64 port
 

'''
import time
import unittest, doctest
import wave
import music21
from music21 import common


_missingImport = []

###
# to download pyaudio for windows 64-bit go to http://www.lfd.uci.edu/~gohlke/pythonlibs/
# users of 64-bit windows but 32-bit python should download the win32 port
# users of 64-bit windows and 64-bit python should download the amd64 port
# requires portaudio to be installed http://www.portaudio.com/download.html
try:
    import pyaudio
    recordFormat = pyaudio.paInt16
except ImportError:
    pyaudio = None
    recordFormat = 8 # pyaudio.paInt16

    _missingImport.append('pyaudio')

recordChannels = 1
recordSampleRate = 44100
recordChunkLength = 1024

def samplesFromRecording(seconds = 10.0, storeFile = True, 
                recordFormat = recordFormat, 
                recordChannels = recordChannels,
                recordSampleRate = recordSampleRate,
                recordChunkLength = 1024):
    '''
    records `seconds` length of sound in the given format (default Wave)
    and optionally stores it to disk using the filename of `storeFile`
    
    
    Returns a list of samples.
    '''
    if recordFormat == pyaudio.paInt8:
        raise AudioSearchException("cannot perform freq_from_autocorr on 8-bit samples")
    
    p_audio = pyaudio.PyAudio()
    st = p_audio.open(format=recordFormat,
                    channels=recordChannels,
                    rate=recordSampleRate,
                    input=True,
                    frames_per_buffer=recordChunkLength)

    recordingLength = int(recordSampleRate*float(seconds)/recordChunkLength)
    
    storedWaveSampleList = []

    #time_start = time.time()
    for i in range(recordingLength):
        data = st.read(recordChunkLength)
        storedWaveSampleList.append(data)
    #print 'Time elapsed: %.3f s\n' % (time.time() - time_start)
    st.close()
    p_audio.terminate()    

    if storeFile != False: 
        if common.isStr(storeFile):
            waveFilename = storeFile
        else:
            waveFilename = 'chrom2.wav'
        ### write recording to disk
        data = ''.join(storedWaveSampleList)
        try:
            wf = wave.open(waveFilename, 'wb')
            wf.setnchannels(recordChannels)
            wf.setsampwidth(p_audio.get_sample_size(recordFormat))
            wf.setframerate(recordSampleRate)
            wf.writeframes(data)
            wf.close()
        except IOError:
            raise AudioSearchException("Cannot open %s for writing." % waveFilename)
    return storedWaveSampleList

#------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

class TestExternal(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testRecording(self):
        '''
        record one second of data and print 10 records
        '''
        sampleList = samplesFromRecording(seconds = 1, storeFile = False)
        print sampleList[30:40]


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    music21.mainTest(Test, 'noDocTest')


#------------------------------------------------------------------------------
# eof