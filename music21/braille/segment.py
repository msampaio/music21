# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         segment.py
# Purpose:      music21 class which allows division of streams into braille segments.
# Authors:      Jose Cabal-Ugaz
#
# Copyright:    (c) 2012 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

import collections
import copy
import itertools
import music21
import unittest

from music21 import articulations
from music21 import bar
from music21 import chord
from music21 import clef
from music21 import dynamics
from music21 import environment
from music21 import expressions
from music21 import key
from music21 import layout
from music21 import meter
from music21 import note
from music21 import spanner
from music21 import stream
from music21 import tempo

from music21.braille import basic
from music21.braille import lookup
from music21.braille import text

symbols = lookup.symbols
environRules = environment.Environment('segment.py')

#-------------------------------------------------------------------------------
# Segment, Grouping classes + transcription methods

class BrailleElementGrouping(list):
    def __init__(self):
        list.__init__(self)
        # External attributes
        # -------------------
        self.keySignature = key.KeySignature(0)
        self.timeSignature = meter.TimeSignature('4/4')
        self.descendingChords = True
        self.showClefSigns = False
        self.upperFirstInNoteFingering = True

class BrailleSegment(collections.defaultdict):
    def __init__(self):
        # Internal attributes
        # -------------------
        self.default_factory = BrailleElementGrouping
        self.allGroupingKeys = None
        self.currentGroupingKey = None
        self.lastNote = None
        self.previousGroupingKey = None
        # External attributes
        # -------------------
        self.cancelOutgoingKeySig = True
        self.dummyRestLength = None
        self.isHyphenated = False
        self.maxLineLength = 40
        self.showFirstMeasureNumber = True
        self.showHand = None
        self.showHeading = True
        self.suppressOctaveMarks = False

    def __str__(self):
        name = "<music21.braille.segment BrailleSegment {0}>".format(id(self))
        hyphenation = "isHyphenated = {0}".format(self.isHyphenated)
        allGroupings = u"\n".join(["{0}: {1}".format(item[0],item[1]) for item in sorted(self.items())])
        return u"\n".join(["---begin segment---", name, hyphenation, allGroupings, "---end segment---"])
    
    def __repr__(self):
        return str(self)

    def transcribe(self):
        bt = text.BrailleText(self.maxLineLength, self.showHand)
        self.allGroupingKeys = sorted(self.keys())
        
        # Heading
        # -------
        self.extractHeading(bt)
        # Measure Number
        # --------------
        self.addMeasureNumber(bt)
        # Dummy Rests
        # -----------
        self.addDummyRests(bt)

        # Everything else
        # ---------------
        while (len(self.allGroupingKeys) > 0):
            self.previousGroupingKey = self.currentGroupingKey
            self.currentGroupingKey = self.allGroupingKeys.pop(0)
            # Note Grouping
            # -------------
            if self.currentGroupingKey % 10 == 9:
                self.extractNoteGrouping(bt)
            # In Accord Grouping
            # ------------------
            elif self.currentGroupingKey % 10 == 8:
                self.extractInaccordGrouping(bt)
            # Signature(s) Grouping
            # ---------------------
            elif self.currentGroupingKey % 10 == 3:
                self.extractSignatureGrouping(bt)
            # Long Expression(s) Grouping
            # ---------------------------
            elif self.currentGroupingKey % 10 == 7:
                self.extractLongExpressionGrouping(bt)
            # Tempo Text Grouping
            # -------------------
            elif self.currentGroupingKey % 10 == 4:
                self.extractTempoTextGrouping(bt)

        return bt

    def addDummyRests(self, brailleText):
        if self.dummyRestLength is not None:
            dummyRests = [self.dummyRestLength * lookup.rests['dummy']]
            brailleText.addElement(keyOrTimeSig = u"".join(dummyRests), withHyphen = False)
        return None

    def addMeasureNumber(self, brailleText):
        if self.showFirstMeasureNumber:
            brailleText.addElement(measureNumber = self.getMeasureNumber())
        return None

    def consolidate(self):
        newSegment = BrailleSegment()
        pngKey = None
        for (groupingKey, groupingList) in sorted(self.items()):
            if groupingKey % 10 != 9:
                newSegment[groupingKey] = groupingList
                pngKey = None
            else:
                if pngKey == None:
                    pngKey = groupingKey
                for item in groupingList:
                    newSegment[pngKey].append(item)
        return newSegment

    def extractHeading(self, brailleText):
        keySignature = None
        timeSignature = None
        tempoText = None
        metronomeMark = None
        
        while True:
            try:
                if self.allGroupingKeys[0] % 10 > 5:
                    break
            except TypeError as te:
                if te.args[0] == "'NoneType' object is not subscriptable":
                    self.allGroupingKeys = sorted(self.keys())
                    return self.extractHeading(brailleText)
            self.currentGroupingKey = self.allGroupingKeys.pop(0)
            if self.currentGroupingKey % 10 == 3:
                try:
                    keySignature, timeSignature = self.get(self.currentGroupingKey)[0], self.get(self.currentGroupingKey)[1]
                except IndexError:
                    keyOrTimeSig = self.get(self.currentGroupingKey)[0]
                    if isinstance(keyOrTimeSig, key.KeySignature):
                        keySignature = keyOrTimeSig
                    else:
                         timeSignature = keyOrTimeSig
            elif self.currentGroupingKey % 10 == 4:
                tempoText = self.get(self.currentGroupingKey)[0]
            elif self.currentGroupingKey % 10 == 5:
                metronomeMark = self.get(self.currentGroupingKey)[0]

        try:
            brailleHeading = basic.transcribeHeading(keySignature, timeSignature, tempoText, metronomeMark, self.maxLineLength)
            brailleText.addElement(heading = brailleHeading)
        except basic.BrailleBasicException as bbe:
            if not bbe.args[0] == "No heading can be made.":
                raise bbe
        return None
            
    def extractInaccordGrouping(self, brailleText):
        inaccords = self.get(self.currentGroupingKey)
        brailleInaccord = symbols['full_inaccord'].join([basic.transcribeVoice(vc) for vc in inaccords])
        brailleText.addElement(inaccord=self.brailleInaccord)
        return None

    def extractLongExpressionGrouping(self, brailleText):
        longExpr = basic.textExpressionToBraille(self.get(self.currentGroupingKey)[0])
        if not self.currentGroupingKey % 100 == 7:
            brailleText.addElement(longExpression = longExpr, withHyphen = True)
        else:
            brailleText.addElement(longExpression = longExpr, withHyphen = False)
        return None

    def extractNoteGrouping(self, brailleText):
        noteGrouping = self.get(self.currentGroupingKey)
        allNotes = [n for n in noteGrouping if isinstance(n, note.Note)]
        withHyphen = False
        if self.previousGroupingKey is not None:
            if (self.currentGroupingKey - self.previousGroupingKey) == 10:
                withHyphen = True
                self.lastNote = None
            if self.previousGroupingKey % 10 != 9:
                self.lastNote = None
        showLeadingOctave = True
        if len(allNotes) > 0:
            if not self.suppressOctaveMarks:
                if self.lastNote is not None:
                    firstNote = allNotes[0]
                    showLeadingOctave = basic.showOctaveWithNote(self.lastNote, firstNote)
            else:
                showLeadingOctave = False
            self.lastNote = allNotes[-1]
        else:
            if self.suppressOctaveMarks:
                showLeadingOctave = False
        try:
            brailleNoteGrouping = basic.transcribeNoteGrouping(noteGrouping, showLeadingOctave)
            brailleText.addElement(noteGrouping = brailleNoteGrouping,\
                          showLeadingOctave = showLeadingOctave, withHyphen = withHyphen)
        except text.BrailleTextException as bte:
            if bte.args[0] == "Recalculate Note Grouping With Leading Octave":
                showLeadingOctave = True
                if self.suppressOctaveMarks:
                    showLeadingOctave = False  
                brailleNoteGrouping = basic.transcribeNoteGrouping(noteGrouping, showLeadingOctave)
                brailleText.addElement(noteGrouping = brailleNoteGrouping,\
                               showLeadingOctave = True, withHyphen = withHyphen)
            elif bte.args[0] == "Split Note Grouping":
                isSolved = False
                bdo = 0
                while not isSolved:
                    (sngA, sngB) = splitNoteGrouping(noteGrouping, beatDivisionOffset = bdo)
                    brailleNoteGroupingA = basic.transcribeNoteGrouping(sngA, showLeadingOctave)
                    try:
                        brailleText.addElement(noteGrouping = brailleNoteGroupingA,\
                                       showLeadingOctave = showLeadingOctave, withHyphen = withHyphen)
                    except text.BrailleTextException:
                        bdo += 1
                        continue
                    showLeadingOctave = True
                    if self.suppressOctaveMarks:
                        showLeadingOctave = False  
                    brailleNoteGroupingB = basic.transcribeNoteGrouping(sngB, showLeadingOctave)
                    brailleText.addElement(noteGrouping = brailleNoteGroupingB,\
                                            showLeadingOctave = True, withHyphen = True, forceHyphen=True)
                    isSolved = True
        return None

    def extractSignatureGrouping(self, brailleText):
        keySignature = None
        timeSignature = None
        try:
            keySignature, timeSignature = self.get(self.currentGroupingKey)[0], self.get(self.currentGroupingKey)[1]
        except IndexError:
            keyOrTimeSig = self.get(self.currentGroupingKey)[0]
            if isinstance(keyOrTimeSig, key.KeySignature):
                keySignature = keyOrTimeSig
            else:
                timeSignature = keyOrTimeSig
        
        outgoingKeySig = None
        if self.cancelOutgoingKeySig and not keySignature is None:
            outgoingKeySig = keySignature.outgoingKeySig

        withHyphen = False
        if self.previousGroupingKey is not None and (self.currentGroupingKey - self.previousGroupingKey) == 4:
            withHyphen = True
        try:
            brailleSig = basic.transcribeSignatures(keySignature, timeSignature, outgoingKeySig)
            brailleText.addElement(keyOrTimeSig = brailleSig, withHyphen = withHyphen)
        except basic.BrailleBasicException as bbe:
            if not bbe.args[0] == "No key or time signature to transcribe!":
                raise bbe
        return None

    def extractTempoTextGrouping(self, brailleText):
        self.allGroupingKeys.insert(0, self.currentGroupingKey)
        if self.previousGroupingKey % 10 == 3:
            self.allGroupingKeys.insert(0, self.previousGroupingKey)
        self.extractHeading(brailleText)
        brailleText.addElement(measureNumber = self.getMeasureNumber())
        return None

    def getMeasureNumber(self):
        initMeasureNumber = self.allGroupingKeys[0] / 100
        return basic.numberToBraille(initMeasureNumber)

class BrailleGrandSegment():
    def __init__(self, rightSegment, leftSegment):
        self.allKeyPairs = self.combineGroupingKeys(rightSegment, leftSegment)
        self.rightSegment = rightSegment
        self.leftSegment = leftSegment
        self.previousGroupingPair = None
        self.currentGroupingPair = None
        self.maxLineLength = self.rightSegment.maxLineLength

    def __str__(self):
        name = "<music21.braille.segment BrailleGrandSegment {0}>".format(id(self))
        allPairs = []
        for (rightKey, leftKey) in self.allKeyPairs:
            a = "{0}: ".format(rightKey)
            b = "{0}".format(self.rightSegment[rightKey])
            c = "{0}: ".format(leftKey)
            d = "{0}".format(self.leftSegment[leftKey])
            ab = u"".join([a,b]) 
            cd = u"".join([c,d])
            allPairs.append(u"\n".join([ab, cd, "====\n"]))
        return u"\n".join(["---begin grand segment---", name, u"".join(allPairs), "---end grand segment---"])

    def combineGroupingKeys(self, rightSegment, leftSegment):
        groupingKeysRight = sorted(rightSegment.keys())
        groupingKeysLeft = sorted(leftSegment.keys())
        combinedGroupingKeys = []
        
        while(len(groupingKeysRight) > 0):
            gkRight = groupingKeysRight.pop(0)
            try:
                groupingKeysLeft.remove(gkRight)
                combinedGroupingKeys.append((gkRight, gkRight))
            except ValueError as ve:
                if gkRight % 10 < 8:
                    combinedGroupingKeys.append((gkRight, None))
                else:
                    if gkRight % 10 == 8:
                        gkLeft = gkRight+1
                    else:
                        gkLeft = gkRight-1
                    try:
                        groupingKeysLeft.remove(gkLeft)
                        combinedGroupingKeys.append((gkRight,gkLeft))
                    except ValueError as ve:
                        raise BrailleSegmentException("Misaligned braille groupings")
        
        while(len(groupingKeysLeft) > 0):
            gkLeft = groupingKeysLeft.pop(0)
            combinedGroupingKeys.append((None, gkLeft))
        
        return combinedGroupingKeys
    
    def transcribe(self):
        bk = text.BrailleKeyboard(self.maxLineLength)
        bk.highestMeasureNumberLength = len(str(self.allKeyPairs[-1][0] / 100))

        # Heading
        # -------
        self.extractHeading(bk)
    
        # Everything else
        # ---------------
        while (len(self.allKeyPairs) > 0):
            self.previousGroupingPair = self.currentGroupingPair
            self.currentGroupingPair = self.allKeyPairs.pop(0)
            (rightKey, leftKey) = self.currentGroupingPair

            # Note Grouping (s) /Inaccord(s)
            # ----------------------
            if rightKey >= 8 or leftKey >=8:
                self.extractNoteGrouping(bk)
            # Signature Grouping
            # ------------------
            elif rightKey == 3 or leftKey == 3:
                self.extractSignatureGrouping(bk)
            # Long Expression(s) Grouping
            # ---------------------------
            elif rightKey == 7 or leftKey == 7:
                self.extractLongExpressionGrouping(bk)
            # Tempo Text Grouping
            # -------------------
            elif rightKey == 4 or leftKey == 4:
                self.extractTempoTextGrouping(bk)
                
        return bk
    
    def extractHeading(self, brailleKeyboard):
        keySignature = None
        timeSignature = None
        tempoText = None
        metronomeMark = None
        
        while True:
            (rightKey, leftKey) = self.allKeyPairs[0]
            useKey = rightKey
            try:
                useElement = self.rightSegment[rightKey]
            except KeyError as ke:
                if ke.args[0] == "None":
                    useElement = self.leftSegment[leftKey]
                    useKey = leftKey
                else:
                    raise ke
            if useKey % 10 > 5:
                break
            self.allKeyPairs.pop(0)
            if useKey % 10 == 3:
                try:
                    keySignature, timeSignature = useElement[0], useElement[1]
                except IndexError:
                    if isinstance(useElement, key.KeySignature):
                        keySignature = useElement[0]
                    else:
                         timeSignature = useElement[0]
            elif useKey % 10 == 4:
                tempoText = useElement[0]
            elif useKey % 10 == 5:
                metronomeMark = useElement[0]

        try:
            brailleHeading = basic.transcribeHeading(keySignature, timeSignature, tempoText, metronomeMark, self.maxLineLength)
            brailleKeyboard.addElement(heading = brailleHeading)
        except basic.BrailleBasicException as bbe:
            if not bbe.args[0] == "No heading can be made.":
                raise bbe
        return None
    
    def extractNoteGrouping(self, brailleKeyboard):
        (rightKey, leftKey) = self.currentGroupingPair
        currentMeasureNumber = basic.numberToBraille(rightKey / 100, withNumberSign=False)
        if rightKey % 10 == 8:
            inaccords = self.rightSegment[rightKey]
            rh_braille = basic.symbols['full_inaccord'].join([transcribeVoice(vc) for vc in inaccords])
        else:
            rh_braille = basic.transcribeNoteGrouping(self.rightSegment[rightKey])
        if leftKey % 10 == 8:
            inaccords = self.leftSegment[leftKey]
            lh_braille = basic.symbols['full_inaccord'].join([transcribeVoice(vc) for vc in inaccords])
        else:
            lh_braille = basic.transcribeNoteGrouping(self.leftSegment[leftKey])
        brailleKeyboard.addNoteGroupings(currentMeasureNumber, rh_braille, lh_braille)
        return None
    
    def extractSignatureGrouping(self, brailleKeyboard):
        pass
    
    def extractLongExpressionGrouping(self, brailleKeyboard):
        pass
    
    def extractTempoTextGrouping(self, brailleKeyboard):
        pass
            
def splitNoteGrouping(noteGrouping, value = 2, beatDivisionOffset = 0):
    music21Measure = stream.Measure()
    for brailleElement in noteGrouping:
        music21Measure.insert(brailleElement.offset, brailleElement)
    newMeasures = splitMeasure(music21Measure, value, beatDivisionOffset, noteGrouping.timeSignature)
    
    leftBrailleElements = BrailleElementGrouping()
    for brailleElement in newMeasures[0]:
        leftBrailleElements.append(brailleElement)
    leftBrailleElements.__dict__ = noteGrouping.__dict__.copy()

    rightBrailleElements = BrailleElementGrouping()
    for brailleElement in newMeasures[1]:
        rightBrailleElements.append(brailleElement)
    rightBrailleElements.__dict__ = noteGrouping.__dict__.copy()

    return (leftBrailleElements, rightBrailleElements)

def transcribeVoice(music21Voice):
    music21Part = stream.Part()
    music21Measure = stream.Measure()
    for brailleElement in music21Voice:
        music21Measure.append(brailleElement)
    music21Part.append(music21Measure)
    music21Measure.number = music21Voice.measureNumber
    allSegments = findSegments(music21Part, showHeading=False, showFirstMeasureNumber=False)
    allTrans = []
    for brailleElementSegment in allSegments:
        segmentTranscription = brailleElementSegment.transcribe()
        allTrans.append(str(segmentTranscription))
    return u"\n".join(allTrans)
#-------------------------------------------------------------------------------
# Grouping + Segment creation from music21.stream Part

def findSegments(music21Part, **partKeywords):
    # Slurring
    # --------
    slurLongPhraseWithBrackets = True
    showShortSlursAndTiesTogether, showLongSlursAndTiesTogether = False, False

    if 'slurLongPhraseWithBrackets' in partKeywords:
        slurLongPhraseWithBrackets = partKeywords['slurLongPhraseWithBrackets']
    if 'showShortSlursAndTiesTogether' in partKeywords:
        showShortSlursAndTiesTogether = partKeywords['showShortSlursAndTiesTogether']
    if 'showLongSlursAndTiesTogether' in partKeywords:
        showLongSlursAndTiesTogether = partKeywords['showLongSlursAndTiesTogether']
    else:
        if slurLongPhraseWithBrackets:
            showLongSlursAndTiesTogether = True
            
    prepareSlurredNotes(music21Part, slurLongPhraseWithBrackets, showShortSlursAndTiesTogether, showLongSlursAndTiesTogether)

    # Raw Segments
    # ------------
    segmentBreaks = None
    if 'segmentBreaks' in partKeywords:
        segmentBreaks = partKeywords['segmentBreaks']
    allSegments = getRawSegments(music21Part, segmentBreaks)
    # Grouping Attributes
    # -------------------
    addGroupingAttributes(allSegments, music21Part, **partKeywords)
    # Segment Attributes
    # ------------------
    addSegmentAttributes(allSegments, music21Part, **partKeywords)
    # Articulations
    # -------------
    fixArticulations(allSegments)
    
    return allSegments

# Slurring
# --------
def prepareSlurredNotes(music21Part, slurLongPhraseWithBrackets = True,\
                         showShortSlursAndTiesTogether = True, showLongSlursAndTiesTogether = True):
    if not len(music21Part.spannerBundle) > 0:
        return None
    allNotes = music21Part.flat.notes
    for slur in music21Part.spannerBundle.getByClass(spanner.Slur):
        slur[0].index = allNotes.index(slur[0])
        slur[1].index = allNotes.index(slur[1])
        beginIndex = slur[0].index
        endIndex = slur[1].index
        delta = abs(endIndex - beginIndex) + 1
        if not showShortSlursAndTiesTogether and delta <= 4:
            if allNotes[beginIndex].tie != None and allNotes[beginIndex].tie.type == 'start':
                beginIndex += 1
            if allNotes[endIndex].tie != None and allNotes[endIndex].tie.type == 'stop':
                endIndex -= 1
        if not showLongSlursAndTiesTogether and delta > 4:
            if allNotes[beginIndex].tie != None and allNotes[beginIndex].tie.type == 'start':
                beginIndex += 1
            if allNotes[endIndex].tie != None and allNotes[endIndex].tie.type == 'stop':
                endIndex -= 1
        if not(delta > 4):
            for noteIndex in range(beginIndex, endIndex):
                allNotes[noteIndex].shortSlur = True
        else:
            if slurLongPhraseWithBrackets:
                allNotes[beginIndex].beginLongBracketSlur = True
                allNotes[endIndex].endLongBracketSlur = True
            else:
                allNotes[beginIndex + 1].beginLongDoubleSlur = True
                allNotes[endIndex - 1].endLongDoubleSlur = True
    return None

# Raw Segments
# ------------
def getRawSegments(music21Part, segmentBreaks=None):
    allSegments = []
    mnStart = 10E5
    offsetStart = 0.0
    if not segmentBreaks == None:
        segmentIndex = 0
        (mnStart, offsetStart) = segmentBreaks[segmentIndex]
    currentSegment = BrailleSegment()
    for music21Measure in music21Part.getElementsByClass(['Measure', 'Voice']):
        prepareBeamedNotes(music21Measure)
        brailleElements = extractBrailleElements(music21Measure)
        offsetFactor = 0
        previousCode = -1
        for brailleElement in brailleElements:
            if (music21Measure.number > mnStart or\
                music21Measure.number == mnStart and brailleElement.offset >= offsetStart):
                if offsetStart != 0.0:
                    currentSegment.isHyphenated = True
                allSegments.append(currentSegment)
                currentSegment = BrailleSegment()
                try:
                    segmentIndex += 1
                    (mnStart, offsetStart) = segmentBreaks[segmentIndex]
                except IndexError:
                    (mnStart, offsetStart) = (10E5, 0.0)
            if brailleElement.affinityCode < previousCode:
                offsetFactor += 1
            bucketNumber = music21Measure.number * 100 +  offsetFactor * 10 + int(brailleElement.affinityCode)
            currentSegment[bucketNumber].append(brailleElement)
            previousCode = brailleElement.affinityCode
    allSegments.append(currentSegment)
    return allSegments

def extractBrailleElements(music21Measure):
    allElements = BrailleElementGrouping()
    for music21Object in music21Measure:
        try:
            setAffinityCode(music21Object)
            allElements.append(music21Object)
        except BrailleSegmentException as notSupportedException:
            isExempt = [isinstance(music21Object, music21Class) for music21Class in excludeClasses]
            if isExempt.count(True) == 0:
                environRules.warn("{0}".format(notSupportedException))

    allElements.sort(cmp = lambda x, y: cmp(x.offset, y.offset) or cmp(x.classSortOrder, y.classSortOrder))
    if len(allElements) >= 2 and isinstance(allElements[-1], dynamics.Dynamic):
        if isinstance(allElements[-2], bar.Barline):
            allElements[-1].classSortOrder = -1
            allElements.sort(cmp = lambda x, y: cmp(x.offset, y.offset) or cmp(x.classSortOrder, y.classSortOrder))
            
    return allElements

def prepareBeamedNotes(music21Measure):
    allNotes = music21Measure.notes
    for sampleNote in allNotes:
        sampleNote.beamStart = False
        sampleNote.beamContinue = False
    allNotesAndRests = music21Measure.notesAndRests
    allNotesWithBeams = allNotes.splitByClass(None, lambda sampleNote: not(sampleNote.beams == None) and len(sampleNote.beams) > 0)[0]
    allStart = allNotesWithBeams.splitByClass(None, lambda sampleNote: sampleNote.beams.getByNumber(1).type is 'start')[0]
    allStop  = allNotesWithBeams.splitByClass(None, lambda sampleNote: sampleNote.beams.getByNumber(1).type is 'stop')[0]
    if not(len(allStart) == len(allStop)):
        raise BrailleSegmentException("Incorrect beaming: number of start notes != to number of stop notes.")
    
    for beamIndex in range(len(allStart)):
        startNote = allStart[beamIndex]
        stopNote = allStop[beamIndex]
        startIndex = allNotesAndRests.index(startNote)
        stopIndex = allNotesAndRests.index(stopNote)
        delta = stopIndex - startIndex + 1
        if delta < 3: # 2. The group must be composed of at least three notes.
            continue
        # 1. All notes in the group must have precisely the same value.
        # 3. A rest of the same value may take the place of the first note in a group, 
        # but if the rest is located anywhere else, grouping may not be used.
        allNotesOfSameValue = True
        for noteIndex in range(startIndex+1, stopIndex+1):
            if not(allNotesAndRests[noteIndex].duration.type == startNote.duration.type) or isinstance(allNotesAndRests[noteIndex], note.Rest):
                allNotesOfSameValue = False
                break
        try:
            afterStopNote = allNotesAndRests[stopIndex+1]
            if isinstance(afterStopNote, note.Rest) and (int(afterStopNote.beat) == int(stopNote.beat)):
                allNotesOfSameValue = False
                continue
        except stream.StreamException: # stopNote is last note of measure.
            pass
        if not allNotesOfSameValue:
            continue
        try:
            # 4. If the notes in the group are followed immediately by a true eighth note or by an eighth rest, 
            # grouping may not be used, unless the eighth is located in a new measure.
            if allNotesAndRests[stopIndex+1].quarterLength == 0.5:
                continue
        except stream.StreamException: # stopNote is last note of measure.
            pass
        startNote.beamStart = True
        try:
            beforeStartNote = allNotesAndRests[startIndex - 1]
            if isinstance(beforeStartNote, note.Rest) and (int(beforeStartNote.beat) == int(startNote.beat)) and \
                (beforeStartNote.duration.type == startNote.duration.type):
                startNote.beamContinue = True
        except IndexError: # startNote is first note of measure.
            pass
        for noteIndex in range(startIndex+1, stopIndex+1):
            allNotesAndRests[noteIndex].beamContinue = True
    
    return True

#                 music21Class        affinityCode    classSortOrder
affinityCodes = [(note.Note,            9,                   10),
                 (note.Rest,            9,                   10),
                 (chord.Chord,          9,                   10),
                 (dynamics.Dynamic,     9,                    9),
                 (clef.Clef,            9,                    7),
                 (bar.Barline,          9.5,                  0),
                 (key.KeySignature,     3,                    1),
                 (meter.TimeSignature,  3,                    2),
                 (tempo.TempoText,      4,                    3),
                 (tempo.MetronomeMark,  5,                    4),
                 (stream.Voice,         8,                   10)]

def setAffinityCode(music21Object):
    for (music21Class, code, sortOrder) in affinityCodes:
        if isinstance(music21Object, music21Class):
            music21Object.affinityCode = code
            music21Object.classSortOrder = sortOrder
            return None
    
    if isinstance(music21Object, expressions.TextExpression):
        music21Object.affinityCode = 9
        if len(music21Object.content.split()) > 1:
            music21Object.affinityCode = 7
        music21Object.classSortOrder = 8
        return None

    raise BrailleSegmentException("{0} cannot be transcribed to braille.".format(music21Object))

excludeClasses = [spanner.Slur, layout.SystemLayout, layout.PageLayout]

# Grouping Attributes
# -------------------
def addGroupingAttributes(allSegments, music21Part, **partKeywords):
    currentKeySig = key.KeySignature(0)
    try:
        currentTimeSig = music21Part.getElementsByClass(['Measure','Voice'])[0].bestTimeSignature()
    except stream.StreamException:
        currentTimeSig = meter.TimeSignature('4/4')

    descendingChords = None
    showClefSigns = False
    upperFirstInNoteFingering = True

    if 'showClefSigns' in partKeywords:
        showClefSigns = partKeywords['showClefSigns']
    if 'upperFirstInNoteFingering' in partKeywords:
        upperFirstInNoteFingering = partKeywords['upperFirstInNoteFingering']
    if 'showHand' in partKeywords:
        if partKeywords['showHand'] == 'left':
            descendingChords = False
        elif partKeywords['showHand'] == 'right':
            descendingChords = True
    if descendingChords is None:
        try:
            bc = music21Part.getElementsByClass(['Measure','Voice'])[0].getClefs()[0]
            descendingChords = False
            if isinstance(bc, clef.TrebleClef) or isinstance(bc, clef.AltoClef):
                descendingChords = True
        except stream.StreamException:
            descendingChords = True
            
    for brailleSegment in allSegments:
        for (groupingKey, groupingList) in sorted(brailleSegment.items()):
            if groupingKey % 10 == 3:
                for brailleElement in groupingList:
                    if isinstance(brailleElement, meter.TimeSignature):
                        currentTimeSig = brailleElement
                    elif isinstance(brailleElement, key.KeySignature):
                        brailleElement.outgoingKeySig = currentKeySig
                        currentKeySig = brailleElement
            elif groupingKey % 10 == 9:
                allGeneralNotes = [n for n in groupingList if isinstance(n, note.GeneralNote)]
                if len(allGeneralNotes) == 1 and isinstance(allGeneralNotes[0], note.Rest):
                    if allGeneralNotes[0].quarterLength == currentTimeSig.totalLength:
                        allGeneralNotes[0].quarterLength = 4.0
            groupingList.keySignature = currentKeySig
            groupingList.timeSignature = currentTimeSig
            groupingList.descendingChords = descendingChords
            groupingList.showClefSigns = showClefSigns
            groupingList.upperFirstInNoteFingering = upperFirstInNoteFingering
            
    return None

# Segment Attributes
# ------------------
def addSegmentAttributes(allSegments, music21Part, **partKeywords):        
    for brailleSegment in allSegments:
        if 'cancelOutgoingKeySig' in partKeywords:
            brailleSegment.cancelOutgoingKeySig = partKeywords['cancelOutgoingKeySig']
        if 'dummyRestLength' in partKeywords:
            brailleSegment.dummyRestLength = partKeywords['dummyRestLength']
        if 'maxLineLength' in partKeywords:
            brailleSegment.maxLineLength = partKeywords['maxLineLength']
        if 'showFirstMeasureNumber' in partKeywords:
            brailleSegment.showFirstMeasureNumber = partKeywords['showFirstMeasureNumber']
        if 'showHand' in partKeywords:
            brailleSegment.showHand = partKeywords['showHand']
        if 'showHeading' in partKeywords:
            brailleSegment.showHeading = partKeywords['showHeading']
        if 'suppressOctaveMarks' in partKeywords:
            brailleSegment.suppressOctaveMarks = partKeywords['suppressOctaveMarks']  
    return None

# Articulations
# -------------
def fixArticulations(allSegments):
    for brailleSegment in allSegments:
        newSegment = brailleSegment.consolidate()
        for noteGrouping in [newSegment[gpKey] for gpKey in newSegment.keys() if gpKey % 10 == 9]:
            allNotes = [n for n in noteGrouping if isinstance(n,note.Note)]
            for noteIndexStart in range(len(allNotes)):
                music21NoteStart = allNotes[noteIndexStart]
                for artc in music21NoteStart.articulations:
                    if isinstance(artc, articulations.Staccato) or isinstance(artc, articulations.Tenuto):
                        if not music21NoteStart.tie == None:
                            if music21NoteStart.tie.type == 'stop':
                                allNotes[noteIndexStart-1].tie = None
                                allNotes[noteIndexStart-1].shortSlur = True
                            else:
                                allNotes[noteIndexStart+1].tie = None
                                music21NoteStart.shortSlur = True
                            music21NoteStart.tie = None
                    numSequential=0
                    for noteIndexContinue in range(noteIndexStart+1, len(allNotes)):
                        music21NoteContinue = allNotes[noteIndexContinue]
                        if artc in music21NoteContinue.articulations:
                            numSequential+=1
                            continue
                        break
                    if numSequential >= 3:
                        music21NoteStart.articulations.append(artc)
                        for noteIndexContinue in range(noteIndexStart+1, noteIndexStart+numSequential):
                            music21NoteContinue = allNotes[noteIndexContinue]
                            music21NoteContinue.articulations.remove(artc)
    return None

#-------------------------------------------------------------------------------
# Helper Methods

def splitMeasure(music21Measure, value = 2, beatDivisionOffset = 0, useTimeSignature = None):
    '''
    Takes a measure and splits it in two parts, although not necessarily in half.
    Value is the number of partitions to split a time signature into.
    The first part will contain all elements found within the offsets of the first partition..
    The last part will contain all elements not found within the offsets of the first partition.
    beatDivisionOffset is meant to adjust the end offset of the first partition by a certain
    number of beats to the left.
    '''
    if not useTimeSignature == None:
        ts = useTimeSignature
    else:
        ts = music21Measure.timeSignature
    
    offset = 0.0
    if not(beatDivisionOffset == 0):
        if abs(beatDivisionOffset) > ts.beatDivisionDurations:
            raise Exception()
        i = len(ts.beatDivisionDurations) - abs(beatDivisionOffset)
        offset += ts.beatDivisionDurations[i].quarterLength
        
    bs = copy.deepcopy(ts.beatSequence)
    try:  
        bs.partitionByCount(value, loadDefault = False)
        (startOffsetZero, endOffsetZero) = bs.getLevelSpan()[0]
    except meter.MeterException:
        value += 1
        bs.partitionByCount(value, loadDefault = False)
        startOffsetZero = bs.getLevelSpan()[0][0]
        endOffsetZero = bs.getLevelSpan()[-2][-1]
    endOffsetZero -= offset
    newMeasures = stream.Part()
    newMeasures.append(stream.Measure())
    newMeasures.append(stream.Measure())
    for x in music21Measure:
        if x.offset >= startOffsetZero and (x.offset < endOffsetZero or (x.offset == endOffsetZero and isinstance(x, bar.Barline))):
            newMeasures[0].insert(x.offset, x)
        else:
            newMeasures[1].insert(x.offset, x)
    for n in newMeasures[1].notes:
        if n.tie != None:
            newMeasures[0].append(n)
            newMeasures[1].remove(n)
            endOffsetZero += n.duration.quarterLength
            continue
        break

    r0 = note.Rest(quarterLength = music21Measure.duration.quarterLength - endOffsetZero)
    newMeasures[0].insert(endOffsetZero, r0)
    r1 = note.Rest(quarterLength = endOffsetZero)
    newMeasures[1].insert(0.0, r1)
    
    ts0_delete = False
    if newMeasures[0].timeSignature == None:
        ts0_delete = True
        newMeasures[0].timeSignature = ts
    newMeasures[1].timeSignature = ts
    newMeasures[0].mergeAttributes(music21Measure)
    newMeasures[1].mergeAttributes(music21Measure)
    newMeasures[0].makeBeams()
    newMeasures[1].makeBeams()
    prepareBeamedNotes(newMeasures[0])
    prepareBeamedNotes(newMeasures[1])
    newMeasures[0].remove(r0)
    newMeasures[1].remove(r1)
    if ts0_delete == True:
        newMeasures[0].remove(ts)
    newMeasures[1].remove(ts)
    return newMeasures

def splitStreamByClass(music21Measure, classFilterList, groupWithPrevious = False):
    elementsOfClasses = music21Measure.getElementsByClass(classFilterList)
    if len(elementsOfClasses) == 0:
        return [music21Measure]
    
    elementsByOffset = elementsOfClasses.groupElementsByOffset(returnDict = True)
    if len(elementsByOffset.keys()) == 1 and 0.0 in elementsByOffset:
        return [music21Measure]

    allStreams = []
    startIndex = 0
    endIndex = 0
    for offset in elementsByOffset:
        if not(offset == 0.0):
            if not groupWithPrevious:
                endIndex = music21Measure.index(elementsByOffset[offset][0])
            else:
                endIndex = music21Measure.index(elementsByOffset[offset][-1]) + 1
            allStreams.append(music21Measure[startIndex:endIndex])
            startIndex = endIndex
    endIndex = len(music21Measure)
    allStreams.append(music21Measure[startIndex:endIndex])
    return allStreams

#-------------------------------------------------------------------------------

class BrailleSegmentException(music21.Music21Exception):
    pass
    
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass


if __name__ == "__main__":
    import sys
    reload(sys)
    sys.setdefaultencoding("UTF-8")
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof