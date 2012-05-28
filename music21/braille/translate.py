# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         translate.py
# Purpose:      music21 class which allows transcription of music21 data to braille
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

"""
Methods for exporting music21 data as braille. The most important method, and the only
one that is needed to translate music into braille, is :meth:`~music21.braille.translate.objectToBraille`.
This method, as well as the others, accept keyword arguments that serve to modify
the output. They divide into two categories, although they can all be passed in together.


Translate keywords:


* **inPlace** (False): If False, then :meth:`~music21.stream.Stream.makeNotation` is called
  on all :class:`~music21.stream.Measure`, :class:`~music21.stream.Part`, and 
  :class:`~music21.stream.PartStaff` instances. Copies of those objects are then
  used to transcribe the music. If True, the transcription is done "as is." 
  This is useful for strict transcription because sometimes :meth:`~music21.stream.Stream.makeNotation` 
  introduces some unwanted artifacts in the music.
* **debug** (False): If True, a braille-english representation of the music is returned. Useful
  for knowing how the music was interpreted by the braille transcriber.


Segment keywords:


* **cancelOutgoingKeySig** (True): If True, whenever a key signature change is encountered, the new
  signature should be preceded by the old one.
* **descendingChords** (True): If True, then chords are spelled around the highest note. If False,
  then chords are spelled around the lowest note. This keyword is overriden by any valid clefs 
  present in the music.
* **dummyRestLength** (None) For a given positive integer n, adds n "dummy rests" near the beginning 
  of a segment. Designed for test purposes, as the rests are used to demonstrate measure division at 
  the end of braille lines. 
* **maxLineLength** (40): The maximum amount of braille characters that should be present in a line of braille.
* **segmentBreaks** ([]): A list consisting of (measure number, offset start) tuples indicating where the
  music should be broken into segments.
* **showClefSigns** (False): If True, then clef signs are displayed. Since braille does not use clefs and
  staves to represent music, they would instead be shown for referential or historical purposes.
* **showFirstMeasureNumber** (True): If True, then a measure number is shown following the heading
  (if applicable) and preceding the music.
* **showHand** (None): If set to "right" or "left", the corresponding hand sign is shown before the music. In
  keyboard music, the hand signs are shown automatically.
* **showHeading** (True): If True, then a braille heading is created above the initial segment. A heading consists
  of an initial :class:`~music21.key.KeySignature`, :class:`~music21.meter.TimeSignature`,
  :class:`~music21.tempo.TempoText`, and :class:`~music21.tempo.MetronomeMark`, or any subset thereof. The heading
  is centered above the music automatically.
* **showLongSlursAndTiesTogether** (False), **showShortSlursAndTiesTogether** (False): If False, then the slur on 
  either side of the phrase is reduced by the amount that ties are present. If True, then slurs and ties are shown 
  together (i.e. the note can have both a slur and a tie).
* **slurLongPhraseWithBrackets** (True): If True, then the slur of a long phrase (4+ consecutive notes) is brailled
  using the bracket slur. If False, the double slur is used instead.
* **suppressOctaveMarks** (True): If True, then all octave marks are suppressed. Designed for test purposes, as
  octave marks were not presented in the Braille Music Transcription Manual until Chapter 7.
* **upperFirstInNoteFingering** (True)
"""

from music21 import metadata, stream, tinyNotation
from music21.braille import segment
import itertools
import music21
import unittest

#-------------------------------------------------------------------------------

def objectToBraille(music21Obj, **keywords):
    ur"""
    
    Translates an arbitrary object to braille.

    >>> from music21.braille import translate
    >>> from music21 import tinyNotation
    >>> samplePart = tinyNotation.TinyNotationStream("C4 D16 E F G# r4 e2.", "3/4")
    >>> print translate.objectToBraille(samplePart)    
    ⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠹⠵⠋⠛⠩⠓⠧⠀⠐⠏⠄⠣⠅


    For normal users, you'll just call this, which starts a text editor:


    >>> #_DOCS_SHOW samplePart.show('braille')
    ⠀⠀⠀⠀⠀⠀⠀⠼⠉⠲⠀⠀⠀⠀⠀⠀⠀
    ⠼⠁⠀⠸⠹⠵⠋⠛⠩⠓⠧⠀⠐⠏⠄⠣⠅


    Other examples:


    >>> from music21 import note
    >>> sampleNote = note.Note("C3")
    >>> print translate.objectToBraille(sampleNote)
    ⠸⠹
    
    >>> from music21 import dynamics
    >>> sampleDynamic = dynamics.Dynamic("fff")
    >>> print translate.objectToBraille(sampleDynamic)
    ⠜⠋⠋⠋
    """
    if isinstance(music21Obj, stream.Stream):
        return streamToBraille(music21Obj, **keywords)
    else:
        music21Measure = stream.Measure()
        music21Measure.append(music21Obj)
        keywords['inPlace'] = True
        return measureToBraille(music21Measure, **keywords)

def streamToBraille(music21Stream, **keywords):
    """
    Translates a :class:`~music21.stream.Stream` to braille.
    """
    
    if isinstance(music21Stream, stream.Part) or isinstance(music21Stream, tinyNotation.TinyNotationStream):
        return partToBraille(music21Stream, **keywords)
    if isinstance(music21Stream, stream.Measure):
        return measureToBraille(music21Stream, **keywords)
    keyboardParts = music21Stream.getElementsByClass(stream.PartStaff)
    if len(keyboardParts) == 2:
        return keyboardPartsToBraille(keyboardParts[0], keyboardParts[1], **keywords)
    if isinstance(music21Stream, stream.Score):
        return scoreToBraille(music21Stream, **keywords)
    if isinstance(music21Stream, stream.Opus):
        return opusToBraille(music21Stream, **keywords)
    raise BrailleTranslateException("Stream cannot be translated to Braille.")
    
def scoreToBraille(music21Score, **keywords):
    """
    Translates a :class:`~music21.stream.Score` to braille.    
    """
    allBrailleLines = []
    for music21Metadata in music21Score.getElementsByClass(metadata.Metadata):
        if music21Metadata.title is not None:
            allBrailleLines.append(unicode(music21Metadata.title, "utf-8"))
        if music21Metadata.composer is not None:
            allBrailleLines.append(unicode(music21Metadata.composer, "utf-8"))
    for p in music21Score.getElementsByClass(stream.Part):
        braillePart = partToBraille(p, **keywords)
        allBrailleLines.append(braillePart)            
    return u"\n".join(allBrailleLines)

def metadataToString(music21Metadata):
    allBrailleLines = []
    if music21Metadata.title is not None:
        allBrailleLines.append(unicode("Title: " + music21Metadata.title, "utf-8"))
    if music21Metadata.composer is not None:
        allBrailleLines.append(unicode("Composer: " + music21Metadata.composer, "utf-8"))
        
    return u"\n".join(allBrailleLines)

def opusToBraille(music21Opus, **keywords):
    """
    Translates an :class:`~music21.stream.Opus` to braille.
    """
    allBrailleLines = []
    for score in music21Opus.getElementsByClass(stream.Score):
        allBrailleLines.append(scoreToBraille(score, **keywords))
    return u"\n\n".join(allBrailleLines)
    
def measureToBraille(music21Measure, **keywords):
    """
    Translates a :class:`~music21.stream.Measure` to braille.
    """
    (inPlace, debug) = _translateArgs(**keywords)
    if not 'showHeading' in keywords:
        keywords['showHeading'] = False
    if not 'showFirstMeasureNumber' in keywords:
        keywords['showFirstMeasureNumber'] = False
    measureToTranscribe = music21Measure
    if not inPlace:
        measureToTranscribe = music21Measure.makeNotation(cautionaryNotImmediateRepeat=False)
    music21Part = stream.Part()
    music21Part.append(measureToTranscribe)
    keywords['inPlace'] = True
    return partToBraille(music21Part, **keywords)

def partToBraille(music21Part, **keywords):
    """
    Translates a :class:`~music21.stream.Part` to braille.
    """
    (inPlace, debug) = _translateArgs(**keywords)
    partToTranscribe = music21Part
    if not inPlace:
        partToTranscribe = music21Part.makeNotation(cautionaryNotImmediateRepeat=False)
    allSegments = segment.findSegments(partToTranscribe, **keywords)
    allBrailleText = []
    for brailleSegment in allSegments:
        transcription = brailleSegment.transcribe()
        if not debug:
            allBrailleText.append(transcription)
        else:
            allBrailleText.append(str(brailleSegment))
    return u"\n".join([unicode(bt) for bt in allBrailleText])
    
def keyboardPartsToBraille(music21PartStaffUpper, music21PartStaffLower, **keywords):
    """
    Translates two :class:`~music21.stream.Part` instances to braille, an upper part and a lower
    part. Assumes that the two parts are aligned and well constructed. Bar over bar format is used.
    """
    (inPlace, debug) = _translateArgs(**keywords)
    upperPartToTranscribe = music21PartStaffUpper
    if not inPlace:
        upperPartToTranscribe = music21PartStaffUpper.makeNotation(cautionaryNotImmediateRepeat=False)
    lowerPartToTranscribe = music21PartStaffLower
    if not inPlace:
        lowerPartToTranscribe = music21PartStaffLower.makeNotation(cautionaryNotImmediateRepeat=False)
    rhSegments = segment.findSegments(upperPartToTranscribe, **keywords)
    lhSegments = segment.findSegments(lowerPartToTranscribe, **keywords)
    allBrailleText = []
    for (rhSegment, lhSegment) in itertools.izip(rhSegments, lhSegments):
        bg = segment.BrailleGrandSegment(rhSegment, lhSegment)
        if not debug:
            allBrailleText.append(bg.transcription)
        else:
            allBrailleText.append(str(bg))
    return u"\n".join([unicode(bt) for bt in allBrailleText])

def _translateArgs(**keywords):
    inPlace=False
    debug=False
    if 'inPlace' in keywords:
        inPlace = keywords['inPlace']
    if 'debug' in keywords:
        debug = keywords['debug']
    return (inPlace, debug)

_DOC_ORDER = [objectToBraille]

#-------------------------------------------------------------------------------

class BrailleTranslateException(music21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof