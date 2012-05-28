import unittest, doctest

import music21
import copy
from music21 import corpus
from music21 import key
from music21 import metadata
from music21 import interval
from music21 import pitch
from music21 import chord
from music21 import stream
from music21 import harmony
from music21 import scale
from music21 import clef

from music21.demos.theoryAnalysis import theoryAnalyzer

import random


#---------------

def reduction(sc):
    reductionStream = sc.chordify()
    for c in reductionStream.flat.getElementsByClass('Chord'):
        c.closedPosition(forceOctave=4, inPlace=True)
        c.removeRedundantPitches(inPlace=True)
        c.annotateIntervals()
    return reductionStream

#---------------

def generateIntervals(numIntervals,kind = None, octaveSpacing = None):
    if kind in ['anyChords','majorChords','diatonicTriads','diatonicTriadInversions']:
        return generateChords(numIntervals,kind)
    
    sc = stream.Stream()
    for i in range(numIntervals):        
        loPs = pitch.convertNameToPs("C3")
        hiPs = pitch.convertNameToPs("C#5")        
        startPs = random.randrange(loPs,hiPs)
        startPitch = pitch.Pitch(ps=startPs)
        numHalfSteps = random.randrange(-19,20)
        intv = interval.ChromaticInterval(numHalfSteps)
        if kind == 'consonant':
            invType = random.choice(['m3','M3','P5','m6','M6','P8'])
            intv = interval.Interval(invType)
        elif kind == 'noAugDim':
            invType = random.choice(['m2','M2','m3','M3','P4','P5','m6','M6','m7','M7'])
            intv = interval.Interval(invType)
        elif kind == 'dissonant':
            invType = random.choice(['m2','M2','m3','M3','P4','P5','m6','M6','m7','M7'])
            intv = interval.Interval(invType)
        endPitch = intv.transposePitch(startPitch)
        
        if kind == 'diatonic':
            startPitchName = random.choice('abcdefg')
            endPitchName = random.choice('abcdefg')
            startPitch = pitch.Pitch(random.choice('abcdefg'))
            endPitch = pitch.Pitch(random.choice('abcdefg'))

        if octaveSpacing is not None:
            startPitch.octave = 4
            endPitch.octave = 4 - octaveSpacing
        
        c = chord.Chord([startPitch,endPitch])
        c.volume.velocity = 127
        c.quarterLength=2
        sc.append(c)
    c = chord.Chord(['C','G'])
    c.quarterLength=2
    sc.append(c)
    return sc

traidInversions = [[1,3,5],[1,3,6],[1,4,6]]

def generateChords(numChords,kind):
    sc = stream.Stream()
    scl = scale.MajorScale('C')
    #possibleChordTypes = [l[0] for l in harmony.CHORD_TYPES.values()]
    possibleChordTypes =['53','63','64']
    if kind == 'diatonicTriads':
        for i in range(numChords):
            startDegree = random.randrange(0,8)
            inversion = random.randrange(0,3)
            chordPitches = []
            testDegrees = [d+startDegree-1 for d in traidInversions[inversion] ]
            print testDegrees
            chordPitches = [scl.pitchFromDegree(d+startDegree-1) for d in traidInversions[inversion] ]
            print chordPitches
            chordType = possibleChordTypes[random.randrange(0,len(possibleChordTypes))]
            c = chord.Chord(chordPitches)
            c.quarterLength=2
            sc.append(c)
        c = chord.Chord(['C','E','G'])
        c.quarterLength=2
        sc.append(c)
        return sc
    else:
        for i in range(numChords):
            loPs = pitch.convertNameToPs("C4")
            hiPs = pitch.convertNameToPs("C#5")        
            startPs = random.randrange(loPs,hiPs)
            startPitch = pitch.Pitch(ps=startPs)
            startPitchName = startPitch.name
            chordType = possibleChordTypes[random.randrange(0,len(possibleChordTypes))]
            print startPitchName+','+chordType
            c = harmony.ChordSymbol(startPitchName+','+chordType)
            c.writeAsChord = True
            c.quarterLength=2
            c.volume.velocity = 127
            sc.append(c)
        c = chord.Chord(['C','E','G'])
        c.quarterLength=2
        sc.append(c)
        return sc
        
    return sc


def runPerceivedDissonanceAnalysis(scoreIn, offsetList, keyStr=None):
    '''
    Perceived Dissonances: Demo app for NEMCOG meeting, April 28 2012

    webapp for determining the accuracy of aural identification of dissonances
    the user listens to a piece of music and clicks when they think they hear a dissonance. this
    information is then passed to this method, which compares the score to the list of offsets corresponding
    to when the user clicked. Music21 then identifies the dissonant vertical slices, and outputs results as a
    dictionary including the score, colored by vertical slices of interest as below:
    
    Green: both music21 and the user identified as dissonant
    Blue: only the user identified as dissonant
    Red: only music21 identified as dissonant
    
    This example runs two analysis, the first is a comparison with the unmodified score and user's offsets, the second
    with the passing tones and neighbor tones of the score removed. Results are returned as nested dictionaries of the
    following form:
    {fullScore , nonharmonicTonesRemovedScore}
    each of which is a dictionary containing these keys:
    {'stream', 'numUserIdentified', 'numMusic21Identified', 'numBothIdentified', 'accuracy', 'romans', 'key'}

    >>> from music21 import *
    >>> piece = corpus.parse('bwv7.7').measures(0,3)
    >>> offsetList = [1.1916666666666667,2.3641666666666667,3.6041666666666665,4.5808333333333335,\
                      6.131666666666667,8.804166666666667,10.148333333333333,11.700833333333334]
    >>> analysisDict = runPerceivedDissonanceAnalysis(piece, offsetList)
    >>> a = analysisDict['fullScore']
    >>> a['numMusic21Identified']
    7
    >>> a['numBothIdentified']
    3
    >>> a['numUserIdentified']
    8
    >>> a['romans']
    ['v43', 'iio65', 'bVIIb73']
    >>> b = analysisDict['nonharmonicTonesRemovedScore']
    >>> b['numMusic21Identified']
    5
    >>> b['numBothIdentified']
    2
    >>> b['accuracy']
    40.0 
   
    '''
    withoutNonharmonictonesScore = copy.deepcopy(scoreIn)
    theoryAnalyzer.removePassingTones(withoutNonharmonictonesScore)
    theoryAnalyzer.removeNeighborTones(withoutNonharmonictonesScore)
    withoutNonharmonictonesScore.sliceByGreatestDivisor(addTies=True, inPlace=True)
    withoutNonharmonictonesScore.stripTies(inPlace=True, matchByPitch=True, retainContainers=False)
    dissonanceAnalysisDict = {'fullScore': determineDissonantIdentificationAccuracy(scoreIn, offsetList,keyStr), \
                              'nonharmonicTonesRemovedScore':determineDissonantIdentificationAccuracy(withoutNonharmonictonesScore, offsetList,keyStr)}
    return dissonanceAnalysisDict


def _withinRange(dataList, lowLim, upperLim):
    '''helper function: returns true if there exists a number in dataList 
    for which the inequality lowLim <= number < upperLim
    
    >>> _withinRange([1,5.5,8], 2,3)
    False
    >>> _withinRange([1,5.5,8], 4,6)
    True
    '''
    dataList.sort()
    for index, offset in enumerate(dataList):
        if lowLim <= offset and offset < upperLim:
            return True
    return False

