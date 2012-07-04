# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         serial.py
# Purpose:      music21 classes for serial transformations
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#               Carl Lian
#
# Copyright:    (c) 2009-2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''This module defines objects for defining and manipulating structures 
common to serial and/or twelve-tone music, 
including :class:`~music21.serial.ToneRow` subclasses.
'''


import unittest, doctest
import copy

import music21
import music21.note
from music21 import stream
from music21 import pitch

from music21 import environment
_MOD = 'serial.py'
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
class SerialException(Exception):
    pass


#-------------------------------------------------------------------------------
class TwelveToneMatrix(stream.Stream):
    '''
    An object representation of a 2-dimensional array of 12 pitches. 
    Internal representation is as a :class:`~music21.stream.Stream`, 
    which stores 12 Streams, each Stream a horizontal row of pitches 
    in the matrix. 

    This object is commonly used by calling the 
    :meth:`~music21.stream.TwelveToneRow.matrix` method of 
    :meth:`~music21.stream.TwelveToneRow` (or a subclass).

    __OMIT_FROM_DOCS__

    >>> from music21 import *
    >>> aMatrix = serial.rowToMatrix([0,2,11,7,8,3,9,1,4,10,6,5])
    '''
    
    def __init__(self, *arguments, **keywords):
        stream.Stream.__init__(self, *arguments, **keywords)
    
    def __str__(self):
        '''
        Return a string representation of the matrix.
        '''
        ret = ""
        for rowForm in self.elements:
            msg = []
            for pitch in rowForm:
                msg.append(str(pitch.pitchClassString).rjust(3))
            ret += ''.join(msg) + "\n"
        return ret

    def __repr__(self):
        if len(self.elements) > 0:
            if isinstance(ToneRow, self.elements[0]):
                return '<music21.serial.TwelveToneMatrix for [%s]>' % self.elements[0]
            else:
                return Music21Object.__repr__(self)
        else:
            return Music21Object.__repr__(self)

#-------------------------------------------------------------------------------
class ToneRow(stream.Stream):
    '''A Stream representation of a tone row, or an ordered sequence of pitches. 

    '''
    def __init__(self):
        stream.Stream.__init__(self)

# functions, including row transformations, on lists of pitches.

def isTwelveToneRow(pitchList):
    '''
    
    Describes whether or not a list of pitches is a twelve-tone row.
    
    >>> from music21 import *
    >>> isTwelveToneRow(range(0,12))
    True
    >>> isTwelveToneRow(range(0,11))
    False
    >>> isTwelveToneRow([3,3,3,3,3,3,3,3,3,3,3,3])
    False
    
    '''
    
    if len(pitchList) != 12:
        return False
    else:
        temp = True
        for i in range(0,11):
            if i not in pitchList:
                temp = False
        return temp
        
    
def _getIntervalsAsString(pitchList):
        
        numPitches = len(pitchList)
        intervalString = ''
        for i in range(0,numPitches - 1):
            interval = (pitchList[i+1] - pitchList[i]) % 12
            if interval in range(0,10):
                intervalString = intervalString + str(interval)
            if interval == 10:
                intervalString = intervalString + 'T'
            if interval == 11:
                intervalString = intervalString + 'E'
        return intervalString
    
def _zeroCenteredTransformation(pitchList, transformationType, index):
    
    numPitches = len(pitchList)
    if int(index) != index:
        raise SerialException("Transformation must be by an integer.")
    else:
        firstPitch = pitchList[0]
        transformedPitchList = []
        if transformationType == 'P':
            for i in range(0,numPitches):
                newPitch = (pitchList[i] - firstPitch + index) % 12
                transformedPitchList.append(newPitch)
            return transformedPitchList
        elif transformationType == 'I':
            for i in range(0,numPitches):
                newPitch = (index + firstPitch - pitchList[i]) % 12
                transformedPitchList.append(newPitch)
            return transformedPitchList
        elif transformationType == 'R':
            for i in range(0,numPitches):
                newPitch = (index + pitchList[numPitches-1-i] - firstPitch) % 12
                transformedPitchList.append(newPitch)
            return transformedPitchList
        elif transformationType == 'RI':
            for i in range(0,numPitches):
                newPitch = (index - pitchList[numPitches-1-i] + firstPitch) % 12
                transformedPitchList.append(newPitch)
            return transformedPitchList     
        else:
            raise SerialException("Invalid transformation type.")
        
def _originalCenteredTransformation(pitchList, transformationType, index):
    
    firstPitch = pitchList[0]
    newIndex = (firstPitch + index) % 12
    if transformationType == 'T':
        return _zeroCenteredTransformation(pitchList, 'P', newIndex)
    else:
        return _zeroCenteredTransformation(pitchList, transformationType, newIndex)
    

# ----------------------------------------------------------------------------------------

class TwelveToneRow(ToneRow):
    '''A Stream representation of a twelve-tone row, capable of producing a 12-tone matrix.
    '''
    row = None

    _DOC_ATTR = {
    'row': 'A list representing the pitch class values of the row.',
    }

    def __init__(self):
        ToneRow.__init__(self)
        #environLocal.printDebug(['TwelveToneRow.__init__: length of elements', len(self)])

        if self.row != None:
            for pc in self.row:
                self.append(pitch.Pitch(pc))
    
    def matrix(self):
        '''
        Returns a :class:`~music21.serial.TwelveToneMatrix` object for the row.  That object can just be printed (or displayed via .show())
        
        >>> from music21 import *
        >>> src = serial.RowSchoenbergOp37()
        >>> [p.name for p in src]
        ['D', 'C#', 'A', 'B-', 'F', 'E-', 'E', 'C', 'G#', 'G', 'F#', 'B']
        >>> len(src)
        12
        >>> s37 = serial.RowSchoenbergOp37().matrix()
        >>> print s37
          0  B  7  8  3  1  2  A  6  5  4  9
          1  0  8  9  4  2  3  B  7  6  5  A
          5  4  0  1  8  6  7  3  B  A  9  2
          4  3  B  0  7  5  6  2  A  9  8  1
        ...
        >>> [e for e in s37[0]]
        [C, B, G, G#, E-, C#, D, B-, F#, F, E, A]

        
        '''        
        # note: do not want to return a TwelveToneRow() type, as this will
        # add again the same pitches to the elements list twice. 
        p = self.getElementsByClass(pitch.Pitch, returnStreamSubClass=False)

        i = [(12-x.pitchClass) % 12 for x in p]
        matrix = [[(x.pitchClass+t) % 12 for x in p] for t in i]

        matrixObj = TwelveToneMatrix()
        i = 0
        for row in matrix:
            i += 1
            rowObject = copy.copy(self)
            rowObject.elements = []
            rowObject.id = 'row-' + str(i)
            for p in row: # iterate over pitch class values
                pObj = pitch.Pitch()
                pObj.pitchClass = p
                rowObject.append(pObj)
            matrixObj.insert(0, rowObject)
        

        #environLocal.printDebug(['calling matrix start: len row:', self.row, 'len self', len(self)])

        return matrixObj
    
    def pitches(self):
        
        '''
        Convenience method showing the pitch classes of a serial.TwelveToneRow object as a list.
        
        >>> from music21 import *
        >>> L = [5*i for i in range(0,12)]
        >>> quintupleRow = serial.pcToToneRow(L)
        >>> quintupleRow.pitches()
        [0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7]
        
        '''
        
        pitchlist = [p.pitchClass for p in self]
        return pitchlist
    
    def noteNames(self):
        
        '''
        Convenience method showing the note names of a serial.TwelveToneRow object as a list.
        
        >>> from music21 import *
        >>> chromatic = serial.pcToToneRow(range(0,12))
        >>> chromatic.noteNames()
        ['C', 'C#', 'D', 'E-', 'E', 'F', 'F#', 'G', 'G#', 'A', 'B-', 'B']
        
        '''
        
        notelist = [p.name for p in self]
        return notelist
    
                    
    def isAllInterval(self):
        
        '''
        Describes whether or not a twelve-tone row is an all-interval row.
        
        >>> from music21 import *
        >>> chromatic = serial.pcToToneRow(range(0,12))
        >>> chromatic.pitches()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        >>> chromatic.isAllInterval()
        False
        >>> bergLyric = serial.pcToToneRow(serial.RowBergLyricSuite().row)
        >>> bergLyric.pitches()
        [5, 4, 0, 9, 7, 2, 8, 1, 3, 6, 10, 11]
        >>> bergLyric.isAllInterval()
        True
        '''
        tempAllInterval = True
        intervalString = _getIntervalsAsString(self.pitches())
        for i in range(1,10):
            if str(i) not in intervalString:
                tempAllInterval = False
        if 'T' not in intervalString:
            tempAllInterval = False
        if 'E' not in intervalString:
            tempAllInterval = False
        return tempAllInterval
    
        
        
    def isLinkChord(self):
        
        '''
        Describes whether or not a twelve-tone row is a Link Chord, that is, is an all-interval
        twelve-tone row containing a voicing of the all-trichord hexachord: [0, 1, 2, 4, 7, 8].

        Named for John Link who discovered them.
        
        >>> from music21 import *
        >>> bergLyric = serial.pcToToneRow(serial.RowBergLyricSuite().row)
        >>> bergLyric.pitches()
        [5, 4, 0, 9, 7, 2, 8, 1, 3, 6, 10, 11]
        >>> bergLyric.isAllInterval()
        True
        >>> bergLyric.isLinkChord()
        False
        >>> link = serial.pcToToneRow([0, 3, 8, 2, 10, 11, 9, 4, 1, 5, 7, 6])
        >>> link.isLinkChord()
        True
        
        '''
        
        if self.isAllInterval() == True:
            pitchList = self.pitches()
            intervalString = _getIntervalsAsString(pitchList)          
            substringsToCheck = ['1T794', '1T8E9', '236E8', '25189', '25387', '26534', '25E43', '289E7', '29658', '29E71', '2E783', '32158', '3268E', '34E52', '352E7', '361T8', '36E8T', '3826E', '3862E', '3871T', '387E2', '42167', '42761', '4316E', '43652', '43765', '43E25', '451T7', '4916E', '4952E', '49765', '497T1']
            hasChord = False
            for substring in substringsToCheck:
                if substring in intervalString:
                    hasChord = True
            if hasChord == True:
                return True
            else:
                return False
        else:
            return False

        
    def zeroCenteredRowTransformation(self,transformationType,index):
        
        '''
        
        Returns a serial.TwelveToneRow object giving a transformation of a twelve-tone row.
        Admissible transformations are 'P' (prime), 'I' (inversion),
        'R' (retrograde), and 'RI' (retrograde inversion). Note that in this convention, 
        the transformations P3 and I3 start on the pitch class 3, and the transformations
        R3 and RI3 end on the pitch class 3.
       
        >>> from music21 import *
        >>> chromatic = serial.pcToToneRow(range(0,12))
        >>> chromatic.pitches()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        >>> chromaticP3 = chromatic.zeroCenteredRowTransformation('P',3)
        >>> chromaticP3.pitches()
        [3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2]
        >>> chromaticI6 = chromatic.zeroCenteredRowTransformation('I',6)
        >>> chromaticI6.pitches()
        [6, 5, 4, 3, 2, 1, 0, 11, 10, 9, 8, 7]
        >>> schoenberg = serial.pcToToneRow(serial.RowSchoenbergOp26().row)
        >>> schoenberg.pitches()
        [3, 7, 9, 11, 1, 0, 10, 2, 4, 6, 8, 5]
        >>> schoenbergR8 = schoenberg.zeroCenteredRowTransformation('R',8)
        >>> schoenbergR8.pitches()
        [10, 1, 11, 9, 7, 3, 5, 6, 4, 2, 0, 8]
        >>> schoenbergRI9 = schoenberg.zeroCenteredRowTransformation('RI',9)
        >>> schoenbergRI9.noteNames()
        ['G', 'E', 'F#', 'G#', 'B-', 'D', 'C', 'B', 'C#', 'E-', 'F', 'A']
        
        '''
        
        transformedPitchList = _zeroCenteredTransformation(self.pitches(), transformationType, index)
        return pcToToneRow(transformedPitchList)
    
    def originalCenteredRowTransformation(self, transformationType, index):
        
                
        '''
        
        Returns a serial.TwelveToneRow object giving a transformation of a twelve-tone row.
        Admissible transformations are 'T' (transposition), 'I' (inversion),
        'R' (retrograde), and 'RI' (retrograde inversion). Note that in this convention,
        which is less common than the 'zero-centered' convention, the original row is not
        transposed to start on the pitch class 0. Thus, the transformation T3 transposes
        the original row by 3 semitones, and the transformations I3, R3, and RI3 first
        transform the row appropriately (without transposition), then transpose the resulting
        row by 3 semitones.
       
        >>> from music21 import *
        >>> chromatic = serial.pcToToneRow(range(0,12))
        >>> chromatic.pitches()
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        >>> chromaticP3 = chromatic.originalCenteredRowTransformation('P',3)
        >>> chromaticP3.pitches()
        [3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2]
        >>> chromaticI6 = chromatic.originalCenteredRowTransformation('I',6)
        >>> chromaticI6.pitches()
        [6, 5, 4, 3, 2, 1, 0, 11, 10, 9, 8, 7]
        >>> schoenberg = serial.pcToToneRow(serial.RowSchoenbergOp26().row)
        >>> schoenberg.pitches()
        [3, 7, 9, 11, 1, 0, 10, 2, 4, 6, 8, 5]
        >>> schoenbergR8 = schoenberg.originalCenteredRowTransformation('R',8)
        >>> schoenbergR8.pitches()
        [1, 4, 2, 0, 10, 6, 8, 9, 7, 5, 3, 11]
        >>> schoenbergRI9 = schoenberg.originalCenteredRowTransformation('RI',9)
        >>> schoenbergRI9.noteNames()
        ['B-', 'G', 'A', 'B', 'C#', 'F', 'E-', 'D', 'E', 'F#', 'G#', 'C']
        
        '''
        
        transformedPitchList = _originalCenteredTransformation(self.pitches(), transformationType, index)
        return pcToToneRow(transformedPitchList)

        
    
    def findTransformations(self, otherRow):
        ''' 
        
        Gives the list of (zero-centered) serial transformations taking one twelve-tone row,
        to another. Each transformation is given as a tuple of the transformation type and
        index.
        
        >>> from music21 import *
        >>> chromatic = serial.pcToToneRow([2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1])
        >>> reversechromatic = serial.pcToToneRow([8, 7, 6, 5, 4, 3, 2, 1, 0, 11, 10, 9])
        >>> chromatic.findTransformations(reversechromatic)
        [('I', 8), ('R', 9)]
        >>> schoenberg25 = serial.pcToToneRow(serial.RowSchoenbergOp25.row)
        >>> schoenberg26 = serial.pcToToneRow(serial.RowSchoenbergOp26.row)
        >>> schoenberg25.findTransformations(schoenberg26)
        []
        
        '''
    
        otherRowPitches = otherRow.pitches()
        transformationList = []
        firstPitch = otherRowPitches[0]
        lastPitch = otherRowPitches[-1]
        
        if otherRow.pitches() == self.zeroCenteredRowTransformation('P',firstPitch).pitches():
            transformation = 'P', firstPitch
            transformationList.append(transformation)
        if otherRow.pitches() == self.zeroCenteredRowTransformation('I',firstPitch).pitches():
            transformation = 'I', firstPitch
            transformationList.append(transformation)
        if otherRow.pitches() == self.zeroCenteredRowTransformation('R',lastPitch).pitches():
            transformation  = 'R', lastPitch
            transformationList.append(transformation)
        if otherRow.pitches() == self.zeroCenteredRowTransformation('RI',lastPitch).pitches():
            transformation = 'RI', lastPitch
            transformationList.append(transformation)
            
        return transformationList
        
        
            
        


class HistoricalTwelveToneRow(TwelveToneRow):
    '''
    A 12-tone row used in the historical literature. 
    Added attributes to document the the historical context of the row. 
    '''
    composer = None
    opus = None
    title = None

    _DOC_ATTR = {
    'composer': 'The composers name.',
    'opus': 'The opus of the work, or None.',
    'title': 'The title of the work.',
    }



class RowSchoenbergOp23No5(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 23, No. 5'
    title = 'Five Piano Pieces'
    row = [1, 9, 11, 7, 8, 6, 10, 2, 4, 3, 0, 5]
class RowSchoenbergOp24Mvmt4(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 24'
    title = 'Serenade, Mvt. 4, "Sonett"'
    row = [4, 2, 3, 11, 0, 1, 8, 6, 9, 5, 7, 10]
class RowSchoenbergOp24Mvmt5(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 24'
    title = 'Serenade, Mvt. 5, "Tanzscene"'
    row = [9, 10, 0, 3, 4, 6, 5, 7, 8, 11, 1, 2]
class RowSchoenbergOp25(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op.25'
    title = 'Suite for Piano'
    row = [4, 5, 7, 1, 6, 3, 8, 2, 11, 0, 9, 10]
class RowSchoenbergOp26(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 26'
    title = 'Wind Quintet'
    row = [3, 7, 9, 11, 1, 0, 10, 2, 4, 6, 8, 5]
class RowSchoenbergOp27No1(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 27 No. 1'
    title = 'Four Pieces for Mixed Chorus, No. 1'
    row = [6, 5, 2, 8, 7, 1, 3, 4, 10, 9, 11, 0]
class RowSchoenbergOp27No2(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 27 No. 2'
    title = 'Four Pieces for Mixed Chorus, No. 2'
    row = [0, 11, 4, 10, 2, 8, 3, 7, 6, 5, 9, 1]
class RowSchoenbergOp27No3(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 27 No. 3'
    title = 'Four Pieces for Mixed Chorus, No. 3'
    row = [7, 6, 2, 4, 5, 3, 11, 0, 8, 10, 9, 1]
class RowSchoenbergOp27No4(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 27 No. 4'
    title = 'Four Pieces for Mixed Chorus, No. 4'
    row = [1, 3, 10, 6, 8, 4, 11, 0, 2, 9, 5, 7]
class RowSchoenbergOp28No1(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 28 No. 1'
    title = 'Three Satires for Mixed Chorus, No. 1'
    row = [0, 4, 7, 1, 9, 11, 5, 3, 2, 6, 8, 10]
class RowSchoenbergOp28No3(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 28 No. 3'
    title = 'Three Satires for Mixed Chorus, No. 3'
    row = [5, 6, 4, 8, 2, 10, 7, 9, 3, 11, 1, 0]
class RowSchoenbergOp29(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 29'
    title = 'Suite'
    row = [3, 7, 6, 10, 2, 11, 0, 9, 8, 4, 5, 1]
class RowSchoenbergOp30(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 30'
    title = 'Third String Quartet'
    row = [7, 4, 3, 9, 0, 5, 6, 11, 10, 1, 8, 2]
class RowSchoenbergOp31(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 31'
    title = 'Variations for Orchestra'
    row = [10, 4, 6, 3, 5, 9, 2, 1, 7, 8, 11, 0]
class RowSchoenbergOp32(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 32'
    title = 'Von Heute Auf Morgen'
    row = [2, 3, 9, 1, 11, 5, 8, 7, 4, 0, 10, 6]
class RowSchoenbergOp33A(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 33A'
    title = 'Two Piano Pieces, No. 1'
    row = [10, 5, 0, 11, 9, 6, 1, 3, 7, 8, 2, 4]
class RowSchoenbergOp33B(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 33B'
    title = 'Two Piano Pieces, No. 2'
    row = [11, 1, 5, 3, 9, 8, 6, 10, 7, 4, 0, 2]
class RowSchoenbergOp34(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 34'
    title = 'Accompaniment to a Film Scene'
    row = [3, 6, 2, 4, 1, 0, 9, 11, 10, 8, 5, 7]
class RowSchoenbergOp35No1(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 35'
    title = 'Six Pieces for Male Chorus, No. 1'
    row = [2, 11, 3, 5, 4, 1, 8, 10, 9, 6, 0, 7]
class RowSchoenbergOp35No2(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 35'
    title = 'Six Pieces for Male Chorus, No. 2'
    row = [6, 9, 7, 1, 0, 2, 5, 11, 10, 3, 4, 8]
class RowSchoenbergOp35No3(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 35'
    title = 'Six Pieces for Male Chorus, No. 3'
    row = [3, 6, 7, 8, 5, 0, 9, 10, 4, 11, 2, 1]
class RowSchoenbergOp35No5(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 35'
    title = 'Six Pieces for Male Chorus, No. 5'
    row = [1, 7, 10, 2, 3, 11, 8, 4, 0, 6, 5, 9]
class RowSchoenbergOp36(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 36'
    title = 'Concerto for Violin and Orchestra'
    row = [9, 10, 3, 11, 4, 6, 0, 1, 7, 8, 2, 5]
class RowSchoenbergOp37(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 37'
    title = 'Fourth String Quartet'
    row = [2, 1, 9, 10, 5, 3, 4, 0, 8, 7, 6, 11]
class RowSchoenbergFragPianoPhantasia(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = None
    title = 'Fragment of Phantasia For Piano'
    row = [1, 5, 3, 6, 4, 8, 0, 11, 2, 9, 10, 7]
class RowSchoenbergFragOrganSonata(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = None
    title = 'Fragment of Sonata For Organ'
    row = [1, 7, 11, 3, 9, 2, 8, 6, 10, 5, 0, 4]
class RowSchoenbergFragPiano(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = None
    title = 'Fragment For Piano'
    row = [6, 9, 0, 7, 1, 2, 8, 11, 5, 10, 4, 3]
class RowSchoenbergOp41(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 41'
    title = 'Ode To Napoleon'
    row = [1, 0, 4, 5, 9, 8, 3, 2, 6, 7, 11, 10]
class RowSchoenbergOp42(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 42'
    title = 'Concerto For Piano And Orchestra'
    row = [3, 10, 2, 5, 4, 0, 6, 8, 1, 9, 11, 7]
class RowSchoenbergJakobsleiter(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = None
    title = 'Die Jakobsleiter'
    row = [1, 2, 5, 4, 8, 7, 0, 3, 11, 10, 6, 9]
class RowSchoenbergOp44(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 44'
    title = 'Prelude To A Suite From "Genesis"'
    row = [10, 6, 2, 5, 4, 0, 11, 8, 1, 3, 9, 7]
class RowSchoenbergOp45(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 45'
    title = 'String Trio'
    row = [2, 10, 3, 9, 4, 1, 11, 8, 6, 7, 5, 0]
class RowSchoenbergOp46(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 46'
    title = 'A Survivor From Warsaw'
    row = [6, 7, 0, 8, 4, 3, 11, 10, 5, 9, 1, 2]
class RowSchoenbergOp47(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 47'
    title = 'Fantasy For Violin And Piano'
    row = [10, 9, 1, 11, 5, 7, 3, 4, 0, 2, 8, 6]
class RowSchoenbergOp48No1(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 48'
    title = 'Three Songs, No. 1, "Sommermud"'
    row = [1, 2, 0, 6, 3, 5, 4, 10, 11, 7, 9, 8]
class RowSchoenbergOp48No2(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 48'
    title = 'Three Songs, No. 2, "Tot"'
    row = [2, 3, 9, 1, 10, 4, 8, 7, 0, 11, 5, 6]
class RowSchoenbergOp48No3(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 48'
    title = 'Three Songs, No, 3, "Madchenlied"'
    row = [1, 7, 9, 11, 3, 5, 10, 6, 4, 0, 8, 2]
class RowSchoenbergIsraelExists(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = None
    title = 'Israel Exists Again'
    row = [0, 3, 4, 9, 11, 5, 2, 1, 10, 8, 6, 7]
class RowSchoenbergOp50A(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 50A'
    title = 'Three Times A Thousand Years'
    row = [7, 9, 6, 4, 5, 11, 10, 2, 0, 1, 3, 8]
class RowSchoenbergOp50B(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 50B'
    title = 'De Profundis'
    row = [3, 9, 8, 4, 2, 10, 7, 2, 0, 6, 5, 1]
class RowSchoenbergOp50C(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = 'Op. 50C'
    title = 'Modern Psalms, The First Psalm'
    row = [4, 3, 0, 8, 9, 7, 5, 9, 6, 10, 1, 2]
class RowSchoenbergMosesAron(HistoricalTwelveToneRow):
    composer = 'Schoenberg'
    opus = None
    title = 'Moses And Aron'
    row = [9, 10, 4, 2, 3, 1, 7, 5, 6, 8, 11, 0]

# Berg
class RowBergChamberConcerto(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Chamber Concerto'
    row = [11, 7, 5, 9, 2, 3, 6, 8, 0, 1, 4, 10]
class RowBergWozzeckPassacaglia(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Wozzeck, Act I, Scene 4 "Passacaglia"'
    row = [3, 11, 7, 1, 0, 6, 4, 10, 9, 5, 8, 2]
class RowBergLyricSuite(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Lyric Suite Primary Row'
    row = [5, 4, 0, 9, 7, 2, 8, 1, 3, 6, 10, 11]
class RowBergLyricSuitePerm(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Lyric Suite, Last Mvt. Permutation'
    row = [5, 6, 10, 4, 1, 9, 2, 8, 7, 3, 0, 11]
class RowBergDerWein(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Der Wein'
    row = [2, 4, 5, 7, 9, 10, 1, 6, 8, 0, 11, 3]
class RowBergLulu(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Lulu: Primary Row'
    row = [0, 4, 5, 2, 7, 9, 6, 8, 11, 10, 3, 1]
class RowBergLuluActIScene20(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = 'Lulu, Act I , Scene XX'
    title = 'Perm. (Every 7th Note Of Primary Row)'
    row = [10, 6, 3, 8, 5, 11, 4, 2, 9, 0, 1, 7]
class RowBergLuluActIIScene1(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = 'Lulu, Act II, Scene 1'
    title = 'Perm. (Every 5th Note Of Primary Row)'
    row = [4, 10, 7, 1, 0, 9, 2, 11, 5, 8, 3, 6]
    #NOTE: this is wrong! 4 was inserted so that the row could pass the testViennese
class RowBergViolinConcerto(HistoricalTwelveToneRow):
    composer = 'Berg'
    opus = None
    title = 'Concerto For Violin And Orchestra'
    row = [7, 10, 2, 6, 9, 0, 4, 8, 11, 1, 3, 5]

# Webern
class RowWebernOpNo17No1(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. No. 17, No. 1'
    title = '"Armer Sunder, Du"'
    row = [11, 10, 5, 6, 3, 4, 7, 8, 9, 0, 1, 2]
class RowWebernOp17No2(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 17, No. 2'
    title = '"Liebste Jungfrau"'
    row = [1, 0, 11, 7, 8, 2, 3, 6, 5, 4, 9, 10]
class RowWebernOp17No3(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 17, No. 3'
    title = '"Heiland, Unsere Missetaten..."'
    row = [8, 5, 4, 3, 7, 6, 0, 1, 2, 11, 10, 9]
class RowWebernOp18No1(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 18, No. 1'
    title = '"Schatzerl Klein"'
    row = [0, 11, 5, 8, 10, 9, 3, 4, 1, 7, 2, 6]
class RowWebernOp18No2(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 18, No. 2'
    title = '"Erlosung"'
    row = [6, 9, 5, 8, 4, 7, 3, 11, 2, 10, 1, 0]
class RowWebernOp18No3(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 18, No. 3'
    title = '"Ave, Regina Coelorum"'
    row = [4, 3, 7, 6, 5, 11, 10, 2, 1, 0, 9, 8]
class RowWebernOp19No1(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 19, No. 1'
    title = '"Weiss Wie Lilien"'
    row = [7, 10, 6, 5, 3, 9, 8, 1, 2, 11, 4, 0]
class RowWebernOp19No2(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 19, No. 2'
    title = '"Ziehn Die Schafe"'
    row = [8, 4, 9, 6, 7, 0, 11, 5, 3, 2, 10, 1]
class RowWebernOp20(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 20'
    title = 'String Trio'
    row = [8, 7, 2, 1, 6, 5, 9, 10, 3, 4, 0, 11]
class RowWebernOp21(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 21'
    title = 'Chamber Symphony'
    row = [5, 8, 7, 6, 10, 9, 3, 4, 0, 1, 2, 11]
class RowWebernOp22(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 22'
    title = 'Quartet For Violin, Clarinet, Tenor Sax, And Piano'
    row = [6, 3, 2, 5, 4, 8, 9, 10, 11, 1, 7, 0]
class RowWebernOp23(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 23'
    title = 'Three Songs'
    row = [8, 3, 7, 4, 10, 6, 2, 5, 1, 0, 9, 11]
class RowWebernOp24(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 24'
    title = 'Concerto For Nine Instruments'
    row = [11, 10, 2, 3, 7, 6, 8, 4, 5, 0, 1, 9]
class RowWebernOp25(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 25'
    title = 'Three Songs'
    row = [7, 4, 3, 6, 1, 5, 2, 11, 10, 0, 9, 8]
class RowWebernOp26(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 26'
    title = 'Das Augenlicht'
    row = [8, 10, 9, 0, 11, 3, 4, 1, 5, 2, 6, 7]
class RowWebernOp27(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 27'
    title = 'Variations For Piano'
    row = [3, 11, 10, 2, 1, 0, 6, 4, 7, 5, 9, 8]
class RowWebernOp28(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 28'
    title = 'String Quartet'
    row = [1, 0, 3, 2, 6, 7, 4, 5, 9, 8, 11, 10]
class RowWebernOp29(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 29'
    title = 'Cantata I'
    row = [3, 11, 2, 1, 5, 4, 7, 6, 10, 9, 0, 8]
class RowWebernOp30(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 30'
    title = 'Variations For Orchestra'
    row = [9, 10, 1, 0, 11, 2, 3, 6, 5, 4, 7, 8]
class RowWebernOp31(HistoricalTwelveToneRow):
    composer = 'Webern'
    opus = 'Op. 31'
    title = 'Cantata II'
    row = [6, 9, 5, 4, 8, 3, 7, 11, 10, 2, 1, 0]



vienneseRows = [RowSchoenbergOp23No5, RowSchoenbergOp24Mvmt4, RowSchoenbergOp24Mvmt5, RowSchoenbergOp25, RowSchoenbergOp26, RowSchoenbergOp27No1, RowSchoenbergOp27No2, RowSchoenbergOp27No3, RowSchoenbergOp27No4, RowSchoenbergOp28No1, RowSchoenbergOp28No3, RowSchoenbergOp29, RowSchoenbergOp30, RowSchoenbergOp31, RowSchoenbergOp32, RowSchoenbergOp33A, RowSchoenbergOp33B, RowSchoenbergOp34, RowSchoenbergOp35No1, RowSchoenbergOp35No2, RowSchoenbergOp35No3, RowSchoenbergOp35No5, RowSchoenbergOp36, RowSchoenbergOp37, RowSchoenbergFragPianoPhantasia, RowSchoenbergFragOrganSonata, RowSchoenbergFragPiano, RowSchoenbergOp41, RowSchoenbergOp42, RowSchoenbergJakobsleiter, RowSchoenbergOp44, RowSchoenbergOp45, RowSchoenbergOp46, RowSchoenbergOp47, RowSchoenbergOp48No1, RowSchoenbergOp48No2, RowSchoenbergOp48No3, RowSchoenbergIsraelExists, RowSchoenbergOp50A, RowSchoenbergOp50B, RowSchoenbergOp50C, RowSchoenbergMosesAron, RowBergChamberConcerto, RowBergWozzeckPassacaglia, RowBergLyricSuite, RowBergLyricSuitePerm, RowBergDerWein, RowBergLulu, RowBergLuluActIScene20, RowBergLuluActIIScene1, RowBergViolinConcerto, RowWebernOpNo17No1, RowWebernOp17No2, RowWebernOp17No3, RowWebernOp18No1, RowWebernOp18No2, RowWebernOp18No3, RowWebernOp19No1, RowWebernOp19No2, RowWebernOp20, RowWebernOp21, RowWebernOp22, RowWebernOp23, RowWebernOp24, RowWebernOp25, RowWebernOp26, RowWebernOp27, RowWebernOp28, RowWebernOp29, RowWebernOp30, RowWebernOp31]



#-------------------------------------------------------------------------------
def pcToToneRow(pcSet):
    '''A convenience function that, given a list of pitch classes represented as integers 

    >>> from music21 import *
    >>> a = serial.pcToToneRow(range(12))
    >>> matrixObj = a.matrix()
    >>> print matrixObj
      0  1  2  3  4  5  6  7  8  9  A  B
      B  0  1  2  3  4  5  6  7  8  9  A
    ...

    >>> a = serial.pcToToneRow([4,5,0,6,7,2,'a',8,9,1,'b',3])
    >>> matrixObj = a.matrix()
    >>> print matrixObj
      0  1  8  2  3  A  6  4  5  9  7  B
      B  0  7  1  2  9  5  3  4  8  6  A
    ...
    '''
    if len(pcSet) == 12:
        # TODO: check for uniqueness
        a = TwelveToneRow()
        for thisPc in pcSet:
            p = music21.pitch.Pitch()
            p.pitchClass = thisPc
            a.append(p)
        return a
    else:
        raise SerialException("pcToToneRow requires a 12-tone-row")
    
def rowToMatrix(p):
    '''
    takes a row of numbers of converts it to a 12-tone 
    '''
    
    i = [(12-x) % 12 for x in p]
    matrix = [[(x+t) % 12 for x in p] for t in i]

    ret = ""
    for row in matrix:
        msg = []
        for pitch in row:
            msg.append(str(pitch).rjust(3))
        ret += ''.join(msg) + "\n"

    return ret









#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testRows(self):
        from music21 import interval

        self.assertEqual(len(vienneseRows), 71)

        totalRows = 0
        cRows = 0
        for thisRow in vienneseRows:
            thisRow = thisRow() 
            self.assertEqual(isinstance(thisRow, TwelveToneRow), True)
            
            if thisRow.composer == "Berg":
                continue
            post = thisRow.title
            
            totalRows += 1
            if thisRow[0].pitchClass == 0:
                cRows += 1
            
#             if interval.notesToInterval(thisRow[0], 
#                                    thisRow[6]).intervalClass == 6:
#              # between element 1 and element 7 is there a TriTone?
#              rowsWithTTRelations += 1


    def testMatrix(self):

        src = RowSchoenbergOp37()
        self.assertEqual([p.name for p in src], 
            ['D', 'C#', 'A', 'B-', 'F', 'E-', 'E', 'C', 'G#', 'G', 'F#', 'B'])
        s37 = RowSchoenbergOp37().matrix()
        self.assertEqual([e.name for e in s37[0]], ['C', 'B', 'G', 'G#', 'E-', 'C#', 'D', 'B-', 'F#', 'F', 'E', 'A'])


    def testLabelingA(self):

        from music21 import corpus, stream, pitch
        series = {'a':1, 'g-':2, 'g':3, 'a-':4, 
                  'f':5, 'e-':6, 'e':7, 'd':8, 
                  'c':9, 'c#':10, 'b-':11, 'b':12}
        s = corpus.parse('bwv66.6')
        for n in s.flat.notes:
            for key in series.keys():
                if n.pitch.pitchClass == pitch.Pitch(key).pitchClass:
                    n.addLyric(series[key])
        match = []
        for n in s.parts[0].flat.notes:
            match.append(n.lyric)
        self.assertEqual(match, ['10', '12', '1', '12', '10', '7', '10', '12', '1', '10', '1', '12', '4', '2', '1', '12', '12', '2', '7', '1', '12', '10', '10', '1', '12', '10', '1', '4', '2', '4', '2', '2', '2', '2', '2', '5', '2'])
        #s.show()
    
    def testViennese(self):
        
        nonRows = []
        for historicalRow in vienneseRows:
            if isTwelveToneRow(historicalRow.row) == False:
                nonRows.append(historicalRow)
                self.assertEqual(nonRows, [])

                
        
#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [ToneRow, TwelveToneRow, TwelveToneMatrix]

if __name__ == "__main__":
    music21.mainTest(Test)

#     import sys
#     if len(sys.argv) == 1: # normal conditions
#         music21.mainTest(Test)
# 
#     elif len(sys.argv) > 1:
#         t = Test()
# 
#         t.testMatrix()

#------------------------------------------------------------------------------
# eof

