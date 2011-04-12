#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         patel.py
# Purpose:      Tools for testing Aniruddh D. Patel's analysis theories
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import unittest, doctest
import music21
import math

_MOD = 'patel.py'


def nPVI(streamForAnalysis):
    '''
    Algorithm to give the normalized pairwise variability index 
    (Low, Grabe, & Nolan, 2000) of the rhythm of a stream.


    Used by Aniruddh D. Patel to argue for national differences between musical
    themes.  First encountered it in a presentation by Patel, Chew, Francois,
    and Child at MIT.

    
    n.b. -- takes the distance between each element, including clefs, keys, etc.
    use .notesAndRests etc. to filter out elements that are not useful.

    
    n.b. # 2 -- duration is used rather than actual distance -- for gapless
    streams (the norm) these two measures will be identical.


    >>> from music21 import *
    >>> s2 = converter.parse('C4 D E F G', '4/4').notesAndRests
    >>> nPVI(s2)
    0.0
    >>> s3 = converter.parse('C4 D8 C4 D8 C4', '4/4').notesAndRests
    >>> nPVI(s3)
    66.6666...
    >>> s4 = corpus.parse('bwv66.6').parts[0].flat.notesAndRests
    >>> nPVI(s4)
    12.96296...
    '''
    s = streamForAnalysis # shorter
    totalElements = len(s)
    summation = 0
    prevQL = s[0].quarterLength
    for i in range(1, totalElements):
        thisQL = s[i].quarterLength
        if thisQL > 0 and prevQL > 0:
            summation += abs(thisQL - prevQL)/((thisQL + prevQL)/2.0)
        else:
            pass
        prevQL = thisQL
    
    final = summation * 100.0/(totalElements - 1)
    return final

def melodicIntervalVariability(streamForAnalysis, *skipArgs, **skipKeywords):
    '''
    gives the Melodic Interval Variability (MIV) for a Stream, 
    as defined by Aniruddh D. Patel in "Music, Language, and the Brain"
    p. 223, as 100 x the coefficient of variation (standard deviation/mean)
    of the interval size (measured in semitones) between consective elements.
  
    
    the 100x is designed to put it in the same range as nPVI
  
    
    this method takes the same arguments of skipArgs and skipKeywords as
    Stream.melodicIntervals() for determining how to find consecutive
    intervals.
    
    >>> from music21 import *
    >>> s2 = converter.parse('C4 D E F# G#', '4/4').notesAndRests
    >>> melodicIntervalVariability(s2)
    0.0
    >>> s3 = converter.parse('C4 D E F G C', '4/4').notesAndRests
    >>> melodicIntervalVariability(s3)
    85.266688...
    >>> s4 = corpus.parse('bwv66.6').parts[0].flat.notesAndRests
    >>> melodicIntervalVariability(s4)
    65.287...
    '''
    s = streamForAnalysis # shorter
    intervalStream = s.melodicIntervals(skipArgs, skipKeywords)
    totalElements = len(intervalStream)
    if totalElements < 2:
        raise PatelException('need at least three notes to have a std-deviation of intervals (and thus a MIV)')
    summation = 0
    semitoneList = [myInt.chromatic.undirected for myInt in intervalStream]
    mean = 0 
    std = 0
    for a in semitoneList:
        mean = mean + a
    mean = mean / float(totalElements)
    for a in semitoneList:
        std = std + (a - mean)**2
    std = math.sqrt(std / float(totalElements - 1))
    return 100*(std/mean)

class PatelException(music21.Music21Exception):
    pass

class Test(unittest.TestCase):
    def runTest(self):
        pass


if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