def determineDissonantIdentificationAccuracy(scoreIn, offsetList, keyStr=None):
    '''
    runs comparison on score to identify dissonances, then compares to the user's offsetList of identified
    dissonances. The score is colored according to the results, and appropriate information is returned
    as a dictionary. See runPerceivedDissonanceAnalysis for full details and an example.
    '''

    score = scoreIn.sliceByGreatestDivisor(addTies=True)
    vsList = theoryAnalyzer.getVerticalSlices(score)
    user = len(offsetList)
    music21VS = 0
    both = 0
    romanFigureList = []
    if keyStr == None:
        pieceKey = scoreIn.analyze('key')
    else:
        pieceKey = key.Key(keyStr)
    for (vsNum, vs) in enumerate(vsList):
            currentVSOffset = vs.offset(leftAlign=False)
            if vsNum + 1 == len(vsList):
                nextVSOffset = scoreIn.highestTime
            else:
                nextVSOffset = vsList[vsNum+1].offset(leftAlign=False)
            if not vs.isConsonant(): #music21 recognizes this as a dissonant vertical slice
                music21VS+=1
                if _withinRange(offsetList, currentVSOffset, nextVSOffset):
                    vs.color = '#00cc33' #the user also recognizes this as a dissonant vertical slice GREEn
                    both+=1
                    c = vs.getChord()
                    romanFigureList.append(music21.roman.romanNumeralFromChord(c, pieceKey).figure)
                else:
                    vs.color = '#cc3300'  #the user did not recognize as a dissonant vertical slice RED
            else: #music21 did not recognize this as a dissonant vertical slice
                if _withinRange(offsetList, currentVSOffset, nextVSOffset):
                    vs.color = '#0033cc' #the user recognized it as a dissonant vertical slice BLUE
    
    score.insert(metadata.Metadata())
    score.metadata.composer = scoreIn.metadata.composer
    score.metadata.movementName = scoreIn.metadata.movementName
    #score.show()
    analysisData = {'stream': score, 'numUserIdentified': user, 'numMusic21Identified':music21VS, 'numBothIdentified':both, 'accuracy': both*100.0/music21VS , 'romans': romanFigureList, 'key': pieceKey}
    return analysisData

## Shortcuts - temporary procedures used for re-implementation of hackday demo. Will be moved 
## to new home or removed when commandList can accommodate more complex structures (arrays, for loops...)

def createMensuralCanon(sc):
    '''
    Implements music21 example of creating a mensural canon

    '''
    melody = sc.parts[0].flat.notesAndRests
    
    canonStream = stream.Score()
    for scalar, t in [(1, 'p1'), (2, 'p-5'), (.5, 'p-11'), (1.5, -24)]:
        part = melody.augmentOrDiminish(scalar, inPlace=False)
        part.transpose(t, inPlace=True)
        canonStream.insert(0, part)
    
    return canonStream

def correctChordSymbols(worksheet, studentResponse):
    
    '''
    Written for hackday demo: accepts as parameters a stream with chord symbols (the worksheet)
    and the student's attempt to write out the pitches for each chord symbol of the worksheet.
    The student's work is returned with annotations, and the percentage correct is also returned
    
    >>> from music21 import *
    >>> worksheet = stream.Stream()
    >>> worksheet.append(harmony.ChordSymbol('C'))
    >>> worksheet.append(harmony.ChordSymbol('G7'))
    >>> worksheet.append(harmony.ChordSymbol('B-'))
    >>> worksheet.append(harmony.ChordSymbol('D7/A')) 
    >>> studentResponse = stream.Stream()
    >>> studentResponse.append(clef.TrebleClef())

    >>> studentResponse.append(chord.Chord(['C','E','G']))
    >>> studentResponse.append(chord.Chord(['G', 'B', 'D5', 'F5']))
    >>> studentResponse.append(chord.Chord(['B-', 'C']))
    >>> studentResponse.append(chord.Chord(['D4', 'F#4', 'A4', 'C5']))
    >>> newScore, percentCorrect = correctChordSymbols( worksheet, studentResponse)
    >>> for x in newScore.notes:
    ...  x.lyric
    ':)'
    ':)'
    'PITCHES'
    'INVERSION'
    >>> percentCorrect
    50.0
    
    
    '''
    numCorrect = 0
    chords1 = worksheet.flat.getElementsByClass(music21.harmony.ChordSymbol)
    totalNumChords = len(chords1)
    chords2 = studentResponse.flat.getElementsByClass([music21.chord.Chord, music21.note.Note])
    isCorrect = False
    for chord1, chord2 in zip(chords1, chords2):
        if chord1 not in studentResponse:
            studentResponse.insertAndShift(chord2.offset, chord1)
        if not('Chord' in chord2.classes):
            chord2.lyric = "NOT A CHORD"
            continue
        newPitches = []
        for x in chord2.pitches:
            newPitches.append(str(x.name))
        for pitch in chord1:
           
            if pitch.name in newPitches:
                isCorrect = True
            else:
                isCorrect = False
                break
        if isCorrect == True:
            newPitches1 = []
            for y in chord1.pitches:
                newPitches1.append(str(y.name))
            p = chord1.sortDiatonicAscending()
            o =  chord2.sortDiatonicAscending()
           
            a = []
            b = []
            for d in p.pitches:
                a.append(str(d.name))
            for k in o.pitches:
                b.append(str(k.name))
            if a != b:
                chord2.lyric = "INVERSION"
            else:
                numCorrect = numCorrect + 1
                chord2.lyric = ":)"
        if isCorrect == False:
            chord2.lyric = "PITCHES"

    percentCorrect =  numCorrect*1.0/totalNumChords * 100
    return (studentResponse, percentCorrect) #student's corrected score

def checkLeadSheetPitches(worksheet, returnType=''):
    '''
    checker routine for hack day demo lead sheet chord symbols exercise. Accepts
    a stream with both the chord symbols and student's chords, and returns the corrected
    stream. if returnType=answerkey, the score is returned with the leadsheet pitches realized
    
    >>> from music21 import *
    >>> worksheet = stream.Stream()
    >>> worksheet.append(harmony.ChordSymbol('C'))
    >>> worksheet.append(harmony.ChordSymbol('G7'))
    >>> worksheet.append(harmony.ChordSymbol('B'))
    >>> worksheet.append(harmony.ChordSymbol('D7/A')) 

    >>> answerKey = checkLeadSheetPitches( worksheet, returnType = 'answerkey' )
    >>> for x in answerKey.notes:
    ...  x.pitches
    [C3, E3, G3]
    [G2, B2, D3, F3]
    [B2, D#3, F#3]
    [A2, C3, D3, F#3]
    '''
    #nicePiece = sc
    #incorrectPiece = sc
    
    #incorrectPiece = messageconverter.parse('C:\Users\sample.xml')
    
    #sopranoLine = nicePiece.getElementsByClass(stream.Part)[0]
    #chordLine = nicePiece.getElementsByClass(stream.Part)[1]
    #chordLine.show('text')
    #bassLine = nicePiece.part(2)
    studentsAnswers = worksheet.flat.getElementsByClass(music21.chord.Chord)
    answerKey = worksheet.flat.getElementsByClass(harmony.ChordSymbol)
    
    correctedAssignment, numCorrect = correctChordSymbols(answerKey, studentsAnswers)
    
    if returnType == 'answerkey':
        
        for chordSymbol in answerKey:
            chordSymbol.writeAsChord = True
        message = 'answer key displayed'
        return answerKey
    else: 
        message = 'you got '+str(numCorrect)+' percent correct'
        return correctedAssignment


def colorAllNotes(sc, color):
    '''
    Iterate through all notes and change their color to the given color - 
    used for testing color rendering in noteflight
    '''
    for n in sc.flat.getElementsByClass('Note'):
        n.color = color 
    return sc

def colorAllChords(sc, color):
    '''
    Iterate through all chords and change their color to the given color - 
    used for testing color rendering in noteflight
    '''
    for c in sc.flat.getElementsByClass('Chord'):
        c.color = color 
    return sc

def writeMIDIFileToServer(sc):
    '''
    Iterate through all notes and change their color to the given color - 
    used for testing color rendering in noteflight
    '''
    #documentRoot = environ['DOCUMENT_ROOT']
    documentRoot = '/Library/WebServer/Documents'
    urlPath = "/music21/OutputFiles/cognitionEx.mid"
    writePath = documentRoot + urlPath
    
    sc.write('mid',writePath)
    
    return urlPath

#------------------------------------------------------------------------
# Tests


class Test(unittest.TestCase):

    def runTest(self):
        pass


if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
