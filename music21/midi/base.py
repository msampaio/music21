#-------------------------------------------------------------------------------
# Name:         midi.base.py
# Purpose:      music21 classes for dealing with midi data
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#               (Will Ware -- see docs)
#
# Copyright:    (c) 2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''
Objects and tools for processing MIDI data. 

This module uses routines from Will Ware's public domain midi.py from 2001
see http://groups.google.com/group/alt.sources/msg/0c5fc523e050c35e
'''

import unittest, doctest
import unicodedata
import sys, os, string, types

try:
    import StringIO # python 2 
except:
    from io import StringIO # python3 (also in python 2.6+)

import music21
from music21 import common

from music21 import environment
_MOD = "midi.base.py"  
environLocal = environment.Environment(_MOD)


# good midi reference:
# http://www.sonicspot.com/guide/midifiles.html



#-------------------------------------------------------------------------------
class EnumerationException(Exception): 
    pass 

class MidiException(Exception): 
    pass 




#-------------------------------------------------------------------------------
# def showstr(str, n=16): 
#     for x in str[:n]: 
#         print (('%02x' % ord(x)),) 
#     print("")

def charToBinary(char):
    '''Convert a char into its binary representation. Useful for debugging. 
    >>> charToBinary('a')
    '01100001'
    '''
    ascii = ord(char)
    bin = []
    while (ascii > 0):
        if (ascii & 1) == 1:
            bin.append("1")
        else:
            bin.append("0")
        ascii = ascii >> 1
    
    bin.reverse()
    binary = ''.join(bin)
    zerofix = (8 - len(binary)) * '0'
    return zerofix + binary


def getNumber(str, length): 
    '''Return the value of a string byte from and 8-bit string. Then, return the remaining string.

    The `length` is the number of chars to read.     

    This will sum a length greater than 1 if desired.

    >>> getNumber('test', 0)
    (0, 'test')
    >>> getNumber('test', 2)
    (29797, 'st')
    >>> getNumber('test', 4)
    (1952805748, '')
    '''
    # MIDI uses big-endian for everything 
    # in python this is the inverse of chr()
    sum = 0 
    for i in range(length): 
        sum = (sum << 8) + ord(str[i]) 
    return sum, str[length:] 

def getVariableLengthNumber(str): 
    '''Given a string of data, strip off a number that might be of variable size; after finding the appropriate termination, return the remaining string.

    This necessary as Delta times are given with variable size, and thus may be if different numbers of characters.

    >>> getVariableLengthNumber('A-u')
    (65, '-u')
    >>> getVariableLengthNumber('-u')
    (45, 'u')
    >>> getVariableLengthNumber('u')
    (117, '')

    >>> getVariableLengthNumber('test')
    (116, 'est')
    >>> getVariableLengthNumber('E@-E')
    (69, '@-E')
    >>> getVariableLengthNumber('@-E')
    (64, '-E')
    >>> getVariableLengthNumber('-E')
    (45, 'E')
    >>> getVariableLengthNumber('E')
    (69, '')

    >>> getVariableLengthNumber('\\xff\\x7f')
    (16383, '')

    '''
    # from http://faydoc.tripod.com/formats/mid.htm
    # This allows the number to be read one byte at a time, and when you see a msb of 0, you know that it was the last (least significant) byte of the number.
    # additional reference here:
    # http://253.ccarh.org/handout/vlv/
    sum = 0 
    i = 0 
    while True: 
        x = ord(str[i]) 
        #environLocal.printDebug(['getVariableLengthNumber: examined char:', charToBinary(str[i])])
        sum = (sum << 7) + (x & 0x7F) 
        i += 1 
        if not (x & 0x80): 
            #environLocal.printDebug(['getVariableLengthNumber: depth read into string: %s' % i])
            return sum, str[i:] 


def getNumbersAsList(str):
    '''Translate each char into a number, return in a list. Used for reading data messages where each byte encodes a different discrete value. 

    >>> getNumbersAsList('\\x00\\x00\\x00\\x03')
    [0, 0, 0, 3]
    '''
    post = []
    for i in range(len(str)):
        post.append(ord(str[i]))
    return post

def putNumber(num, length): 
    '''
    >>> putNumber(3, 4)
    '\\x00\\x00\\x00\\x03'
    >>> putNumber(0, 1)
    '\\x00'
    '''
    lst = [] 
    for i in range(length): 
        n = 8 * (length - 1 - i) 
        lst.append(chr((num >> n) & 0xFF)) 
    return string.join(lst, "") 

def putVariableLengthNumber(x): 
    '''
    >>> putVariableLengthNumber(4)
    '\\x04'
    >>> putVariableLengthNumber(127)
    '\\x7f'
    >>> putVariableLengthNumber(0)
    '\\x00'
    >>> putVariableLengthNumber(1024)
    '\\x88\\x00'
    >>> putVariableLengthNumber(8192)
    '\\xc0\\x00'
    >>> putVariableLengthNumber(16383)
    '\\xff\\x7f'

    >>> putVariableLengthNumber(-1)
    Traceback (most recent call last):
    MidiException: cannot putVariableLengthNumber() when number is negative: -1
    '''
    #environLocal.printDebug(['calling putVariableLengthNumber(x) with', x])
    # note: negative numbers will cause an infinite loop here
    if x < 0:
        raise MidiException('cannot putVariableLengthNumber() when number is negative: %s' % x)
    lst = [ ] 
    while True: 
        y, x = x & 0x7F, x >> 7 
        lst.append(chr(y + 0x80)) 
        if x == 0: 
            break 
    lst.reverse() 
    lst[-1] = chr(ord(lst[-1]) & 0x7f) 
    return string.join(lst, "") 


def putNumbersAsList(numList):
    '''Translate a list of numbers into a character byte strings. Used for encoding data messages where each byte encodes a different discrete value. 

    >>> putNumbersAsList([0, 0, 0, 3])
    '\\x00\\x00\\x00\\x03'
    >>> putNumbersAsList([0, 0, 0, -3])
    '\\x00\\x00\\x00\\xfd'
    >>> putNumbersAsList([0, 0, 0, -1])
    '\\x00\\x00\\x00\\xff'
    '''
    post = []
    for n in numList:
        # assume if a number exceeds range count down from top?
        if n < 0:
            n = 256 + n # -1 will be 255
        post.append(chr(n))
    return ''.join(post)

#-------------------------------------------------------------------------------
class Enumeration(object): 
    '''Utility object for defining binary MIDI message constants. 
    '''
    def __init__(self, enumList): 
        lookup = { } 
        reverseLookup = { } 
        i = 0 
        uniqueNames = [ ] 
        uniqueValues = [ ] 
        for x in enumList: 
            if type(x) == types.TupleType: 
                x, i = x 
            if type(x) != types.StringType: 
                raise EnumerationException("enum name is not a string: " + x)
            if type(i) != types.IntType: 
                raise EnumerationException("enum value is not an integer: " + i)
            if x in uniqueNames: 
                raise EnumerationException("enum name is not unique: " + x)
            if i in uniqueValues: 
                raise EnumerationException("enum value is not unique for " + x)
            uniqueNames.append(x) 
            uniqueValues.append(i) 
            lookup[x] = i 
            reverseLookup[i] = x 
            i = i + 1 
        self.lookup = lookup 
        self.reverseLookup = reverseLookup 

    def __add__(self, other): 
        lst = [ ] 
        for k in self.lookup.keys(): 
            lst.append((k, self.lookup[k])) 
        for k in other.lookup.keys(): 
            lst.append((k, other.lookup[k])) 
        return Enumeration(lst) 

    def hasattr(self, attr): 
        return self.lookup.has_key(attr) 

    def hasValue(self, attr): 
        return self.reverseLookup.has_key(attr) 

    def __getattr__(self, attr): 
        if not self.lookup.has_key(attr): 
            raise AttributeError 
        return self.lookup[attr] 

    def whatis(self, value): 
        return self.reverseLookup[value] 

channelVoiceMessages = Enumeration([("NOTE_OFF", 0x80), 
                                    ("NOTE_ON", 0x90), 
                                    ("POLYPHONIC_KEY_PRESSURE", 0xA0), 
                                    ("CONTROLLER_CHANGE", 0xB0), 
                                    ("PROGRAM_CHANGE", 0xC0), 
                                    ("CHANNEL_KEY_PRESSURE", 0xD0), 
                                    ("PITCH_BEND", 0xE0)]) 

channelModeMessages = Enumeration([("ALL_SOUND_OFF", 0x78), 
                                   ("RESET_ALL_CONTROLLERS", 0x79), 
                                   ("LOCAL_CONTROL", 0x7A), 
                                   ("ALL_NOTES_OFF", 0x7B), 
                                   ("OMNI_MODE_OFF", 0x7C), 
                                   ("OMNI_MODE_ON", 0x7D), 
                                   ("MONO_MODE_ON", 0x7E), 
                                   ("POLY_MODE_ON", 0x7F)]) 

metaEvents = Enumeration([("SEQUENCE_NUMBER", 0x00), 
                          ("TEXT_EVENT", 0x01), 
                          ("COPYRIGHT_NOTICE", 0x02), 
                          ("SEQUENCE_TRACK_NAME", 0x03), 
                          ("INSTRUMENT_NAME", 0x04), 
                          ("LYRIC", 0x05), 
                          ("MARKER", 0x06), 
                          ("CUE_POINT", 0x07), 
                          ("MIDI_CHANNEL_PREFIX", 0x20), 
                          ("MIDI_PORT", 0x21), 
                          ("END_OF_TRACK", 0x2F), 
                          ("SET_TEMPO", 0x51), 
                          ("SMTPE_OFFSET", 0x54), 
                          ("TIME_SIGNATURE", 0x58), 
                          ("KEY_SIGNATURE", 0x59), 
                          ("SEQUENCER_SPECIFIC_META_EVENT", 0x7F)]) 



# def register_note(track_index, channel_index, pitch, velocity, 
#                   keyDownTime, keyUpTime): 
# 
#     """ 
#     register_note() is a hook that can be overloaded from a script that 
#     imports this module. Here is how you might do that, if you wanted to 
#     store the notes as tuples in a list. Including the distinction 
#     between track and channel offers more flexibility in assigning voices. 
#     import midi 
#     notelist = [ ] 
#     def register_note(t, c, p, v, t1, t2): 
#         notelist.append((t, c, p, v, t1, t2)) 
#     midi.register_note = register_note 
#     """ 
#     pass 



# class MidiChannel(object): 
#     '''A channel (together with a track) provides the continuity connecting 
#     a NOTE_ON event with its corresponding NOTE_OFF event. Together, those 
#     define the beginning and ending times for a Note.
# 
#     >>> mc = MidiChannel(0, 0)
#     ''' 
#     
#     def __init__(self, track, index): 
#         self.index = index 
#         self.track = track 
#         self.pitches = {} # store pairs of time and velocity
# 
#     def __repr__(self): 
#         return "<MIDI channel %d>" % self.index 

#     def noteOn(self, pitch, time, velocity): 
#         self.pitches[pitch] = (time, velocity) 
# 
#     def noteOff(self, pitch, time): 
#         # find and remove form dictionary
#         if pitch in self.pitches: 
#             keyDownTime, velocity = self.pitches[pitch] 
#             #register_note(self.track.index, self.index, pitch, velocity, 
#             #              keyDownTime, time) 
#             del self.pitches[pitch] 



#-------------------------------------------------------------------------------
class MidiEvent(object): 
    '''A model of a MIDI event, including note-on, note-off, program change, controller change, any many others.

    MidiEvent objects are paired (preceded) by DeltaTime objects in the list of events in a MidiTrack object.

    The `track` argument must be a :class:`~music21.midi.base.MidiTrack` object.

    The `type` attribute is a string representation of a Midi event from the channelVoiceMessages or metaEvents definitions. 

    The `channel` attribute is an integer channel id, from 1 to 16. 

    The `time` attribute is an integer duration of the event in ticks. This value can be zero. This value is not essential, as ultimate time positioning is determined by DeltaTime objects. 

    The `pitch` attribute is only defined for note-on and note-off messages. The attribute stores an integer representation (0-127).

    The `velocity` attribute is only defined for note-on and note-off messages. The attribute stores an integer representation (0-127).

    The `data` attribute is used for storing other messages, such as SEQUENCE_TRACK_NAME string values. 

    >>> mt = MidiTrack(1)
    >>> me1 = MidiEvent(mt)
    >>> me1.type = "NOTE_ON"
    >>> me1.channel = 1
    >>> me1.time = 200
    >>> me1.pitch = 60
    >>> me1.velocity = 120
    >>> me1
    <MidiEvent NOTE_ON, t=200, track=1, channel=1, pitch=60, velocity=120>

    >>> me2 = MidiEvent(mt)
    >>> me2.type = "SEQUENCE_TRACK_NAME"
    >>> me2.time = 0
    >>> me2.data = 'guitar'
    >>> me2
    <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=None, data='guitar'>
    '''
    
    def __init__(self, track, type=None, time=None, channel=None): 
        self.track = track 
        self.type = type
        self.time = time
        self.channel = channel

        self._parameter1 = None # pitch or first data value
        self._parameter2 = None # velocity or second data value
        #self.data = None # alternative data storage

        # if this is a Note on/off, need to store original
        # pitch space value in order to determine if this is has a microtone
        self.centShift = None
    
        # store a reference to a corresponding event
        # if a noteOn, store the note off, and vice versa
        self.correspondingEvent = None

    def __cmp__(self, other): 
        return cmp(self.time, other.time) 
    
    def __repr__(self): 
        if self.track == None:
            trackIndex = None
        else:
            trackIndex = self.track.index

        r = ("<MidiEvent %s, t=%s, track=%s, channel=%s" % 
             (self.type, repr(self.time), trackIndex, 
              repr(self.channel))) 
        if self.type in ['NOTE_ON', 'NOTE_OFF']:
            attrList = ["pitch", "velocity"]
        else:
            attrList = ["data"]

        for attrib in attrList: 
            if getattr(self, attrib) != None: 
                r = r + ", " + attrib + "=" + repr(getattr(self, attrib)) 
        return r + ">" 
    

    # provide parameter access to pitch and velocity
    def _setPitch(self, value):
        self._parameter1 = value

    def _getPitch(self):
        # only return pitch if this is note on /off
        if self.type in ['NOTE_ON', 'NOTE_OFF']:
            return self._parameter1
        else:
            return None

    pitch = property(_getPitch, _setPitch)

    def _setVelocity(self, value):
        self._parameter2 = value

    def _getVelocity(self):
        return self._parameter2

    velocity = property(_getVelocity, _setVelocity)


    # store generic data in parameter 1
    def _setData(self, value):
        self._parameter1 = value

    def _getData(self):
        return self._parameter1

    data = property(_getData, _setData)


    def setPitchBend(self, cents, bendRange=2):
        '''Treat this event as a pitch bend value, and set the ._parameter1 and ._parameter2 fields appropriately given a specified bend value in cents.
    
        The `bendRange` parameter gives the number of half steps in the bend range.

        >>> mt = MidiTrack(1)
        >>> me1 = MidiEvent(mt)
        >>> me1.setPitchBend(50)
        >>> me1._parameter1, me1._parameter2
        (0, 80)
        >>> me1.setPitchBend(100)
        >>> me1._parameter1, me1._parameter2
        (0, 96)
        >>> me1.setPitchBend(200)
        >>> me1._parameter1, me1._parameter2
        (127, 127)
        >>> me1.setPitchBend(-50)
        >>> me1._parameter1, me1._parameter2
        (0, 48)
        >>> me1.setPitchBend(-100)
        >>> me1._parameter1, me1._parameter2
        (0, 32)
        '''
        # value range is 0, 16383
        # center should be 8192
        centRange = bendRange * 100
        center = 8192
        topSpan = 16383 - center
        bottomSpan = center

        if cents > 0:
            shiftScalar = cents / float(centRange)
            shift = int(round(shiftScalar * topSpan))
        elif cents < 0:
            shiftScalar = cents / float(centRange) # will be negative
            shift = int(round(shiftScalar * bottomSpan)) # will be negative
        else: # cents is zero
            shift = 0
        target = center + shift

        # produce a two-char value
        charValue = putVariableLengthNumber(target)
        d1, junk = getNumber(charValue[0], 1)
        # need to convert from 8 bit to 7, so using & 0x7F
        d1 = d1 & 0x7F
        if len(charValue) > 1:
            d2, junk = getNumber(charValue[1], 1)
            d2 = d2 & 0x7F
        else:
            d2 = 0

        #environLocal.printDebug(['got target char value', charValue, 'getVariableLengthNumber(charValue)', getVariableLengthNumber(charValue)[0], 'd1', d1, 'd2', d2,])

        self._parameter1 = d2
        self._parameter2 = d1 # d1 is msb here
        


    def read(self, time, str): 
        '''Read a MIDI event.

        The `time` value is the number of ticks into the Track at which this event happens. This is derived from reading data the level of the track.
        '''
        if len(str) < 2:
            # often what we have here are null events:
            # the string is simply: 0x00
            environLocal.printDebug(['MidiEvent.read(): got bad data string', 'time', time, 'str', repr(str)])
            return ''

        # x, y, and z define characteristics of the first two chars
        # for x: The left nybble (4 bits) contains the actual command, and the right nibble contains the midi channel number on which the command will be executed.
        x = ord(str[0]) # given a string representation, return the char number
        y = x & 0xF0  # bitwise and to derive channel number
        z = ord(str[1]) 

        #environLocal.printDebug(['MidiEvent.read(): trying to parse a MIDI event, looking at first two chars:', 'repr(x)', repr(x), 'charToBinary(str[0])', charToBinary(str[0]), 'charToBinary(str[1])', charToBinary(str[1])])
        if channelVoiceMessages.hasValue(y): 
            self.channel = (x & 0x0F) + 1  # this is same as y + 1
            self.type = channelVoiceMessages.whatis(y) 
            #environLocal.printDebug(['MidiEvent.read()', self.type])
            if (self.type == "PROGRAM_CHANGE" or 
                self.type == "CHANNEL_KEY_PRESSURE"): 
                self.data = z 
                return str[2:] # only used x and z; return remainder
            elif (self.type == "CONTROLLER_CHANGE"):
                # for now, do nothing with this data
                # for a note, str[2] is velocity; here, it is the control value
                self.pitch = z # this is the controller id
                self.velocity = ord(str[2]) # this is the controller value
                return str[3:] 
            else: 
                self.pitch = z
                # read the third chart toi get velocity 
                self.velocity = ord(str[2]) 
                # each MidiChannel object is accessed here
                # using that channel, data for each event is added or 
                # removed 

                # this is not necessary for reading/writing files
                #channel = self.track.channels[self.channel - 1] 
#                 if (self.type == "NOTE_OFF" or 
#                     (self.velocity == 0 and self.type == "NOTE_ON")): 
#                     channel.noteOff(self.pitch, self.time) 
#                 elif self.type == "NOTE_ON": 
#                     channel.noteOn(self.pitch, self.time, self.velocity) 
                return str[3:] 

        elif y == 0xB0 and channelModeMessages.hasValue(z): 
            self.channel = (x & 0x0F) + 1 
            self.type = channelModeMessages.whatis(z) 
            if self.type == "LOCAL_CONTROL": 
                self.data = (ord(str[2]) == 0x7F) 
            elif self.type == "MONO_MODE_ON": 
                self.data = ord(str[2]) 
            return str[3:] 
        elif x == 0xF0 or x == 0xF7: 
            self.type = {0xF0: "F0_SYSEX_EVENT", 
                         0xF7: "F7_SYSEX_EVENT"}[x] 
            length, str = getVariableLengthNumber(str[1:]) 
            self.data = str[:length] 
            return str[length:]

        # SEQUENCE_TRACK_NAME is here
        elif x == 0xFF: 
            #environLocal.printDebug(['MidiEvent.read(): got a variable length meta event', charToBinary(str[0])])

            if not metaEvents.hasValue(z): 
                environLocal.printDebug(["unknown meta event: FF %02X" % z])
                sys.stdout.flush() 
                raise MidiException("Unknown midi event type: %r, %r" % (x, z))
            self.type = metaEvents.whatis(z) 
            length, str = getVariableLengthNumber(str[2:]) 
            self.data = str[:length] 
            # return remainder
            return str[length:] 
        else:
            environLocal.printDebug(['got unknown midi event type', repr(x), 'charToBinary(str[0])', charToBinary(str[0]), 'charToBinary(str[1])', charToBinary(str[1])])
            raise MidiException("Unknown midi event type")
            # return everything but the first character
            #return str[1:] # 


    def write(self): 
        '''Write out a midi track.
        '''
        sysex_event_dict = {"F0_SYSEX_EVENT": 0xF0, 
                            "F7_SYSEX_EVENT": 0xF7} 
        if channelVoiceMessages.hasattr(self.type): 
            #environLocal.printDebug(['writing channelVoiceMessages', self.type])
            x = chr((self.channel - 1) + 
                    getattr(channelVoiceMessages, self.type)) 
            # for writing note-on/note-off
            if self.type not in ['PROGRAM_CHANGE', 
                'CHANNEL_KEY_PRESSURE']:
                # this results in a two-part string, like '\x00\x00'
                data = chr(self._parameter1) + chr(self._parameter2) 
            elif self.type in ['PROGRAM_CHANGE']:
                #environLocal.printDebug(['trying to add program change data: %s' % self.data])
                data = chr(self.data) 
            else:  # all other messages
                data = chr(self.data) 
            return x + data 

        elif channelModeMessages.hasattr(self.type): 
            x = getattr(channelModeMessages, self.type) 
            x = (chr(0xB0 + (self.channel - 1)) + 
                 chr(x) + 
                 chr(self.data)) 
            return x 

        elif sysex_event_dict.has_key(self.type): 
            s = chr(sysex_event_dict[self.type]) 
            s = s + putVariableLengthNumber(len(self.data)) 
            return s + self.data 

        elif metaEvents.hasattr(self.type):                 
            s = chr(0xFF) + chr(getattr(metaEvents, self.type)) 
            s = s + putVariableLengthNumber(len(self.data)) 
            try: # TODO: need to handle unicode
                return s + self.data 
            except UnicodeDecodeError:
                #environLocal.printDebug(['cannot decode data', self.data])
                return s + unicodedata.normalize('NFKD', 
                           self.data).encode('ascii','ignore')
        else: 
            raise MidiException("unknown midi event type: %s" % self.type)

    #---------------------------------------------------------------------------
    def isNoteOn(self):
        '''Return a boolean if this is a note-on message and velocity is not zero.

        >>> mt = MidiTrack(1)
        >>> me1 = MidiEvent(mt)
        >>> me1.type = "NOTE_ON"
        >>> me1.velocity = 120
        >>> me1.isNoteOn()
        True
        >>> me1.isNoteOff()
        False
        '''
        if self.type == "NOTE_ON" and self.velocity != 0:
            return True
        return False

    def isNoteOff(self):
        '''Return a boolean if this is a note-off message, either as a note-off or as a note-on with zero velocity.

        >>> mt = MidiTrack(1)
        >>> me1 = MidiEvent(mt)
        >>> me1.type = "NOTE_OFF"
        >>> me1.isNoteOn()
        False
        >>> me1.isNoteOff()
        True

        >>> me2 = MidiEvent(mt)
        >>> me2.type = "NOTE_ON"
        >>> me2.velocity = 0
        >>> me2.isNoteOn()
        False
        >>> me2.isNoteOff()
        True
        '''
        if self.type == "NOTE_OFF":
            return True
        elif self.type == "NOTE_ON" and self.velocity == 0:
            return True
        return False

    def isDeltaTime(self):
        '''Return a boolean if this is a note-on message and velocity is not zero.

        >>> mt = MidiTrack(1)
        >>> dt = DeltaTime(mt)
        >>> dt.isDeltaTime()
        True
        '''
        if self.type == "DeltaTime":
            return True
        return False

    def matchedNoteOff(self, other):
        '''If this is a note-on, given another MIDI event, is this a matching note-off for this event, return True. Checks both pitch and channel.

        >>> mt = MidiTrack(1)
        >>> me1 = MidiEvent(mt)
        >>> me1.type = "NOTE_ON"
        >>> me1.velocity = 120
        >>> me1.pitch = 60

        >>> me2 = MidiEvent(mt)
        >>> me2.type = "NOTE_ON"
        >>> me2.velocity = 0
        >>> me2.pitch = 60

        >>> me1.matchedNoteOff(me2)
        True

        >>> me2.pitch = 61
        >>> me1.matchedNoteOff(me2)
        False

        >>> me2.type = "NOTE_OFF"
        >>> me1.matchedNoteOff(me2)
        False

        >>> me2.pitch = 60
        >>> me1.matchedNoteOff(me2)
        True

        '''
        if other.isNoteOff:
            # might check velocity here too?
            if self.pitch == other.pitch and self.channel == other.channel:
                return True
        return False



class DeltaTime(MidiEvent): 
    '''Store the time change since the start or the last MidiEvent.

    Pairs of DeltaTime and MidiEvent objects are the basic presentation of temporal data.

    The `track` argument must be a :class:`~music21.midi.base.MidiTrack` object.

    Time values are in integers, representing ticks. 

    The `channel` attribute, inherited from MidiEvent is not used.

    >>> mt = MidiTrack(1)
    >>> dt = DeltaTime(mt)
    >>> dt.time = 380
    >>> dt
    <MidiEvent DeltaTime, t=380, track=1, channel=None>

    '''
    def __init__(self, track, time=None, channel=None):
        MidiEvent.__init__(self, track, time=time, channel=channel)
        self.type = "DeltaTime" 

    def read(self, oldstr): 
        self.time, newstr = getVariableLengthNumber(oldstr) 
        return self.time, newstr 

    def write(self): 
        str = putVariableLengthNumber(self.time) 
        return str 





class MidiTrack(object): 
    '''A MIDI Track. Each track contains a list of :class:`~music21.midi.base.MidiChannel` objects, one for each channel.

    All events are stored in the `events` list, in order.

    An `index` is an integer identifier for this object.

    >>> mt = MidiTrack(0)
    
    '''
    def __init__(self, index): 
        self.index = index 
        self.events = [] 
        self.length = 0 #the data length; only used on read()

        # no longer need channel objects
        # an object for each of 16 channels is created
#         self.channels = [] 
#         for i in range(16): 
#             self.channels.append(MidiChannel(self, i+1)) 

    def read(self, str): 
        '''Read as much of the string as necessary; return the remaining string for reassignment and further processing.

        Creates and stores :class:`~music21.midi.base.DeltaTime` and :class:`~music21.midi.base.MidiEvent` objects. 
        '''
        time = 0 # a running counter of ticks

        if not str[:4] == "MTrk":
            raise MidiException('badly formed midi string: missing leading MTrk')
        # get the 4 chars after the MTrk encoding
        length, str = getNumber(str[4:], 4)      
        environLocal.printDebug(['MidiTrack.read(): got chunk size', length])   
        self.length = length 

        # all event data is in the track str
        trackStr = str[:length] 
        remainder = str[length:] 

        while trackStr: 
            # shave off the time stamp from the event
            delta_t = DeltaTime(self) 
            # return extracted time, as well as remaining string
            dt, trackStrCandidate = delta_t.read(trackStr) 
            # this is the offset that this event happens at, in ticks
            timeCandidate = time + dt 
    
            # pass self to even, set this MidiTrack as the track for this event
            e = MidiEvent(self) 
            # some midi events may raise errors; simply skip for now
            try:
                trackStrCandidate = e.read(timeCandidate, trackStrCandidate) 
            except MidiException:
                # assume that trackStr, after delta extraction, is still correct
                environLocal.printDebug(['forced to skip event; delta_t:', delta_t])
                # set to result after taking delta time
                trackStr = trackStrCandidate
                continue
            # only set after trying to read, which may raise exception
            time = timeCandidate
            trackStr = trackStrCandidate
            # only append if we get this far
            self.events.append(delta_t) 
            self.events.append(e) 

        return remainder # remainder string after extrating track data
    
    def write(self): 
        # set time to the first event
        time = self.events[0].time 
        # build str using MidiEvents 
        str = ""
        for e in self.events: 
            # this writes both delta time and message events
            ew = e.write()
            str = str + ew 
        return "MTrk" + putNumber(len(str), 4) + str 
    
    def __repr__(self): 
        r = "<MidiTrack %d -- %d events\n" % (self.index, len(self.events)) 
        for e in self.events: 
            r = r + "    " + `e` + "\n" 
        return r + "  >" 

    #---------------------------------------------------------------------------
    def updateEvents(self):
        '''We may attach events to this track before setting their `track` parameter. This method will move through all events and set their track to this track. 
        '''
        for e in self.events:
            e.track = self

    def hasNotes(self):
        '''Return True/False if this track has any note-on/note-off pairs defined. 
        '''
        for e in self.events:
            if e.isNoteOn(): 
                return True
        return False

    def setChannel(self, value):
        '''Set the channel of all events in this Track.
        '''
        if value not in range(1,17): # count from 1
            raise MidiException('bad channel value: %s' % value)
        for e in self.events:
            e.channel = value



class MidiFile(object):
    '''
    Low-level MIDI file writing, emulating methods from normal Python files. 

    The `ticksPerQuarterNote` attribute must be set before writing. 1024 is a common value.

    This object is returned by some properties for directly writing files of midi representations.
    '''
    
    def __init__(self): 
        self.file = None 
        self.format = 1 
        self.tracks = [] 
        self.ticksPerQuarterNote = 1024 
        self.ticksPerSecond = None 
    
    def open(self, filename, attrib="rb"): 
        '''Open a MIDI file path for reading or writing.

        For writing to a MIDI file, `attrib` should be "wb".
        '''
        if attrib not in ['rb', 'wb']:
            raise MidiException('cannot read or write unless in binary mode, not:', attrib)
        self.file = open(filename, attrib) 

    def openFileLike(self, fileLike):
        '''Assign a file-like object, such as those provided by StringIO, as an open file object.

        >>> fileLikeOpen = StringIO.StringIO()
        >>> mf = MidiFile()
        >>> mf.openFileLike(fileLikeOpen)
        >>> mf.close()
        '''
        self.file = fileLike
    
    def __repr__(self): 
        r = "<MidiFile %d tracks\n" % len(self.tracks) 
        for t in self.tracks: 
            r = r + "  " + `t` + "\n" 
        return r + ">" 
    
    def close(self): 
        '''
        Close the file. 
        '''
        self.file.close() 
    
    def read(self): 
        '''
        Read and parse MIDI data stored in a file.
        '''
        self.readstr(self.file.read()) 
    
    def readstr(self, str): 
        '''
        Read and parse MIDI data as a string.
        '''
        if not str[:4] == "MThd":
            raise MidiException('badly formated midi string, got: %s' % str[:20])

        # we step through the str src, chopping off characters as we go
        # and reassigning to str
        length, str = getNumber(str[4:], 4) 
        if not length == 6:
            raise MidiException('badly formated midi string')

        format, str = getNumber(str, 2) 
        self.format = format 
        if not format in [0, 1]:
            raise MidiException('cannot handle midi file format: %s' % format)

        numTracks, str = getNumber(str, 2) 
        division, str = getNumber(str, 2) 

        # very few midi files seem to define ticksPerSecond
        if division & 0x8000: 
            framesPerSecond = -((division >> 8) | -128) 
            ticksPerFrame = division & 0xFF 
            if not ticksPerFrame in [24, 25, 29, 30]:
                raise MidiException('cannot handle ticks per frame: %s' % ticksPerFrame)
            if ticksPerFrame == 29: 
                ticksPerFrame = 30  # drop frame 
            self.ticksPerSecond = ticksPerFrame * framesPerSecond 
        else: 
            self.ticksPerQuarterNote = division & 0x7FFF 

        environLocal.printDebug(['MidiFile.readstr(): got midi file format:', self.format, 'with specified number of tracks:', numTracks, 'ticksPerSecond:', self.ticksPerSecond, 'ticksPerQuarterNote:', self.ticksPerQuarterNote])

        for i in range(numTracks): 
            trk = MidiTrack(i) # sets the MidiTrack index parameters
            str = trk.read(str) # pass all the remaining string, reassing
            self.tracks.append(trk) 
    
    def write(self): 
        '''
        Write MIDI data as a file.
        '''
        ws = self.writestr()
        self.file.write(ws) 
    
    def writestr(self): 
        '''
        Return MIDI data as a string. 
        '''
        division = self.ticksPerQuarterNote 
        # Don't handle ticksPerSecond yet, too confusing 
        if (division & 0x8000) != 0:
            raise MidiException('cannot write midi string')
        str = "MThd" + putNumber(6, 4) + putNumber(self.format, 2) 
        str = str + putNumber(len(self.tracks), 2) 
        str = str + putNumber(division, 2) 
        for trk in self.tracks: 
            str = str + trk.write() 
        return str 




#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):
    '''These are tests that open windows and rely on external software
    '''

    def runTest(self):
        pass

    def testBasic(self):
        pass

#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasicImport(self):

        dir = common.getPackageDir(relative=False, remapSep=os.sep)
        for fp in dir:
            if fp.endswith('midi'):
                break

        dirLib = os.path.join(fp, 'testPrimitive')
        # a simple file created in athenacl
        fp = os.path.join(dirLib, 'test01.mid')
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        self.assertEqual(len(mf.tracks), 2)
        self.assertEqual(mf.ticksPerQuarterNote, 960)
        self.assertEqual(mf.ticksPerSecond, None)
        #self.assertEqual(mf.writestr, None)

        # try to write contents
        fileLikeOpen = StringIO.StringIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()


        # a simple file created in athenacl
        fp = os.path.join(dirLib, 'test02.mid')
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        self.assertEqual(len(mf.tracks), 5)
        self.assertEqual(mf.ticksPerQuarterNote, 1024)
        self.assertEqual(mf.ticksPerSecond, None)

        # try to write contents
        fileLikeOpen = StringIO.StringIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()


        # random files from the internet
        fp = os.path.join(dirLib, 'test03.mid')
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        self.assertEqual(len(mf.tracks), 4)
        self.assertEqual(mf.ticksPerQuarterNote, 1024)
        self.assertEqual(mf.ticksPerSecond, None)

        # try to write contents
        fileLikeOpen = StringIO.StringIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

        # random files from the internet
        fp = os.path.join(dirLib, 'test04.mid')
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        self.assertEqual(len(mf.tracks), 18)
        self.assertEqual(mf.ticksPerQuarterNote,480)
        self.assertEqual(mf.ticksPerSecond, None)

        # try to write contents
        fileLikeOpen = StringIO.StringIO()
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()

#         mf = MidiFile()
#         mf.open(fp)
#         mf.read()
#         mf.close()


    def testInternalDataModel(self):

        dir = common.getPackageDir(relative=False, remapSep=os.sep)
        for fp in dir:
            if fp.endswith('midi'):
                break

        dirLib = os.path.join(fp, 'testPrimitive')
        # a simple file created in athenacl
        fp = os.path.join(dirLib, 'test01.mid')
        environLocal.printDebug([fp])
        mf = MidiFile()
        mf.open(fp)
        mf.read()
        mf.close()

        track2 = mf.tracks[1]
        # defines a channel object for each of 16 channels
        #self.assertEqual(len(track2.channels), 16)
        # length seems to be the size of midi data in this track
        self.assertEqual(track2.length, 255)

        # a list of events
        self.assertEqual(len(track2.events), 116)

        i = 0
        while i < len(track2.events)-1:
            self.assertTrue(isinstance(track2.events[i], DeltaTime))
            self.assertTrue(isinstance(track2.events[i+1], MidiEvent))

            #environLocal.printDebug(['sample events: ', track2.events[i]])
            #environLocal.printDebug(['sample events: ', track2.events[i+1]])
            i += 2

        # first object is delta time
        # all objects are pairs of delta time, event


    def testBasicExport(self):

        mt = MidiTrack(1)
        # duration, pitch, velocity
        data = [[1024, 60, 90], [1024, 50, 70], [1024, 51, 120],[1024, 62, 80],
                ]
        t = 0
        tLast = 0
        for d, p, v in data:
            dt = DeltaTime(mt)
            dt.time = t - tLast
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt)
            me.type = "NOTE_ON"
            me.channel = 1
            me.time = None #d
            me.pitch = p
            me.velocity = v
            mt.events.append(me)

            # add note off / velocity zero message
            dt = DeltaTime(mt)
            dt.time = d
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt)
            me.type = "NOTE_ON"
            me.channel = 1
            me.time = None #d
            me.pitch = p
            me.velocity = 0
            mt.events.append(me)

            tLast = t + d # have delta to note off
            t += d # next time

        # add end of track
        dt = DeltaTime(mt)
        dt.time = 0
        mt.events.append(dt)

        me = MidiEvent(mt)
        me.type = "END_OF_TRACK"
        me.channel = 1
        me.data = '' # must set data to empty string
        mt.events.append(me)

#        for e in mt.events:
#            print e

        mf = MidiFile()
        mf.ticksPerQuarterNote = 1024 # cannot use: 10080
        mf.tracks.append(mt)

        
        fileLikeOpen = StringIO.StringIO()
        #mf.open('/src/music21/music21/midi/out.mid', 'wb')
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()


    def testSetPitchBend(self):
        mt = MidiTrack(1)
        me = MidiEvent(mt)
        me.setPitchBend(0)
        me.setPitchBend(200) # 200 cents should be max range
        me.setPitchBend(-200) # 200 cents should be max range


    def testWritePitchBendA(self):

        mt = MidiTrack(1)

            
#(0 - 16383). The pitch value affects all playing notes on the current channel. Values below 8192 decrease the pitch, while values above 8192 increase the pitch. The pitch range may vary from instrument to instrument, but is usually +/-2 semi-tones.
        #pbValues = [0, 5, 10, 15, 20, 25, 30, 35, 40, 50] 
        pbValues = [0, 25, 0, 50, 0, 100, 0, 150, 0, 200] 
        pbValues += [-x for x in pbValues]

        # duration, pitch, velocity
        data = [[1024, 60, 90]] * 20
        t = 0
        tLast = 0
        for i, e in enumerate(data):
            d, p, v = e
            
            dt = DeltaTime(mt)
            dt.time = t - tLast
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt, type="PITCH_BEND", channel=1)
            #environLocal.printDebug(['creating event:', me, 'pbValues[i]', pbValues[i]])
            me.time = None #d
            me.setPitchBend(pbValues[i]) # set values in cents
            mt.events.append(me)

            dt = DeltaTime(mt)
            dt.time = t - tLast
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt, type="NOTE_ON", channel=1)
            me.time = None #d
            me.pitch = p
            me.velocity = v
            mt.events.append(me)

            # add note off / velocity zero message
            dt = DeltaTime(mt)
            dt.time = d
            # add to track events
            mt.events.append(dt)

            me = MidiEvent(mt, type='NOTE_ON', channel=1)
            me.time = None #d
            me.pitch = p
            me.velocity = 0
            mt.events.append(me)

            tLast = t + d # have delta to note off
            t += d # next time

        # add end of track
        dt = DeltaTime(mt)
        dt.time = 0
        mt.events.append(dt)

        me = MidiEvent(mt)
        me.type = "END_OF_TRACK"
        me.channel = 1
        me.data = '' # must set data to empty string
        mt.events.append(me)

        # try setting different channels
        mt.setChannel(3)

        mf = MidiFile()
        mf.ticksPerQuarterNote = 1024 # cannot use: 10080
        mf.tracks.append(mt)

        
        fileLikeOpen = StringIO.StringIO()
        #mf.open('/_scratch/test.mid', 'wb')
        mf.openFileLike(fileLikeOpen)
        mf.write()
        mf.close()


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []

if __name__ == "__main__":
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof

