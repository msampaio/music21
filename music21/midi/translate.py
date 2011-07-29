# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         midi.translate.py
# Purpose:      Translate MIDI and music21 objects
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2010-2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


#Quantization takes place on the stream...


import unittest
import math
import copy

import music21
from music21 import midi as midiModule
from music21 import defaults
from music21 import common

# modules that import this include stream.py, chord.py, note.py
# thus, cannot import these here

from music21 import environment
_MOD = "midi.translate.py"  
environLocal = environment.Environment(_MOD)




#-------------------------------------------------------------------------------
class TranslateException(Exception):
    pass


#-------------------------------------------------------------------------------
# Durations

def offsetToMidi(o):
    '''Convert an offset value to MIDI ticks.
    '''
    return int(round(o * defaults.ticksPerQuarter))

def durationToMidi(d):
    if d._quarterLengthNeedsUpdating:
        d.updateQuarterLength()
    return int(round(d.quarterLength * defaults.ticksPerQuarter))

def midiToDuration(ticks, ticksPerQuarter=None, inputM21DurationObject=None):
    '''    
    Converts a number of MIDI Ticks to a music21 duration.Duration() object.
    
    
    Optional parameters include ticksPerQuarter -- in case something other
    than the default.ticksPerQuarter (1024) is used in this file.  And
    it can take a music21 duration.Duration() object to modify (this is
    what 
    
    
    >>> from music21 import *
    >>> d = midi.translate.midiToDuration(1024)
    >>> d
    <music21.duration.Duration 1.0>
    >>> d.type
    'quarter'
    '''
    if inputM21DurationObject is None:
        from music21 import duration
        d = duration.Duration()
    else:
        d = inputM21DurationObject

    if ticksPerQuarter == None:
        ticksPerQuarter = defaults.ticksPerQuarter
    # given a value in ticks
    d._qtrLength = float(ticks) / ticksPerQuarter
    d._componentsNeedUpdating = True
    d._quarterLengthNeedsUpdating = False
    return d




#-------------------------------------------------------------------------------
# utility functions for getting commonly used event


def _getStartEvents(mt=None, channel=1, instrumentObj=None):
    '''Provide a list of events found at the beginning of a track.

    A MidiTrack reference can be provided via the `mt` parameter.
    '''
    events = []
    if instrumentObj is None or instrumentObj.bestName() is None:
        partName = ''
    else:
        partName = instrumentObj.bestName()

    dt = midiModule.DeltaTime(mt, channel=channel)
    dt.time = 0
    events.append(dt)

    me = midiModule.MidiEvent(mt, channel=channel)
    me.type = "SEQUENCE_TRACK_NAME"
    me.time = 0 # always at zero?
    me.data = partName
    events.append(me)

    # additional allocation of instruments may happen elsewhere
    # this may lead to two program changes happening at time zero
    # however, this assures that the program change happens before the 
    # the clearing of the pitch bend data
    if instrumentObj is not None and instrumentObj.midiProgram is not None:
        sub = instrumentToMidiEvents(instrumentObj, includeDeltaTime=True, 
                                    channel=channel)
        events += sub

    return events


def getEndEvents(mt=None, channel=1):
    '''Provide a list of events found at the end of a track.
    '''
    events = []

    dt = midiModule.DeltaTime(mt, channel=channel)
    dt.time = 0
    events.append(dt)

    me = midiModule.MidiEvent(mt)
    me.type = "END_OF_TRACK"
    me.channel = channel
    me.data = '' # must set data to empty string
    events.append(me)

    return events





#-------------------------------------------------------------------------------
# Notes

def midiEventsToNote(eventList, ticksPerQuarter=None, inputM21=None):
    '''Convert from a list of MIDI message to a music21 note

    The `inputM21` parameter can be a Note or None; in the case of None, a Note object is created. 

    >>> from music21 import *

    >>> mt = midi.MidiTrack(1)
    >>> dt1 = midi.DeltaTime(mt)
    >>> dt1.time = 1024

    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "NOTE_ON"
    >>> me1.pitch = 45
    >>> me1.velocity = 94

    >>> dt2 = midi.DeltaTime(mt)
    >>> dt2.time = 2048

    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "NOTE_ON"
    >>> me1.pitch = 45
    >>> me1.velocity = 0

    >>> n = midiEventsToNote([dt1, me1, dt2, me1])
    >>> n.pitch
    A2
    >>> n.duration.quarterLength
    1.0
    '''
    if inputM21 == None:
        from music21 import note
        n = note.Note()
    else:
        n = inputM21

    if ticksPerQuarter == None:
        ticksPerQuarter = defaults.ticksPerQuarter

    # pre sorted from a stream
    if len(eventList) == 2:
        tOn, eOn = eventList[0]
        tOff, eOff = eventList[1]

    # a representation closer to stream
    elif len(eventList) == 4:
        # delta times are first and third
        dur = eventList[2].time - eventList[0].time
        # shift to start at zero; only care about duration here
        tOn, eOn = 0, eventList[1]
        tOff, eOff = dur, eventList[3]
    else:
        raise TranslateException('cannot handle MIDI event list in the form: %r', eventList)

    n.pitch.midi = eOn.pitch
    # here we are handling an occasional error that probably should not happen
    # TODO: handle chords
    if (tOff - tOn) != 0:
        n.duration.midi = (tOff - tOn), ticksPerQuarter
    else:       
        #environLocal.printDebug(['cannot translate found midi event with zero duration:', eOn, n])
        # for now, substitute 1
        n.quarterLength = 1

    return n


def noteToMidiEvents(inputM21, includeDeltaTime=True, channel=1):
    '''Translate Note to four MIDI events.

    >>> from music21 import *
    >>> n1 = note.Note()
    >>> eventList = noteToMidiEvents(n1)
    >>> eventList
    [<MidiEvent DeltaTime, t=0, track=None, channel=1>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=60, velocity=90>, <MidiEvent DeltaTime, t=1024, track=None, channel=1>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=60, velocity=0>]
    >>> n1.duration.quarterLength = 2.5
    >>> eventList = noteToMidiEvents(n1)
    >>> eventList
    [<MidiEvent DeltaTime, t=0, track=None, channel=1>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=60, velocity=90>, <MidiEvent DeltaTime, t=2560, track=None, channel=1>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=60, velocity=0>]
    '''
    n = inputM21

    mt = None # use a midi track set to None
    eventList = []

    if includeDeltaTime:
        dt = midiModule.DeltaTime(mt, channel=channel)
        dt.time = 0 # set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

    me1 = midiModule.MidiEvent(mt)
    me1.type = "NOTE_ON"
    me1.channel = channel
    me1.time = None # not required
    #me1.pitch = n.midi
    me1.pitch = n.pitch.getMidiPreCentShift() # will shift later, do not round
    if not n.pitch.isTwelveTone():
        me1.centShift = n.pitch.getCentShiftFromMidi()
    me1.velocity = 90 # default, can change later
    eventList.append(me1)

    if includeDeltaTime:
        # add note off / velocity zero message
        dt = midiModule.DeltaTime(mt, channel=channel)
        dt.time = n.duration.midi
        # add to track events
        eventList.append(dt)

    me2 = midiModule.MidiEvent(mt)
    me2.type = "NOTE_OFF"
    me2.channel = channel
    me2.time = None #d
    #me2.pitch = n.midi
    me2.pitch = n.pitch.getMidiPreCentShift() # will shift later, do not round
    me2.pitchSpace = n.ps
    if not n.pitch.isTwelveTone():
        me2.centShift = n.pitch.getCentShiftFromMidi()

    me2.velocity = 0 # must be zero
    eventList.append(me2)

    # set correspondence
    me1.correspondingEvent = me2
    me2.correspondingEvent = me1

    return eventList 



def noteToMidiFile(inputM21): 
    '''
    >>> from music21 import note
    >>> n1 = note.Note()
    >>> n1.quarterLength = 6
    >>> mf = noteToMidiFile(n1)
    >>> mf.tracks[0].events
    [<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=1, data=''>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=None, track=1, channel=1, pitch=60, velocity=90>, <MidiEvent DeltaTime, t=6144, track=1, channel=1>, <MidiEvent NOTE_OFF, t=None, track=1, channel=1, pitch=60, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent END_OF_TRACK, t=None, track=1, channel=1, data=''>]
    '''
    n = inputM21
    mt = midiModule.MidiTrack(1)
    mt.events += _getStartEvents(mt)
    mt.events += noteToMidiEvents(n)
    mt.events += getEndEvents(mt)

    # set all events to have this track
    mt.updateEvents()

    mf = midiModule.MidiFile()
    mf.tracks = [mt]
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf




#-------------------------------------------------------------------------------
# Chords

def midiEventsToChord(eventList, ticksPerQuarter=None, inputM21=None):
    '''

    >>> from music21 import *
    >>> mt = midi.MidiTrack(1)

    >>> dt1 = midi.DeltaTime(mt)
    >>> dt1.time = 0

    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "NOTE_ON"
    >>> me1.pitch = 45
    >>> me1.velocity = 94

    >>> dt2 = midi.DeltaTime(mt)
    >>> dt2.time = 0

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = "NOTE_ON"
    >>> me2.pitch = 46
    >>> me2.velocity = 94


    >>> dt3 = midi.DeltaTime(mt)
    >>> dt3.time = 2048

    >>> me3 = midi.MidiEvent(mt)
    >>> me3.type = "NOTE_OFF"
    >>> me3.pitch = 45
    >>> me3.velocity = 0

    >>> dt4 = midi.DeltaTime(mt)
    >>> dt4.time = 0

    >>> me4 = midi.MidiEvent(mt)
    >>> me4.type = "NOTE_OFF"
    >>> me4.pitch = 46
    >>> me4.velocity = 0

    >>> c = midiEventsToChord([dt1, me1, dt2, me2, dt3, me3, dt4, me4])
    >>> c
    <music21.chord.Chord A2 B-2>
    >>> c.duration.quarterLength
    2.0
    '''
    if inputM21 == None:
        from music21 import chord
        c = chord.Chord()
    else:
        c = inputM21

    if ticksPerQuarter == None:
        ticksPerQuarter = defaults.ticksPerQuarter

    from music21 import pitch
    pitches = []

    # this is a format provided by the Stream conversion of 
    # midi events; it pre groups events for a chord together in nested pairs
    # of abs start time and the event object
    if isinstance(eventList, list) and isinstance(eventList[0], list):
        # pairs of pairs
        for onPair, offPair in eventList:
            tOn, eOn = onPair
            tOff, eOff = offPair

            p = pitch.Pitch()
            p.midi = eOn.pitch
            pitches.append(p)

    # assume it is  a flat list        
    else:
        onEvents = eventList[:(len(eventList) / 2)]
        offEvents = eventList[(len(eventList) / 2):]
        # first is always delta time
        tOn = onEvents[0].time
        tOff = offEvents[0].time

        # create pitches for the odd on Events:
        for i in range(1, len(onEvents), 2):
            p = pitch.Pitch()
            p.midi = onEvents[i].pitch
            pitches.append(p)

    c.pitches = pitches
    # can simply use last-assigned pair of tOff, tOn
    if (tOff - tOn) != 0:
        c.duration.midi = (tOff - tOn), ticksPerQuarter
    else:
        #environLocal.printDebug(['cannot translate found midi event with zero duration:', eventList, c])
        # for now, substitute 1
        c.quarterLength = 1    
    return c


def chordToMidiEvents(inputM21, includeDeltaTime=True):
    '''
    >>> from music21 import *
    >>> c = chord.Chord(['c3','g#4', 'b5'])
    >>> eventList = chordToMidiEvents(c)
    >>> eventList
    [<MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=48, velocity=90>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=68, velocity=90>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_ON, t=None, track=None, channel=1, pitch=83, velocity=90>, <MidiEvent DeltaTime, t=1024, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=48, velocity=0>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=68, velocity=0>, <MidiEvent DeltaTime, t=0, track=None, channel=None>, <MidiEvent NOTE_OFF, t=None, track=None, channel=1, pitch=83, velocity=0>]

    '''
    mt = None # midi track 
    eventList = []
    c = inputM21

    # temporary storage for setting correspondance
    noteOn = []
    noteOff = [] 

    for i in range(len(c.pitches)):
        pitchObj = c.pitches[i]

        if includeDeltaTime:
            dt = midiModule.DeltaTime(mt)
            # for a chord, only the first delta time should have the offset
            # here, all are zero
            dt.time = 0 # set to zero; will be shifted later as necessary
            # add to track events
            eventList.append(dt)

        me = midiModule.MidiEvent(mt)
        me.type = "NOTE_ON"
        me.channel = 1
        me.time = None # not required
        me.pitch = pitchObj.midi
        if not pitchObj.isTwelveTone():
            me.centShift =  pitchObj.getCentShiftFromMidi()
        me.velocity = 90 # default, can change later
        eventList.append(me)
        noteOn.append(me)

    # must create each note on in chord before each note on
    for i in range(len(c.pitches)):
        pitchObj = c.pitches[i]

        if includeDeltaTime:
            # add note off / velocity zero message
            dt = midiModule.DeltaTime(mt)
            # for a chord, only the first delta time should have the dur
            if i == 0:
                dt.time = c.duration.midi
            else:
                dt.time = 0
            eventList.append(dt)

        me = midiModule.MidiEvent(mt)
        me.type = "NOTE_OFF"
        me.channel = 1
        me.time = None #d
        me.pitch = pitchObj.midi
        if not pitchObj.isTwelveTone():
            me.centShift =  pitchObj.getCentShiftFromMidi()
        me.velocity = 0 # must be zero
        eventList.append(me)
        noteOff.append(me)

    # set correspondence
    for i, meOn in enumerate(noteOn):
        meOff = noteOff[i]
        meOn.correspondingEvent = meOff
        meOff.correspondingEvent = meOn

    return eventList 



def chordToMidiFile(inputM21): 
    # this can be consolidated with noteToMidiFile
    c = inputM21

    mt = midiModule.MidiTrack(1)
    mt.events += _getStartEvents(mt)
    mt.events += chordToMidiEvents(c)
    mt.events += getEndEvents(mt)

    # set all events to have this track
    mt.updateEvents()

    mf = midiModule.MidiFile()
    mf.tracks = [mt]
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf



#-------------------------------------------------------------------------------
def instrumentToMidiEvents(inputM21, includeDeltaTime=True, 
                            midiTrack=None, channel=1):
    inst = inputM21
    mt = midiTrack # midi track 
    events = []
    if includeDeltaTime:
        dt = midiModule.DeltaTime(mt, channel=channel)
        dt.time = 0
        events.append(dt)
    me = midiModule.MidiEvent(mt)
    me.type = "PROGRAM_CHANGE"
    me.time = 0 
    me.channel = channel
    me.data = inst.midiProgram # key step
    events.append(me)
    return events




#-------------------------------------------------------------------------------
# Meta events

def midiEventsToTimeSignature(eventList):
    '''Convert a single MIDI event into a music21 TimeSignature object.

    >>> from music21 import *
    >>> mt = midi.MidiTrack(1)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "TIME_SIGNATURE"
    >>> me1.data = midi.putNumbersAsList([3, 1, 24, 8]) # 3/2 time
    >>> ts = midiEventsToTimeSignature(me1)
    >>> ts
    <music21.meter.TimeSignature 3/2>

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = "TIME_SIGNATURE"
    >>> me2.data = midi.putNumbersAsList([3, 4]) # 3/16 time
    >>> ts = midiEventsToTimeSignature(me2)
    >>> ts
    <music21.meter.TimeSignature 3/16>

    '''
    # http://www.sonicspot.com/guide/midifiles.html
    # The time signature defined with 4 bytes, a numerator, a denominator, a metronome pulse and number of 32nd notes per MIDI quarter-note. The numerator is specified as a literal value, but the denominator is specified as (get ready) the value to which the power of 2 must be raised to equal the number of subdivisions per whole note. For example, a value of 0 means a whole note because 2 to the power of 0 is 1 (whole note), a value of 1 means a half-note because 2 to the power of 1 is 2 (half-note), and so on. 

    #The metronome pulse specifies how often the metronome should click in terms of the number of clock signals per click, which come at a rate of 24 per quarter-note. For example, a value of 24 would mean to click once every quarter-note (beat) and a value of 48 would mean to click once every half-note (2 beats). And finally, the fourth byte specifies the number of 32nd notes per 24 MIDI clock signals. This value is usually 8 because there are usually 8 32nd notes in a quarter-note. At least one Time Signature Event should appear in the first track chunk (or all track chunks in a Type 2 file) before any non-zero delta time events. If one is not specified 4/4, 24, 8 should be assumed.
    from music21 import meter

    if not common.isListLike(eventList):
        event = eventList
    else: # get the second event; first is delta time
        event = eventList[1]

    # time signature is 4 byte encoding
    post = midiModule.getNumbersAsList(event.data)

    n = post[0]
    d = pow(2, post[1])
    ts = meter.TimeSignature('%s/%s' % (n, d))
    return ts

def timeSignatureToMidiEvents(ts, includeDeltaTime=True):
    '''Translate a m21 TiemSignature to a pair of events, including a DeltaTime.

    >>> from music21 import *
    >>> ts = meter.TimeSignature('5/4')
    >>> eventList = timeSignatureToMidiEvents(ts)
    >>> eventList[0]
    <MidiEvent DeltaTime, t=0, track=None, channel=None>
    >>> eventList[1]
    <MidiEvent TIME_SIGNATURE, t=None, track=None, channel=1, data='\\x05\\x02\\x18\\x08'>
    '''
    mt = None # use a midi track set to None

    eventList = []

    if includeDeltaTime:
        dt = midiModule.DeltaTime(mt)
        dt.time = 0 # set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

    n = ts.numerator
    # need log base 2 to solve for exponent of 2
    # 1 is 0, 2 is 1, 4 is 2, 16 is 4, etc
    d = int(math.log(ts.denominator, 2))
    metroClick = 24 # clock signals per click, clicks are 24 per quarter
    subCount = 8 # number of 32 notes in a quarternote

    me = midiModule.MidiEvent(mt)
    me.type = "TIME_SIGNATURE"
    me.channel = 1
    me.time = None # not required
    me.data = midiModule.putNumbersAsList([n, d, metroClick, subCount])
    eventList.append(me)

    return eventList 



def midiEventsToKeySignature(eventList):
    '''Convert a single MIDI event into a music21 TimeSignature object.

    >>> from music21 import *
    >>> mt = midi.MidiTrack(1)
    >>> me1 = midi.MidiEvent(mt)
    >>> me1.type = "KEY_SIGNATURE"
    >>> me1.data = midi.putNumbersAsList([2, 0]) # d major
    >>> ks = midiEventsToKeySignature(me1)
    >>> ks
    <music21.key.KeySignature of 2 sharps>

    >>> me2 = midi.MidiEvent(mt)
    >>> me2.type = "KEY_SIGNATURE"
    >>> me2.data = midi.putNumbersAsList([-2, 0]) # b- major
    >>> me2.data
    '\\xfe\\x00'
    >>> midi.getNumbersAsList(me2.data)
    [254, 0]
    >>> ks = midiEventsToKeySignature(me2)
    >>> ks
    <music21.key.KeySignature of 2 flats>

    '''
    # This meta event is used to specify the key (number of sharps or flats) and scale (major or minor) of a sequence. A positive value for the key specifies the number of sharps and a negative value specifies the number of flats. A value of 0 for the scale specifies a major key and a value of 1 specifies a minor key.
    from music21 import key

    if not common.isListLike(eventList):
        event = eventList
    else: # get the second event; first is delta time
        event = eventList[1]
    post = midiModule.getNumbersAsList(event.data)

    if post[0] > 12:
        # flip around 256
        sharpCount = post[0] - 256 # need negative values
    else:
        sharpCount = post[0]

    #environLocal.printDebug(['midiEventsToKeySignature', post, sharpCount])

    # first value is number of sharp, or neg for number of flat
    ks = key.KeySignature(sharpCount)

    if post[1] == 0:
        ks.mode = 'major'
    if post[1] == 1:
        ks.mode = 'minor'
    return ks

def keySignatureToMidiEvents(ks, includeDeltaTime=True):
    '''Convert a single MIDI event into a music21 TimeSignature object.

    >>> from music21 import key
    >>> ks = key.KeySignature(2)
    >>> ks
    <music21.key.KeySignature of 2 sharps>
    >>> eventList = keySignatureToMidiEvents(ks)
    >>> eventList[1]
    <MidiEvent KEY_SIGNATURE, t=None, track=None, channel=1, data='\\x02\\x00'>

    >>> ks = key.KeySignature(-5)
    >>> ks
    <music21.key.KeySignature of 5 flats>
    >>> eventList = keySignatureToMidiEvents(ks)
    >>> eventList[1]
    <MidiEvent KEY_SIGNATURE, t=None, track=None, channel=1, data='\\xfb\\x00'>
    '''

    mt = None # use a midi track set to None

    eventList = []

    if includeDeltaTime:
        dt = midiModule.DeltaTime(mt)
        dt.time = 0 # set to zero; will be shifted later as necessary
        # add to track events
        eventList.append(dt)

    sharpCount = ks.sharps
    if ks.mode == 'minor':        
        mode = 1
    else: # major or None; must define one
        mode = 0

    me = midiModule.MidiEvent(mt)
    me.type = "KEY_SIGNATURE"
    me.channel = 1
    me.time = None # not required
    me.data = midiModule.putNumbersAsList([sharpCount, mode])
    eventList.append(me)

    return eventList 




#-------------------------------------------------------------------------------
# Streams



# TODO: phase out use of this for new multi-part processing
def _prepareStream(streamObj, instObj=None):
    '''Prepare a Stream for MIDI processing. This includes removing ties, flattening, and finding a first instrument if necessary. 

    An optional `instObj` parameter can be provided to force an instrument assignment.
    '''
    if instObj is None:
        # see if an instrument is defined in this or a parent stream
        # used for the first instrument definition
        instObj = streamObj.getInstrument(returnDefault=False)

    # have to be sorted, have to strip ties
    # retain containers to get all elements: time signatures, dynamics, etc
    s = streamObj.stripTies(inPlace=False, matchByPitch=False, 
        retainContainers=True)
    s = s.flat.sorted

    # see if there is an instrument in the first position of this Stream, if not
    # insert found instrument
    if instObj is not None:
        iStream = s.getElementsByClass('Instrument')
        if len(iStream) > 0 and iStream[0].getOffsetBySite(s) == 0:
            # already have an instrument in the first position
            pass
        else:
            s.insert(0, instObj)
    return s, instObj


def _getPacket(trackId, offset, midiEvent, obj, lastInstrument=None):
    '''Pack a dictionary of parameters for each event. Packets are used for sorting and configuring all note events. Includes offset, any cent shift, the midi event, and the source object.

    Offset and duration values stored here are MIDI ticks, not quarter lengths.
    '''
    post = {}
    post['trackId'] = trackId
    post['offset'] = offset # offset values are in midi ticks

    # update sort order here, as type may have been set after creation
    midiEvent.updateSortOrder()
    post['midiEvent'] = midiEvent
    post['obj'] = obj # keep a reference to the source object
    post['centShift'] = midiEvent.centShift
    # allocate channel later
    #post['channel'] = None
    if midiEvent.type != 'NOTE_OFF' and obj is not None:
        # store duration so as to calculate when the 
        # channel/pitch bend can be freed
        post['duration'] = durationToMidi(obj.duration)
    # note offs will have the same object ref, and seem like the have a 
    # duration when they do not
    else: 
        post['duration'] = 0

    # store last m21 instrument object, as needed to reset program changes
    post['lastInstrument'] = lastInstrument
    return post

def _streamToPackets(s, trackId=1):
    '''Convert a Stream to packets. This assumes that the Stream has already been flattened, ties have been stripped, and instruments, if necessary, have been added. 

    In converting from a Stream to MIDI, this is called first, resulting in a collection of packets by offset. Then, packets to events is called.
    '''
    # store all events by offset by offset without delta times
    # as (absTime, event)
    packetsByOffset = []
    lastInstrument = None

    # probably already flat and sorted
    for obj in s:
        classes = obj.classes
        # test: match to 'GeneralNote'
        if 'Note' in classes or 'Rest' in classes:
            if 'Rest' in classes:
                continue
            # get a list of midi events
            # using this property here is easier than using the above conversion
            # methods, as we do not need to know what the object is
            sub = noteToMidiEvents(obj, includeDeltaTime=False)
        elif 'Chord' in classes:
            sub = chordToMidiEvents(obj, includeDeltaTime=False)
        elif 'Dynamic' in classes:
            pass # configure dynamics
        elif 'TimeSignature' in classes:
            # return a pair of events
            sub = timeSignatureToMidiEvents(obj, includeDeltaTime=False)
        elif 'KeySignature' in classes:
            sub = keySignatureToMidiEvents(obj, includeDeltaTime=False)
        # first instrument will have been gathered above with get start elements
        elif 'Instrument' in classes:
            lastInstrument = obj # store last instrument
            sub = instrumentToMidiEvents(obj, includeDeltaTime=False)
        else: # other objects may have already been added
            continue

        # we process sub here, which is a list of midi events
        # for each event, we create a packet representation
        # all events: delta/note-on/delta/note-off
        # strip delta times
        packets = []
        for i in range(len(sub)):
            # store offset, midi event, object
            # add channel and pitch change also
            midiEvent = sub[i]
            if midiEvent.type != 'NOTE_OFF':
                # use offset
                p = _getPacket(trackId, 
                            offsetToMidi(obj.getOffsetBySite(s)), 
                            midiEvent, obj=obj, lastInstrument=lastInstrument)
                packets.append(p)
            # if its a note_off, use the duration to shift offset
            # midi events have already been created; 
            else: 
                p = _getPacket(trackId, 
                    offsetToMidi(obj.getOffsetBySite(s)) + durationToMidi(obj.duration), 
                    midiEvent, obj=obj, lastInstrument=lastInstrument)
                packets.append(p)
        packetsByOffset += packets

    # sorting is useful here, as we need these to be in order to assign last
    # instrument
    packetsByOffset.sort(
        cmp=lambda x,y: cmp(x['offset'], y['offset']) or
                        cmp(x['midiEvent'].sortOrder, y['midiEvent'].sortOrder)
        )

    # return packets and stream, as this flat stream should be retained
    return packetsByOffset


def _processPackets(packets, channelForInstrument={}, channelsDyanmic=[], 
        initChannelForTrack={}):
    '''Given a list of packets, assign each to a channel. Do each track one at time, based on the track id. Shift to different channels if a pitch bend is necessary. Keep track of which channels are available. Need to insert a program change in the empty channel to based on last instrument. Insert pitch bend messages as well, one for start of event, one for end of event.

    The `channels` argument is a list of channels to use.
    '''
    #allChannels = range(1, 10) + range(11, 17) # all but 10

    uniqueChannelEvents = {} # dict of (start, stop, usedChannel) : channel
    post = []
    usedTracks = []

    for p in packets:
        #environLocal.printDebug(['_processPackets', p['midiEvent'].track, p['trackId']])

        # must use trackId, as .track on MidiEvent is not yet set
        if p['trackId'] not in usedTracks:
            usedTracks.append(p['trackId'])

        # only need note_ons, as stored correspondingEvent attr can be used
        # to get noteOff
        if p['midiEvent'].type not in ['NOTE_ON']:
            # set all not note-off messages to init channel
            if p['midiEvent'].type not in ['NOTE_OFF']:
                p['midiEvent'].channel = p['initChannel']
            post.append(p) # add the non note_on packet first
            # if this is a note off, and has a cent shift, need to 
            # rest the pitch bend back to 0 cents
            if p['midiEvent'].type in ['NOTE_OFF']:
                #environLocal.printDebug(['got note-off', p['midiEvent']])
                # cent shift is set for note on and note off
                if p['centShift'] is not None:
                    # do not set channel, as already set
                    me = midiModule.MidiEvent(p['midiEvent'].track, 
                        type="PITCH_BEND", channel=p['midiEvent'].channel)
                    # note off stores note on's pitch; do not invert, simply
                    # set to zero
                    me.setPitchBend(0) 
                    pBendEnd = _getPacket(trackId=p['trackId'], 
                        offset=p['offset'], midiEvent=me, 
                        obj=None, lastInstrument=None)
                    post.append(pBendEnd)
                    #environLocal.printDebug(['adding pitch bend', pBendEnd])
            continue # store and continue

        # set default channel for all packets
        p['midiEvent'].channel = p['initChannel']

        # find a free channel       
        # if necessary, add pitch change at start of Note, 
        # cancel pitch change at end
        o = p['offset']
        oEnd = p['offset']+p['duration']

        channelExclude = [] # channels that cannot be used
        centShift = p['centShift'] # may be None

        #environLocal.printDebug(['\n\noffset', o, 'oEnd', oEnd, 'centShift', centShift])

        # iterate through all past events/channels, and find all
        # that are active and have a pitch bend
        for key in uniqueChannelEvents.keys():
            start, stop, usedChannel = key
            # if offset (start time) is in this range of a found event
            # or if any start or stop is within this span
            #if o >= start and o < stop: # found an offset that is used

            if ( (start >= o and start < oEnd) or
                 (stop > o and stop < oEnd) or
                 (start <= o and stop > o) or
                 (start < oEnd and stop > oEnd)
                ) : 
                # if there is a cent shift active in the already used channel
                #environLocal.printDebug(['matchedOffset overlap'])
                centShiftList = uniqueChannelEvents[key]
                if len(centShiftList) > 0:
                    # only add if unique
                    if usedChannel not in channelExclude:
                        channelExclude.append(usedChannel)
                # or if this event has shift, then we can exclude
                # the channel already used without a shift
                elif centShift is not None:
                    if usedChannel not in channelExclude:
                        channelExclude.append(usedChannel)
                            # cannot break early w/o sorting

        # if no channels are excluded, get a new channel
        #environLocal.printDebug(['post process channelExclude', channelExclude])
        if len(channelExclude) > 0: # only change if necessary
            ch = None       
            # iterate in order over all channels: lower will be added first
            for x in channelsDyanmic:
                if x not in channelExclude:
                    ch = x
                    break
            if ch is None:
                raise TranslateException('no unused channels available for microtone/instrument assignment')
            p['midiEvent'].channel = ch
            # change channel of note off; this is used above to turn off pbend
            p['midiEvent'].correspondingEvent.channel = ch
            #environLocal.printDebug(['set channel of correspondingEvent:', 
                                #p['midiEvent'].correspondingEvent])

            # TODO: must add program change, as we are now in a new 
            # channel; regardless of if we have a pitch bend (we may
            # move channels for a different reason  
            if p['lastInstrument'] is not None:
                meList = instrumentToMidiEvents(inputM21=p['lastInstrument'], 
                    includeDeltaTime=False, 
                    midiTrack=p['midiEvent'].track, channel=ch)
                pgmChangePacket = _getPacket(trackId=p['trackId'], 
                    offset=o, midiEvent=meList[0], # keep offset here
                    obj=None, lastInstrument=None)
                post.append(pgmChangePacket)


        else: # use the existing channel
            ch = p['midiEvent'].channel
            # always set corresponding event to the same channel
            p['midiEvent'].correspondingEvent.channel = ch

        #environLocal.printDebug(['assigning channel', ch, 'channelsDynamic', channelsDyanmic, "p['initChannel']", p['initChannel']])

        if centShift is not None:
            # add pitch bend
            me = midiModule.MidiEvent(p['midiEvent'].track, 
                                    type="PITCH_BEND", channel=ch)
            me.setPitchBend(centShift)
            pBendStart = _getPacket(trackId=p['trackId'], 
                offset=o, midiEvent=me, # keep offset here
                obj=None, lastInstrument=None)
            post.append(pBendStart)
            #environLocal.printDebug(['adding pitch bend', me])
            # removal of pitch bend will happen above with note off

        # key includes channel, so that durations can span once in each channel
        key = (p['offset'], p['offset']+p['duration'], ch)
        if key not in uniqueChannelEvents.keys():
            # need to count multiple instances of events on the same
            # span and in the same channel (fine if all have the same pitchbend
            uniqueChannelEvents[key] = [] 
        # always add the cent shift if it is not None
        if centShift is not None:
            uniqueChannelEvents[key].append(centShift)
        post.append(p) # add packet/ done after ch change or bend addition
        #environLocal.printDebug(['uniqueChannelEvents', uniqueChannelEvents])

    # this is called once at completion
    #environLocal.printDebug(['uniqueChannelEvents', uniqueChannelEvents])

    # after processing, collect all channels used
    foundChannels = []
    for start, stop, usedChannel in uniqueChannelEvents.keys(): # a list
        if usedChannel not in foundChannels:
            foundChannels.append(usedChannel)
#         for ch in chList:
#             if ch not in foundChannels:
#                 foundChannels.append(ch)
    #environLocal.printDebug(['foundChannels', foundChannels])
    #environLocal.printDebug(['usedTracks', usedTracks])


    # post processing of entire packet collection
    # for all used channels, create a zero pitch bend at time zero
    #for ch in foundChannels:
    # for each track, places a pitch bend in its initChannel
    for trackId in usedTracks:
        ch = initChannelForTrack[trackId]
        # use None for track; will get updated later
        me = midiModule.MidiEvent(track=trackId, type="PITCH_BEND", channel=ch)
        me.setPitchBend(0) 
        pBendEnd = _getPacket(trackId=trackId, 
            offset=0, midiEvent=me, obj=None, lastInstrument=None)
        post.append(pBendEnd)
        #environLocal.printDebug(['adding pitch bend for found channels', me])
    # this sort is necessary
    post.sort(
        cmp=lambda x,y: cmp(x['offset'], y['offset']) or
                        cmp(x['midiEvent'].sortOrder, y['midiEvent'].sortOrder)
        )

    # TODO: for each track, add an additional silent event to make sure
    # entire duration gets played

    # diagnostic display
    #for p in post: environLocal.printDebug(['proceessed packet', p])

    #post = packets
    return post



def _packetsToEvents(midiTrack, packetsSrc, trackIdFilter=None):
    '''Given a list of packets, sort all packets and add proper delta times. Optionally filters packets by track Id. 

    At this stage MIDI event objects have been created. The key process here is finding the adjacent time between events and adding DeltaTime events before each MIDI event.

    Delta time channel values are derived from the the previous midi event. 

    If `trackIdFilter` is not None, process only packets with a matching track id. this can be used to filter out events associated with a track. 
    '''
    #environLocal.printDebug(['_packetsToEvents', 'got packets:', len(packetsSrc)])
    # add delta times
    # first, collect only the packets for this track id
    packets = []
    if trackIdFilter is not None:
        for p in packetsSrc:
            if p['trackId'] == trackIdFilter:
                packets.append(p)
    else:
        packets = packetsSrc

    events = []
    lastOffset = 0
    for p in packets:
        me = p['midiEvent']
        if me.time is None:
            me.time = 0
        t = p['offset'] - lastOffset
        if t < 0:
            raise TranslateException('got a negative delta time')
        # set the channel from the midi event
        dt = midiModule.DeltaTime(midiTrack, time=t, channel=me.channel)
        #environLocal.printDebug(['packetsByOffset', p])
        events.append(dt)
        events.append(me)
        lastOffset = p['offset']
    #environLocal.printDebug(['_packetsToEvents', 'total events:', len(events)])
    return events

# DEPRECIATED: use of this function should be removed. instead, use
# streamsToMidiTracks and get the first element of the list
# this is necessary for allocating channels independent of track partitions
# def streamToMidiTrack(inputM21, instObj=None, trackId=1, channels=None):
#     '''Returns a :class:`music21.midi.base.MidiTrack` object based on the content of this Stream.
# 
#     This assumes that this Stream has only one Part. For Streams that contain sub-streams, use streamsToMidiTracks.
# 
#     DEPRECIATED: use of this function should be removed. instead, use streamsToMidiTracks and get the first element of the list this is necessary for allocating channels independent of track partitions.
# 
#     >>> from music21 import *
#     >>> s = stream.Stream()
#     >>> n = note.Note('g#')
#     >>> n.quarterLength = .5
#     >>> s.repeatAppend(n, 4)
#     >>> mt = streamsToMidiTracks(s)[0]
#     >>> len(mt.events)
#     22
#     '''
#     #environLocal.printDebug(['streamToMidiTrack()'])
#     s, instObj = _prepareStream(inputM21, instObj)
#     # assume one track per Stream
#     mt = midiModule.MidiTrack(trackId)
# 
#     # gets track name from instrument object
#     mt.events += _getStartEvents(mt, channel=1, instrumentObj=instObj) 
#     # convert stream to packets, attaching track id
#     packets = _streamToPackets(s, trackId)
#     # routine that dynamically assigns channels and adds microtones and 
#     # program changes
#     packets = _processPackets(packets)
#     # here events are created
#     mt.events += _packetsToEvents(mt, packets, trackIdFilter=trackId)
#     # must update all events with a ref to this MidiTrack
# 
#     mt.updateEvents()
#     mt.events += getEndEvents(mt)
#     return mt


def packetsToMidiTrack(packets, trackId=1, channels=None):
    '''Given packets already allocated with channel and/or instrument assignments, place these in a MidiTrack.

    Note that all packets can be sent; only those with matching trackIds will be collected into the resulting track

    The `channels` defines a collection of channels available for this Track

    Use _streamToPackets to convert the Stream to the packets
    '''
    primaryChannel = 1
    mt = midiModule.MidiTrack(trackId)
    # update based on primary ch   
    mt.events += _getStartEvents(mt, channel=primaryChannel) 
    # track id here filters 
    mt.events += _packetsToEvents(mt, packets, trackIdFilter=trackId)
    # must update all events with a ref to this MidiTrack
    mt.updateEvents() # sets this track as .track for all events
    mt.events += getEndEvents(mt, channel=primaryChannel)
    return mt




def midiTrackToStream(mt, ticksPerQuarter=None, quantizePost=True,
    inputM21=None):
    '''
    Note that quantization takes place in stream.py since it's useful not just for MIDI.


    >>> from music21 import *
    >>> import os
    >>> fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test05.mid')
    >>> mf = midi.MidiFile()
    >>> mf.open(fp)
    >>> mf.read()
    >>> mf.close()
    >>> len(mf.tracks)
    1
    >>> mt = mf.tracks[0] 
    >>> s = midiTrackToStream(mt)
    >>> len(s.notesAndRests)
    9
    '''
    #environLocal.printDebug(['midiTrackToStream(): got midi track: events', len(mt.events), 'ticksPerQuarter', ticksPerQuarter])

    if inputM21 == None:
        from music21 import stream
        s = stream.Stream()
    else:
        s = inputM21

    if ticksPerQuarter == None:
        ticksPerQuarter = defaults.ticksPerQuarter

    # need to build chords and notes
    from music21 import chord
    from music21 import note

    # get an abs start time for each event, discard deltas
    events = []
    t = 0

    # pair deltas with events, convert abs time
    # get even numbers
    # in some cases, the first event may not be a delta time, but
    # a SEQUENCE_TRACK_NAME or something else. thus, need to get
    # first delta time
    i = 0
    while i < len(mt.events):
        # in pairs, first should be delta time, second should be event
        #environLocal.printDebug(['midiTrackToStream(): index', 'i', i, mt.events[i]])
        #environLocal.printDebug(['midiTrackToStream(): index', 'i+1', i+1, mt.events[i+1]])

        # need to find pairs of delta time and events
        # in some cases, there are delta times that are out of order, or
        # packed in the beginning
        if mt.events[i].isDeltaTime() and not mt.events[i+1].isDeltaTime():
            td = mt.events[i]
            e = mt.events[i+1]
            t += td.time # increment time
            events.append([t, e])
            i += 2
            continue
        elif (not mt.events[i].isDeltaTime() and not 
            mt.events[i+1].isDeltaTime()):
            #environLocal.printDebug(['midiTrackToStream(): got two non delta times in a row'])
            i += 1
            continue
        elif mt.events[i].isDeltaTime() and mt.events[i+1].isDeltaTime():
            #environLocal.printDebug(['midiTrackToStream(): got two delta times in a row'])
            i += 1
            continue
        else:
            # cannot pair delta time to the next event; skip by 1
            #environLocal.printDebug(['cannot pair to delta time', mt.events[i]])
            i += 1
            continue


    #environLocal.printDebug(['raw event pairs', events])

    # need to pair note-on with note-off
    notes = [] # store pairs of pairs
    metaEvents = [] # store pairs of abs time, m21 object
    memo = [] # store already matched note off
    for i in range(len(events)):
        #environLocal.printDebug(['midiTrackToStream(): paired events', events[i][0], events[i][1]])

        if i in memo:
            continue
        t, e = events[i]
        # for each note on event, we need to search for a match in all future
        # events
        if e.isNoteOn():
            match = None
            for j in range(i+1, len(events)):
                if j in memo: 
                    continue
                tSub, eSub = events[j]
                if e.matchedNoteOff(eSub):
                    memo.append(j)
                    match = i, j
                    break
            if match is not None:
                i, j = match
                notes.append([events[i], events[j]])
            else:
                pass
                #environLocal.printDebug(['midiTrackToStream(): cannot find a note off for a note on', e])
        else:
            if e.type == 'TIME_SIGNATURE':
                # time signature should be 4 bytes
                metaEvents.append([t, midiEventsToTimeSignature(e)])
            elif e.type == 'KEY_SIGNATURE':
                metaEvents.append([t, midiEventsToKeySignature(e)])
            elif e.type == 'SET_TEMPO':
                pass
            elif e.type == 'INSTRUMENT_NAME':
                # TODO import instrument object
                pass
            elif e.type == 'PROGRAM_CHANGE':
                pass
            elif e.type == 'MIDI_PORT':
                pass

    # first create meta events
    for t, obj in metaEvents:
        #environLocal.printDebug(['insert midi meta event:', t, obj])
        s.insert(t / float(ticksPerQuarter), obj)

    #environLocal.printDebug(['midiTrackToStream(): found notes ready for Stream import', len(notes)])

    # collect notes with similar start times into chords
    # create a composite list of both notes and chords
    #composite = []
    chordSub = None
    i = 0
    if len(notes) > 1:
        while i < len(notes):
            # look at each note; get on time and event
            on, off = notes[i]
            t, e = on
            #environLocal.printDebug(['on, off', on, off, 'i', i, 'len(notes)', len(notes)])
            # go through all following notes; if there is only 1 note, this will 
            # not exectue
            for j in range(i+1, len(notes)):
                # look at each on time event
                onSub, offSub = notes[j]
                tSub, eSub = onSub
                # can set a tolerance for chordSubing; here at 1/16th
                # of a quarter
                if tSub - t <= ticksPerQuarter / 16:
                    if chordSub == None: # start a new one
                        chordSub = [notes[i]]
                    chordSub.append(notes[j])
                    continue # keep looping
                else: # no more matches; assuming chordSub tones are contiguous
                    if chordSub != None:
                        #composite.append(chordSub)
                        # create a chord here
                        c = chord.Chord()
                        c._setMidiEvents(chordSub, ticksPerQuarter)
                        o = notes[i][0][0] / float(ticksPerQuarter)
                        s._insertCore(o, c)
                        iSkip = len(chordSub)
                        chordSub = None
                    else: # just append the note
                        #composite.append(notes[i])
                        # create a note here
                        n = note.Note()
                        n._setMidiEvents(notes[i], ticksPerQuarter)
                        # the time is the first value in the first pair
                        # need to round, as floating point error is likely
                        o = notes[i][0][0] / float(ticksPerQuarter)
                        s._insertCore(o, n)
                        iSkip = 1
                    break # exit secondary loop
            i += iSkip
    elif len(notes) == 1: # rare case of just one note
        n = note.Note()
        n._setMidiEvents(notes[0], ticksPerQuarter)
        # the time is the first value in the first pair
        # need to round, as floating point error is likely
        o = notes[0][0][0] / float(ticksPerQuarter)
        s._insertCore(o, n)
                    
    s._elementsChanged()

    # quantize to nearest 16th
    if quantizePost:    
        s.quantize([8, 3], processOffsets=True, processDurations=True)

    # always need to fill gaps, as rests are not found in any other way
    s.makeRests(inPlace=True, fillGaps=True)
    return s



def streamsToMidiTracks(inputM21):
    '''Given a multipart stream, return a list of MIDI tracks. 
    '''
    from music21 import stream
    s = inputM21

    # return a list of MidiTrack objects
    midiTracks = []

    # TODO: may need to shift all time values to accomodate 
    # Streams that do not start at same time

    # temporary channel allocation
    allChannels = range(1, 10) + range(11, 17) # all but 10

    # store streams in uniform list
    procList = []
    if s.hasPartLikeStreams():
        for obj in s.getElementsByClass('Stream'):
            procList.append(obj)
    else:
        procList.append(s) # add single

    # first, create all packets by track
    packetStorage = {}
    allUniqueInstruments = [] # store program numbers
    trackCount = 1
    for s in procList:
        s = s.stripTies(inPlace=False, matchByPitch=False, 
            retainContainers=True)
        s = s.flat.sorted

        # get a first instrument; iterate over rest
        iStream = s.getElementsByClass('Instrument')
        if len(iStream) > 0 and iStream[0].getOffsetBySite(s) == 0:
            instObj = iStream[0]
        else:
            instObj = None
        # get all unique instrument ids
        if len(iStream) > 0:
            for i in iStream:
                if i.midiProgram not in allUniqueInstruments:
                    allUniqueInstruments.append(i.midiProgram)
        else: # get None as a placeholder for detaul
            if None not in allUniqueInstruments:
                allUniqueInstruments.append(None)

        # store packets in dictionary; keys are trackids
        packetStorage[trackCount] = {}
        packetStorage[trackCount]['rawPackets'] = _streamToPackets(s, 
                                               trackId=trackCount)
        packetStorage[trackCount]['initInstrument'] = instObj
        trackCount += 1

    channelForInstrument = {} # the instrument is the key
    channelsDyanmic = [] # remaining channels
    # create an entry for all unique instruments, assign channels
    # for each instrument, assign a channel; if we go above 16, that is fine
    # we just cannot use it and will take modulus later
    channelsAssigned = []
    for i, iPgm in enumerate(allUniqueInstruments): # values are program numbers
        # the the key is the program number; the values is the start channel
        if i < len(allChannels) - 1: # save at least on dynamic channel
            channelForInstrument[iPgm] = allChannels[i]
            channelsAssigned.append(allChannels[i])
        else: # just use 1, and deal with the mess: cannot allocate
            channelForInstrument[iPgm] = allChannels[0]
            channelsAssigned.append(allChannels[0])
            
    # get the dynamic channels, or those not assigned
    for ch in allChannels:
        if ch not in channelsAssigned:
            channelsDyanmic.append(ch)

    #environLocal.printDebug(['channelForInstrument', channelForInstrument, 'channelsDyanmic', channelsDyanmic, 'allChannels', allChannels, 'allUniqueInstruments', allUniqueInstruments])

    initChannelForTrack = {}
    # update packets with first channel
    for key, bundle in packetStorage.items():
        initChannelForTrack[key] = None # key is channel id
        bundle['initChannel'] = None # set for bundle too
        for p in bundle['rawPackets']:
            # get instrument
            instObj = bundle['initInstrument']

            if instObj is None:
                initCh = channelForInstrument[None]
            else: # use midi program
                initCh = channelForInstrument[instObj.midiProgram]
            p['initChannel'] = initCh
            # only set for bundle once
            if bundle['initChannel'] is None:
                bundle['initChannel'] = initCh
                initChannelForTrack[key] = initCh

    # combine all packets for processing of channel allocation 
    netPackets = []
    for bundle in packetStorage.values():
        netPackets += bundle['rawPackets']

    # process all channel assignments for all packets together
    netPackets = _processPackets(netPackets, 
        channelForInstrument=channelForInstrument, 
        channelsDyanmic=channelsDyanmic, 
        initChannelForTrack=initChannelForTrack)

    #environLocal.printDebug(['got netPackets:', len(netPackets), 'packetStorage keys (tracks)', packetStorage.keys()])
    # build each track, sorting out the appropriate packets based on track
    # ids
    for trackId in packetStorage.keys():   

        initChannel = packetStorage[trackId]['initChannel']
        instObj = packetStorage[trackId]['initInstrument']
        # TODO: for a given track id, need to find start/end channel
        mt = midiModule.MidiTrack(trackId) 
        # need to pass preferred channel here
        mt.events += _getStartEvents(mt, channel=initChannel, 
                                    instrumentObj=instObj) 
        # note that netPackets is must be passed here, and then be filtered
        # packets have been added to net packets
        mt.events += _packetsToEvents(mt, netPackets, trackIdFilter=trackId)
        mt.events += getEndEvents(mt, channel=initChannel)
        mt.updateEvents()
    # need to filter out packets only for the desired tracks
        midiTracks.append(mt)

    return midiTracks


def midiTracksToStreams(midiTracks, ticksPerQuarter=None, quantizePost=True,
    inputM21=None):
    '''Given a list of midiTracks, populate this Stream with sub-streams for each part. 
    '''
    from music21 import stream
    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21
    # store common elements such as time sig, key sig from conductor
    conductorTrack = stream.Stream()
    for mt in midiTracks:
        # not all tracks have notes defined; only creates parts for those
        # that do
        #environLocal.printDebug(['raw midi trakcs', mt])

        if mt.hasNotes(): 
            streamPart = stream.Part() # create a part instance for each part
            midiTrackToStream(mt, ticksPerQuarter, quantizePost, 
                              inputM21=streamPart)
#             streamPart._setMidiTracksPart(mt,
#                 ticksPerQuarter=ticksPerQuarter, quantizePost=quantizePost)
            s.insert(0, streamPart)
        else:
            # note: in some cases a track such as this might have metadata
            # such as the time sig, tempo, or other parameters
            midiTrackToStream(mt, ticksPerQuarter, quantizePost, 
                              inputM21=conductorTrack)
    #environLocal.printDebug(['show() conductorTrack elements'])
    # if we have time sig/key sig elements, add to each part
    for p in s.getElementsByClass('Stream'):
        for e in conductorTrack.getElementsByClass(
                            ('TimeSignature', 'KeySignature')):
            # create a deepcopy of the element so a flat does not cause
            # multiple references of the same
            eventCopy = copy.deepcopy(e)
            p.insert(e.getOffsetBySite(conductorTrack), eventCopy)
    return s


def streamToMidiFile(inputM21):
    '''
    >>> from music21 import *
    >>> s = stream.Stream()
    >>> n = note.Note('g#')
    >>> n.quarterLength = .5
    >>> s.repeatAppend(n, 4)
    >>> mf = streamToMidiFile(s)
    >>> len(mf.tracks)
    1
    >>> len(mf.tracks[0].events)
    22
    '''
    s = inputM21
    midiTracks = streamsToMidiTracks(s)

    # update track indices
    # may need to update channel information
    for i in range(len(midiTracks)):
        midiTracks[i].index = i + 1

    mf = midiModule.MidiFile()
    mf.tracks = midiTracks
    mf.ticksPerQuarterNote = defaults.ticksPerQuarter
    return mf



def midiFileToStream(mf, inputM21=None):
    '''
    >>> from music21 import *
    >>> import os
    >>> fp = os.path.join(common.getSourceFilePath(), 'midi', 'testPrimitive',  'test05.mid')
    >>> mf = midi.MidiFile()
    >>> mf.open(fp)
    >>> mf.read()
    >>> mf.close()
    >>> len(mf.tracks)
    1
    >>> s = midiFileToStream(mf)
    >>> len(s.flat.notesAndRests)
    9
    '''
    #environLocal.printDebug(['got midi file: tracks:', len(mf.tracks)])

    from music21 import stream
    if inputM21 == None:
        s = stream.Stream()
    else:
        s = inputM21

    if len(mf.tracks) == 0:
        raise StreamException('no tracks are defined in this MIDI file.')
    else:
        # create a stream for each tracks   
        # may need to check if tracks actually have event data
        midiTracksToStreams(mf.tracks, 
            ticksPerQuarter=mf.ticksPerQuarterNote, inputM21=s)
        #s._setMidiTracks(mf.tracks, mf.ticksPerQuarterNote)

    return s



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass

    def testNote(self):

        from music21 import note
        n1 = note.Note('A4')
        n1.quarterLength = 2.0
        eventList = n1.midiEvents
        self.assertEqual(len(eventList), 4)

        self.assertEqual(isinstance(eventList[0], midiModule.DeltaTime), True)
        self.assertEqual(isinstance(eventList[2], midiModule.DeltaTime), True)


        # translate eventList back to a note
        n2 = midiEventsToNote(eventList)
        self.assertEqual(n2.pitch.nameWithOctave, 'A4')
        self.assertEqual(n2.quarterLength, 2.0)


    def testTimeSignature(self):
        import copy
        from music21 import note, stream, meter
        n = note.Note()
        n.quarterLength = .5
        s = stream.Stream()
        for i in range(20):
            s.append(copy.deepcopy(n))

        s.insert(0, meter.TimeSignature('3/4'))
        s.insert(3, meter.TimeSignature('5/4'))
        s.insert(8, meter.TimeSignature('2/4'))

        
        mt = streamsToMidiTracks(s)[0]
        #self.assertEqual(str(mt.events), match)
        self.assertEqual(len(mt.events), 92)

        #s.show('midi')
        
        # get and compare just the time signatures
        mtAlt = streamsToMidiTracks(s.getElementsByClass('TimeSignature'))[0]

        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=1, data=''>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PITCH_BEND, t=0, track=1, channel=1, _parameter1=0, _parameter2=64>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x03\\x02\\x18\\x08'>, <MidiEvent DeltaTime, t=3072, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x05\\x02\\x18\\x08'>, <MidiEvent DeltaTime, t=5120, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x02\\x02\\x18\\x08'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent END_OF_TRACK, t=None, track=1, channel=1, data=''>]"""
        self.assertEqual(str(mtAlt.events), match)





    def testKeySignature(self):
        import copy
        from music21 import note, stream, meter, key
        n = note.Note()
        n.quarterLength = .5
        s = stream.Stream()
        for i in range(20):
            s.append(copy.deepcopy(n))

        s.insert(0, meter.TimeSignature('3/4'))
        s.insert(3, meter.TimeSignature('5/4'))
        s.insert(8, meter.TimeSignature('2/4'))

        s.insert(0, key.KeySignature(4))
        s.insert(3, key.KeySignature(-5))
        s.insert(8, key.KeySignature(6))

        mt = streamsToMidiTracks(s)[0]
        self.assertEqual(len(mt.events), 98)

        #s.show('midi')
        mtAlt = streamsToMidiTracks(s.getElementsByClass('TimeSignature'))[0]



    def testAnacrusisTiming(self):

        from music21 import corpus

        s = corpus.parse('bach/bwv103.6')

        # get just the soprano part
        soprano = s.parts['soprano']
        mts = streamsToMidiTracks(soprano)[0] # get one

        # first note-on is not delayed, even w anacrusis
        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=1, data=u'Soprano'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>]"""
       

        self.assertEqual(str(mts.events[:5]), match)

        # first note-on is not delayed, even w anacrusis
        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=1, data=u'Alto'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PITCH_BEND, t=0, track=1, channel=1, _parameter1=0, _parameter2=64>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent KEY_SIGNATURE, t=0, track=1, channel=1, data='\\x02\\x01'>]"""

        alto = s.parts['alto']
        mta = streamsToMidiTracks(alto)[0]

        self.assertEqual(str(mta.events[:10]), match)


        # try streams to midi tracks
        # get just the soprano part
        soprano = s.parts['soprano']
        mtList = streamsToMidiTracks(soprano)
        self.assertEqual(len(mtList), 1)

        # its the same as before
        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent SEQUENCE_TRACK_NAME, t=0, track=1, channel=1, data=u'Soprano'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PITCH_BEND, t=0, track=1, channel=1, _parameter1=0, _parameter2=64>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent PROGRAM_CHANGE, t=0, track=1, channel=1, data=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent KEY_SIGNATURE, t=0, track=1, channel=1, data='\\x02\\x01'>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent TIME_SIGNATURE, t=0, track=1, channel=1, data='\\x04\\x02\\x18\\x08'>]"""

        self.assertEqual(str(mtList[0].events[:12]), match)



    def testMidiProgramChangeA(self):
        from music21 import stream, instrument, note
        p1 = stream.Part()
        p1.append(instrument.Dulcimer())
        p1.repeatAppend(note.Note('g6', quarterLength=1.5), 4)
        
        p2 = stream.Part()
        p2.append(instrument.Tuba())
        p2.repeatAppend(note.Note('c1', quarterLength=2), 2)
        
        p3 = stream.Part()
        p3.append(instrument.TubularBells())
        p3.repeatAppend(note.Note('e4', quarterLength=1), 4)
        
        s = stream.Score()
        s.insert(0, p1)
        s.insert(0, p2)
        s.insert(0, p3)

        mts = streamsToMidiTracks(s)
        #p1.show()
        #s.show('midi')


    def testMidiProgramChangeB(self):

        from music21 import stream, instrument, note, scale
        import random

        iList = [instrument.Harpsichord, instrument.Clavichord, instrument.Accordion, instrument.Celesta, instrument.Contrabass, instrument.Viola, instrument.Harp, instrument.ElectricGuitar, instrument.Ukulele, instrument.Banjo, instrument.Piccolo, instrument.AltoSaxophone, instrument.Trumpet]

        sc = scale.MinorScale()
        pitches = sc.getPitches('c2', 'c5')
        random.shuffle(pitches)

        s = stream.Stream()
        for i in range(30):
            n = note.Note(pitches[i%len(pitches)])
            n.quarterLength = .5
            inst = iList[i%len(iList)]() # call to create instance
            s.append(inst)
            s.append(n)

        mts = streamsToMidiTracks(s)

        #s.show('midi')



    def testOverlappedEventsA(self):
        from music21 import corpus
        s = corpus.parse('bwv66.6')
        sFlat = s.flat
        mtList = streamsToMidiTracks(sFlat)
        self.assertEqual(len(mtList), 1)

        # its the same as before
        match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=65, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=66, velocity=90>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=61, velocity=90>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=58, velocity=90>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=54, velocity=90>, <MidiEvent DeltaTime, t=1024, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=66, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=61, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=58, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=54, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent END_OF_TRACK, t=None, track=1, channel=1, data=''>]"""


        self.assertEqual(str(mtList[0].events[-20:]), match)


    def testOverlappedEventsB(self):
        from music21 import stream, scale, note
        import random
        
        sc = scale.MajorScale()
        pitches = sc.getPitches('c2', 'c5')
        random.shuffle(pitches)
        
        dur = 16
        step = .5
        o = 0
        s = stream.Stream()
        for p in pitches:
            n = note.Note(p)
            n.quarterLength = dur - o
            s.insert(o, n)
            o = o + step

        mt = streamsToMidiTracks(s)[0]

        #s.plot('pianoroll')
        #s.show('midi')

    def testOverlappedEventsC(self):

        from music21 import stream, note, chord, meter, key

        s = stream.Stream()
        s.insert(key.KeySignature(3))
        s.insert(meter.TimeSignature('2/4'))
        s.insert(0, note.Note('c'))
        n = note.Note('g')
        n.pitch.microtone = 25
        s.insert(0, n)

        c = chord.Chord(['d','f','a'], type='half')
        c.pitches[1].microtone = -50
        s.append(c)

        pos = s.highestTime
        s.insert(pos, note.Note('e'))
        s.insert(pos, note.Note('b'))

        mt = streamsToMidiTracks(s)[0]

        #s.show('midi')

    def testExternalMidiProgramChangeB(self):

        from music21 import stream, instrument, note, scale
        import random

        iList = [instrument.Harpsichord, instrument.Clavichord, instrument.Accordion, 
                 instrument.Celesta, instrument.Contrabass, instrument.Viola, 
                 instrument.Harp, instrument.ElectricGuitar, instrument.Ukulele, 
                 instrument.Banjo, instrument.Piccolo, instrument.AltoSaxophone, 
                 instrument.Trumpet, instrument.Clarinet, instrument.Flute,
                 instrument.Violin, instrument.Soprano, instrument.Oboe,
                 instrument.Tuba, instrument.Sitar, instrument.Ocarina,
                 instrument.Piano]

        sc = scale.MajorScale()
        pitches = sc.getPitches('c2', 'c5')
        #random.shuffle(pitches)

        s = stream.Stream()
        for i, p in enumerate(pitches):
            n = note.Note(p)
            n.quarterLength = 1.5
            inst = iList[i]() # call to create instance
            s.append(inst)
            s.append(n)

 
        mts = streamsToMidiTracks(s)
        #s.show('midi')

        

    def testMicrotonalOutputA(self):
        from music21 import stream, note

        s = stream.Stream()
        s.append(note.Note('c4', type='whole')) 
        s.append(note.Note('c~4', type='whole')) 
        s.append(note.Note('c#4', type='whole')) 
        s.append(note.Note('c#~4', type='whole')) 
        s.append(note.Note('d4', type='whole')) 

        #mts = streamsToMidiTracks(s)

        s.insert(0, note.Note('g3', quarterLength=10)) 
        mts = streamsToMidiTracks(s)

#         match = """[<MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=61, velocity=90>, <MidiEvent DeltaTime, t=2048, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=61, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=2>, <MidiEvent PITCH_BEND, t=0, track=1, channel=2, _parameter1=0, _parameter2=80>, <MidiEvent DeltaTime, t=0, track=1, channel=2>, <MidiEvent NOTE_ON, t=0, track=1, channel=2, pitch=61, velocity=90>, <MidiEvent DeltaTime, t=2048, track=1, channel=2>, <MidiEvent NOTE_OFF, t=0, track=1, channel=2, pitch=61, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=2>, <MidiEvent PITCH_BEND, t=0, track=1, channel=2, _parameter1=0, _parameter2=64>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_ON, t=0, track=1, channel=1, pitch=62, velocity=90>, <MidiEvent DeltaTime, t=2048, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=55, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent NOTE_OFF, t=0, track=1, channel=1, pitch=62, velocity=0>, <MidiEvent DeltaTime, t=0, track=1, channel=1>, <MidiEvent END_OF_TRACK, t=None, track=1, channel=1, data=''>]"""
#         self.assertEqual(str(mts[0].events[-20:]), match)
# 
# 
#         #s.show('midi', app='Logic Express')
#         s.show('midi')

        #print s.write('midi')
    def testMicrotonalOutputB(self):
        # a two-part stream
        from music21 import stream, note

        p1 = stream.Part()
        p1.append(note.Note('c4', type='whole')) 
        p1.append(note.Note('c~4', type='whole')) 
        p1.append(note.Note('c#4', type='whole')) 
        p1.append(note.Note('c#~4', type='whole')) 
        p1.append(note.Note('d4', type='whole')) 

        #mts = streamsToMidiTracks(s)
        p2 = stream.Part()
        p2.insert(0, note.Note('g2', quarterLength=20)) 

        # order here matters: this needs to be fixed
        s = stream.Score()
        s.insert(0, p1)
        s.insert(0, p2)

        mts = streamsToMidiTracks(s)
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[1].getChannels(),  [1, 2])
        #print mts
        #s.show('midi', app='Logic Express')
        #s.show('midi')

        # recreate with different order
        s = stream.Score()
        s.insert(0, p2)
        s.insert(0, p1)

        mts = streamsToMidiTracks(s)
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[1].getChannels(),  [1, 2])



    def testMicrotonalOutputC(self):
        # test instrument assignments
        from music21 import instrument, stream, note

        iList = [instrument.Harpsichord,  instrument.Viola, 
                    instrument.ElectricGuitar, instrument.Flute]

        # number of notes, ql, pitch
        pmtr = [(8, 1, 'C6'), (4, 2, 'G3'), (2, 4, 'E4'), (6, 1.25, 'C5')]

        s = stream.Score()
        for i, inst in enumerate(iList):
            p = stream.Part()
            p.insert(0, inst()) # must call instrument to create instance

            number, ql, pitchName = pmtr[i]
            for j in range(number):
                p.append(note.Note(pitchName, quarterLength=ql))
            s.insert(0, p)

        #s.show('midi')
        mts = streamsToMidiTracks(s)
        #print mts[0]
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[1].getChannels(),  [2])
        self.assertEqual(mts[2].getChannels(),  [3])
        self.assertEqual(mts[3].getChannels(),  [4])


    def testMicrotonalOutputD(self):
        # test instrument assignments with microtones
        from music21 import instrument, stream, note

        iList = [instrument.Harpsichord,  instrument.Viola, 
                    instrument.ElectricGuitar, instrument.Flute]

        # number of notes, ql, pitch
        pmtr = [(8, 1, ['C6']), (4, 2, ['G3', 'G~3']), (2, 4, ['E4', 'E5']), (6, 1.25, ['C5'])]

        s = stream.Score()
        for i, inst in enumerate(iList):
            p = stream.Part()
            p.insert(0, inst()) # must call instrument to create instance

            number, ql, pitchNameList = pmtr[i]
            for j in range(number):
                p.append(note.Note(pitchNameList[j%len(pitchNameList)], quarterLength=ql))
            s.insert(0, p)

        #s.show('midi')
        mts = streamsToMidiTracks(s)
        #print mts[0]
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[0].getProgramChanges(),  [6])

        self.assertEqual(mts[1].getChannels(),  [2, 5])
        self.assertEqual(mts[1].getProgramChanges(),  [41])

        self.assertEqual(mts[2].getChannels(),  [3, 6])
        self.assertEqual(mts[2].getProgramChanges(),  [26])
        #print mts[2]

        self.assertEqual(mts[3].getChannels(),  [4, 6])
        self.assertEqual(mts[3].getProgramChanges(),  [73])

        #s.show('midi')


    def testMicrotonalOutputE(self):

        from music21 import corpus, stream, interval
        s = corpus.parse('bwv66.6')
        p1 = s.parts[0]
        p2 = copy.deepcopy(p1)
        t = interval.Interval(0.5) # a sharp p4
        p2.transpose(t, inPlace=True)
        post = stream.Score()
        post.insert(0, p1)
        post.insert(0, p2)

        #post.show('midi')

        mts = streamsToMidiTracks(post)
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[0].getProgramChanges(),  [0])
        self.assertEqual(mts[1].getChannels(),  [1, 2])
        self.assertEqual(mts[1].getProgramChanges(),  [0])

        #post.show('midi', app='Logic Express')

    def testMicrotonalOutputF(self):

        from music21 import corpus, stream, interval
        s = corpus.parse('bwv66.6')
        p1 = s.parts[0]
        p2 = copy.deepcopy(p1)
        p3 = copy.deepcopy(p1)

        t1 = interval.Interval(12.5) # a sharp p4
        t2 = interval.Interval(-12.25) # a sharp p4
        p2.transpose(t1, inPlace=True)
        p3.transpose(t2, inPlace=True)
        post = stream.Score()
        post.insert(0, p1)
        post.insert(0, p2)
        post.insert(0, p3)

        #post.show('midi')

        mts = streamsToMidiTracks(post)
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[0].getProgramChanges(),  [0])
        self.assertEqual(mts[1].getChannels(),  [1, 2])
        self.assertEqual(mts[1].getProgramChanges(),  [0])
        self.assertEqual(mts[2].getChannels(),  [1, 2, 3])
        self.assertEqual(mts[2].getProgramChanges(),  [0])

        #post.show('midi', app='Logic Express')

    def testMicrotonalOutputG(self):

        from music21 import corpus, stream, interval, instrument
        s = corpus.parse('bwv66.6')
        p1 = s.parts[0]
        p1.remove(p1.getElementsByClass('Instrument')[0])
        p2 = copy.deepcopy(p1)
        p3 = copy.deepcopy(p1)
        
        t1 = interval.Interval(12.5) # a sharp p4
        t2 = interval.Interval(-7.25) # a sharp p4
        p2.transpose(t1, inPlace=True)
        p3.transpose(t2, inPlace=True)
        post = stream.Score()
        p1.insert(0, instrument.Dulcimer())
        post.insert(0, p1)
        p2.insert(0, instrument.Trumpet())
        post.insert(0.125, p2)
        p3.insert(0, instrument.ElectricGuitar())
        post.insert(0.25, p3)
        
        #post.show('midi')
        
        mts = streamsToMidiTracks(post)
        self.assertEqual(mts[0].getChannels(),  [1])
        self.assertEqual(mts[0].getProgramChanges(),  [15])
        
        self.assertEqual(mts[1].getChannels(),  [2, 4])
        self.assertEqual(mts[1].getProgramChanges(),  [56])
        
        #print mts[2]
        self.assertEqual(mts[2].getChannels(),  [3, 4, 5])
        self.assertEqual(mts[2].getProgramChanges(),  [26])

        #post.show('midi', app='Logic Express')




if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof

