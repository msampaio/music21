# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         romanText/translate.py
# Purpose:      Translation routines for roman numeral analysis text files
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


'''Translation routines for roman numeral analysis text files, as defined and demonstrated by Dmitri Tymoczko.
'''
import unittest
import music21
import copy

from music21 import common
from music21.romanText import base as romanTextModule

from music21 import environment
_MOD = 'romanText.translate.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
class TranslateRomanTextException(Exception):
    pass


def _copySingleMeasure(t, p, kCurrent):
    '''Given a RomanText token, a Part used as the current container, and the current Key, return a Measure copied from the past of the Part. 
    '''
    # copy from a past location; need to change key
    #environLocal.printDebug(['calling _copySingleMeasure()'])
    targetNumber, targetRepeat = t.getCopyTarget()
    if len(targetNumber) > 1: # this is an encoding error
        raise TranslateRomanTextException('a single measure cannot define a copy operation for multiple measures')
    # TODO: ignoring repeat letters
    target = targetNumber[0]
    for mPast in p.getElementsByClass('Measure'):
        if mPast.number == target:
            m = copy.deepcopy(mPast)
            m.number = t.number[0]
            # update all keys
            for rnPast in m.getElementsByClass('RomanNumeral'):
                if kCurrent is None: # should not happen
                    raise TranslateRomanTextException('attempting to copy a measure but no past key definitions are found')
                rnPast.setKeyOrScale(kCurrent)
            break
    return m

def _copyMultipleMeasures(t, p, kCurrent):
    '''Given a RomanText token for a RTMeasure, a Part used as the current container, and the current Key, return a Measure range copied from the past of the Part.
    '''
    from music21 import stream
    # the key provided needs to be the current key
    #environLocal.printDebug(['calling _copyMultipleMeasures()'])

    targetNumbers, targetRepeat = t.getCopyTarget()
    if len(targetNumbers) == 1: # this is an encoding error
        raise TranslateRomanTextException('a multiple measure range cannot copy a single measure')
    # TODO: ignoring repeat letters
    targetStart = targetNumbers[0]
    targetEnd = targetNumbers[1]
    
    if t.number[1] - t.number[0] != targetEnd - targetStart:
        raise TranslateRomanTextException('both the source and destination sections need to have the same number of measures')
    elif t.number[0] < targetEnd:
        raise TranslateRomanTextException('the source section cannot overlap with the destination section')

    measures = []
    for mPast in p.getElementsByClass('Measure'):
        if mPast.number in range(targetStart, targetEnd +1):
            m = copy.deepcopy(mPast)
            m.number = t.number[0] + mPast.number - targetStart
            measures.append(m)
            # update all keys
            for rnPast in m.getElementsByClass('RomanNumeral'):
                if kCurrent is None: # should not happen
                    raise TranslateRomanTextException('attempting to copy a measure but no past key definitions are found')
                rnPast.setKeyOrScale(kCurrent)
        if mPast.number == targetEnd:
            break
    return measures


def _getKeyAndPrefix(rtKeyOrString):
    '''
    Given an RTKey specification, return 
    the Key and a string prefix based on the tonic. 

    >>> _getKeyAndPrefix('c')
    (<music21.key.Key of c minor>, 'c: ')
    >>> _getKeyAndPrefix('F#')
    (<music21.key.Key of F# major>, 'F#: ')
    >>> _getKeyAndPrefix('Eb')
    (<music21.key.Key of E- major>, 'E-: ')
    >>> _getKeyAndPrefix('Bb')
    (<music21.key.Key of B- major>, 'B-: ')
    >>> _getKeyAndPrefix('bb')
    (<music21.key.Key of b- minor>, 'b-: ')
    >>> _getKeyAndPrefix('b#')
    (<music21.key.Key of b# minor>, 'b#: ')

    '''
    from music21 import key
    if common.isStr(rtKeyOrString):
        rtKeyOrString = key.convertKeyStringToMusic21KeyString(rtKeyOrString)
        k = key.Key(rtKeyOrString)
    else:
        k = rtKeyOrString.getKey()

    prefix = k.tonic + ": "
    return k, prefix

def romanTextToStreamScore(rtHandler, inputM21=None):
    '''Given a roman text handler or string, return or fill a Score Stream.
    '''
    # accept a string directly; mostly for testing
    if common.isStr(rtHandler):
        rtf = romanTextModule.RTFile()
        rtHandler = rtf.readstr(rtHandler) # return handler, processes tokens

    # this could be just a Stream, but b/c we are creating metadata, perhaps better to match presentation of other scores. 

    from music21 import metadata
    from music21 import stream
    from music21 import note
    from music21 import meter
    from music21 import key
    from music21 import roman
    from music21 import tie


    if inputM21 == None:
        s = stream.Score()
    else:
        s = inputM21

    # metadata can be first
    md = metadata.Metadata()
    s.insert(0, md)

    p = stream.Part()
    # ts indication are found in header, and also found elsewhere
    tsCurrent = meter.TimeSignature('4/4') # create default 4/4
    tsSet = False # store if set to a measure
    lastMeasureNumber = 0
    previousRn = None
    keySigCurrent = None
    keySigSet = True  # set a keySignature
    foundAKeySignatureSoFar = False
    kCurrent, prefixLyric = _getKeyAndPrefix('C') # default if none defined
    prefixLyric = ''

    for t in rtHandler.tokens:
        #environLocal.printDebug(['token', t])
        if t.isTitle():
            md.title = t.data            
        elif t.isWork():
            md.alternativeTitle = t.data
        elif t.isPiece():
            md.alternativeTitle = t.data
        elif t.isComposer():
            md.composer = t.data
        elif t.isMovement():
            md.movementNumber = t.data

        elif t.isTimeSignature():
            tsCurrent = meter.TimeSignature(t.data)
            tsSet = False
            #environLocal.printDebug(['tsCurrent:', tsCurrent])
        elif t.isKeySignature():
            if t.data == "":
                keySigCurrent = key.KeySignature(0)
            elif t.data == "Bb":
                keySigCurrent = key.KeySignature(-1)
            else:
                pass 
                # better to print a message
                #environLocal.printDebug(['still need to write a generic RomanText KeySignature routine.  this is just temporary'])
                #raise TranslateRomanTextException("still need to write a generic RomanText KeySignature routine.  this is just temporary")
            keySigSet = False
            #environLocal.printDebug(['keySigCurrent:', keySigCurrent])
            foundAKeySignatureSoFar = True
        elif t.isMeasure():
            #environLocal.printDebug(['handling measure token:', t])

            if t.variantNumber is not None:
                #environLocal.printDebug(['skipping variant: %s' % t])
                continue
            if t.variantLetter is not None:
                #environLocal.printDebug(['skipping variant: %s' % t])
                continue

            # if this measure number is more than 1 greater than the last
            # defined measure number, and the previous chord is not None, 
            # then fill with copies of the last-defined measure
            if ((t.number[0] > lastMeasureNumber + 1) and 
                (previousRn is not None)):
                for i in range(lastMeasureNumber + 1, t.number[0]):
                    mFill = stream.Measure()
                    mFill.number = i
                    newRn = copy.deepcopy(previousRn)
                    newRn.lyric = ""
                    # set to entire bar duration and tie 
                    newRn.duration = copy.deepcopy(tsCurrent.barDuration)
                    if previousRn.tie is None:
                        previousRn.tie = tie.Tie('start')
                    else:
                        previousRn.tie.type = 'continue'
                    # set to stop for now; may extend on next iteration
                    newRn.tie = tie.Tie('stop')
                    previousRn = newRn
                    mFill.append(newRn)
                    p.append(mFill)
                lastMeasureNumber = t.number[0] - 1
            # create a new measure or copy a past measure
            if len(t.number) == 1 and t.isCopyDefinition: # if not a range
                m = _copySingleMeasure(t, p, kCurrent)
                p.append(m)
                lastMeasureNumber = m.number
                romans = m.getElementsByClass(roman.RomanNumeral)
                if len(romans) > 0:
                    previousRn = romans[-1] 
            elif len(t.number) > 1:
                measures = _copyMultipleMeasures(t, p, kCurrent)
                p.append(measures)
                lastMeasureNumber = measures[-1].number
                romans = measures[-1].getElementsByClass(roman.RomanNumeral)
                if len(romans) > 0:
                    previousRn = romans[-1]
            else:       
                m = stream.Measure()
                m.number = t.number[0]
                lastMeasureNumber = t.number[0]
                
                if not tsSet:
                    m.timeSignature = tsCurrent
                    tsSet = True # only set when changed
                if not keySigSet and keySigCurrent is not None:
                    m.insert(0, keySigCurrent)
                    keySigSet = True # only set when changed
    
                o = 0.0 # start offsets at zero
                previousChordInMeasure = None
                pivotChordPossible = False
                for i, a in enumerate(t.atoms):
                    if isinstance(a, romanTextModule.RTKey) or \
                       ((foundAKeySignatureSoFar == False) and \
                        (isinstance(a, romanTextModule.RTAnalyticKey))): 
                        # found a change of Key+KeySignature or
                        # just found a change of analysis but no keysignature so far
                
                        #environLocal.printDebug(['handling key token:', a])
                        try: # this sets the key and the keysignature
                            kCurrent, pl = _getKeyAndPrefix(a)
                            prefixLyric += pl
                        except:
                            raise TranslateRomanTextException('cannot get key from %s in line %s' % (a.src, t.src))
                        #insert at beginning of measure if at beginning -- for things like pickups.
                        if m.number < 2:
                            m.insert(0, kCurrent)
                        else:
                            m.insert(o, kCurrent)
                        foundAKeySignatureSoFar = True

                    elif isinstance(a, romanTextModule.RTKeySignature):
                        try: # this sets the keysignature but not the prefix text
                            thisSig = a.getKeySignature()
                        except:
                            raise TranslateRomanTextException('cannot get key from %s in line %s' % (a.src, t.src))
                        #insert at beginning of measure if at beginning -- for things like pickups.
                        if m.number < 2:
                            m.insert(0, thisSig)
                        else:
                            m.insert(o, thisSig)
                        foundAKeySignatureSoFar = True

                    elif isinstance(a, romanTextModule.RTAnalyticKey):
                        # just a change in analyzed key, not a change in anything else
                        try: # this sets the key, not the keysignature
                            kCurrent, pl = _getKeyAndPrefix(a)
                            prefixLyric += pl
                        except:
                            raise TranslateRomanTextException('cannot get key from %s in line %s' % (a.src, t.src))

                    elif isinstance(a, romanTextModule.RTBeat):
                        # set new offset based on beat
                        try:
                            o = a.getOffset(tsCurrent)
                        except ValueError:
                            raise TranslateRomanTextException("cannot properly get an offset from beat data %s under timeSignature %s in line %s" % (a.src, tsCurrent, t.src))
                        if (previousChordInMeasure is None and 
                            previousRn is not None and o > 0):
                            # setting a new beat before giving any chords
                            firstChord = copy.deepcopy(previousRn)
                            firstChord.quarterLength = o
                            firstChord.lyric = ""
                            if previousRn.tie == None:
                                previousRn.tie = tie.Tie('start')
                            else:
                                previousRn.tie.type = 'continue'    
                            firstChord.tie = tie.Tie('stop')
                            previousRn = firstChord
                            previousChordInMeasure = firstChord
                            m.insert(0, firstChord)
                        pivotChordPossible = False
                    
                    elif isinstance(a, romanTextModule.RTChord):
                        # use source to evaluation roman 
                        try:
                            rn = roman.RomanNumeral(a.src, copy.deepcopy(kCurrent))
                        except (roman.RomanNumeralException, 
                            common.Music21CommonException): 
                            #environLocal.printDebug('cannot create RN from: %s' % a.src)
                            rn = note.Note() # create placeholder 
                        if pivotChordPossible == False:
                            # probably best to find duration
                            if previousChordInMeasure is None:
                                pass # use default duration
                            else: # update duration of previous chord in Measure
                                oPrevious = previousChordInMeasure.getOffsetBySite(m)
                                newQL = o - oPrevious
                                if newQL <= 0:
                                    raise TranslateRomanTextException('too many notes in this measure: %s' % t.src)
                                previousChordInMeasure.quarterLength = newQL                          
                            
                            rn.addLyric(prefixLyric + a.src)
                            prefixLyric = ""
                            m.insert(o, rn)
                            previousChordInMeasure = rn
                            previousRn = rn
                            pivotChordPossible = True
                        else:
                            previousChordInMeasure.lyric += "//" + prefixLyric + a.src
                            prefixLyric = ""
                            pivotChordPossible = False

                
                # may need to adjust duration of last chord added
                previousRn.quarterLength = tsCurrent.barDuration.quarterLength - o
                p.append(m)
    p.makeBeams(inPlace=True)
    p.makeAccidentals(inPlace=True)
    s.insert(0, p)
    return s


def romanTextToStreamOpus(rtHandler, inputM21=None):
    '''Return either a Score object, or, if a multi-movement work is defined, an Opus object. 
    '''
    from music21 import stream
    if common.isStr(rtHandler):
        rtf = romanTextModule.RTFile()
        rtHandler = rtf.readstr(rtHandler) # return handler, processes tokens

    if rtHandler.definesMovements(): # create an opus
        if inputM21 == None:
            s = stream.Opus()
        else:
            s = inputM21
        # copy the common header to each of the sub-handlers
        handlerBundles = rtHandler.splitByMovement(duplicateHeader=True)
        # see if we have header information
        for h in handlerBundles:
            #print h, len(h)
            # append to opus
            s.append(romanTextToStreamScore(h))
        return s # an opus
    else: # create a Score
        return romanTextToStreamScore(rtHandler, inputM21=inputM21)


#-------------------------------------------------------------------------------
class TestExternal(unittest.TestCase):

    def runTest(self):
        pass
 
    def testExternalA(self):
        from music21 import romanText
        from music21.romanText import testFiles

        for tf in testFiles.ALL:
            rtf = romanText.RTFile()
            rth = rtf.readstr(tf) # return handler, processes tokens
            s = romanTextToStreamScore(rth)
            s.show()


class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def testBasicA(self):
        from music21 import romanText
        from music21.romanText import testFiles

        for tf in testFiles.ALL:
            rtf = romanText.RTFile()
            rth = rtf.readstr(tf) # return handler, processes tokens
            s = romanTextToStreamScore(rth)
            #s.show()

        
        s = romanTextToStreamScore(testFiles.swv23)
        self.assertEqual(s.metadata.composer, 'Heinrich Schutz')
        # this is defined as a Piece tag, but shows up here as a title, after
        # being set as an alternate title
        self.assertEqual(s.metadata.title, 'Warum toben die Heiden, Psalmen Davids no. 2, SWV 23')
        

        s = romanTextToStreamScore(testFiles.riemenschneider001)
        self.assertEqual(s.metadata.composer, 'J. S. Bach')
        self.assertEqual(s.metadata.title, 'Aus meines Herzens Grunde')

        s = romanTextToStreamScore(testFiles.monteverdi_3_13)
        self.assertEqual(s.metadata.composer, 'Claudio Monteverdi')

    def testBasicB(self):
        from music21 import romanText
        from music21.romanText import testFiles

        s = romanTextToStreamScore(testFiles.riemenschneider001)
        #s.show()

    def testMeasureCopyingA(self):
        from music21 import romanText
        from music21.romanText import testFiles

        s = romanTextToStreamScore(testFiles.swv23)
        mStream = s.parts[0].getElementsByClass('Measure')
        # the first four measures should all have the same content
        rn1 = mStream[1].getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn1.pitches), '[D5, F#5, A5]')
        self.assertEqual(str(rn1.figure), 'V')
        rn2 = mStream[1].getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn2.figure), 'i')

        # make sure that m2, m3, m4 have the same values
        rn1 = mStream[2].getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn1.figure), 'V')
        rn2 = mStream[2].getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn2.figure), 'i')

        rn1 = mStream[3].getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn1.figure), 'V')
        rn2 = mStream[3].getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn2.figure), 'i')


        # test multiple measure copying
        s = romanTextToStreamScore(testFiles.monteverdi_3_13)
        mStream = s.parts[0].getElementsByClass('Measure')
        for m in mStream:
            if m.number == 41: #m49-51 = m41-43
                m1a = m
            elif m.number == 42: #m49-51 = m41-43
                m2a = m
            elif m.number == 43: #m49-51 = m41-43
                m3a = m
            elif m.number == 49: #m49-51 = m41-43
                m1b = m
            elif m.number == 50: #m49-51 = m41-43
                m2b = m
            elif m.number == 51: #m49-51 = m41-43
                m3b = m

        rn = m1a.getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn.figure), 'IV')        
        rn = m1a.getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn.figure), 'I')        

        rn = m1b.getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn.figure), 'IV')        
        rn = m1b.getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn.figure), 'I')        

        rn = m2a.getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn.figure), 'I')        
        rn = m2a.getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn.figure), 'ii')        

        rn = m2b.getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn.figure), 'I')        
        rn = m2b.getElementsByClass('RomanNumeral')[1]
        self.assertEqual(str(rn.figure), 'ii')        

        rn = m3a.getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn.figure), 'V/ii')        
        rn = m3b.getElementsByClass('RomanNumeral')[0]
        self.assertEqual(str(rn.figure), 'V/ii')        


    def testRomanTextString(self):
        from music21 import converter
        s = converter.parse('m1 KS1 I \n m2 V6/5 \n m3 I b3 V7 \n m4 KS-3 vi \n m5 a: i b3 V4/2 \n m6 I', format='romantext')

        rnStream = s.flat.getElementsByClass('RomanNumeral')
        self.assertEqual(rnStream[0].figure, 'I')
        self.assertEqual(rnStream[1].figure, 'V6/5')        
        self.assertEqual(rnStream[2].figure, 'I')
        self.assertEqual(rnStream[3].figure, 'V7')
        self.assertEqual(rnStream[4].figure, 'vi')
        self.assertEqual(rnStream[5].figure, 'i')
        self.assertEqual(rnStream[6].figure, 'V4/2')
        self.assertEqual(rnStream[7].figure, 'I')

        rnStreamKey = s.flat.getElementsByClass('KeySignature')
        self.assertEqual(rnStreamKey[0].sharps, 1)
        self.assertEqual(rnStreamKey[1].sharps, -3)

        #s.show()


    def testMeasureCopyingB(self):
        from music21 import converter
        from music21 import pitch

        src = """m1 G: IV || b3 d: III b4 ii
m2 v b2 III6 b3 iv6 b4 ii/o6/5
m3 i6/4 b3 V
m4-5 = m2-3
m6-7 = m4-5
"""
        s = converter.parse(src, format='romantext')
        rnStream = s.flat.getElementsByClass('RomanNumeral')

        for elementNumber in [0, 6, 12]:
            self.assertEqual(rnStream[elementNumber + 4].figure, 'III6')
            self.assertEqual(str(rnStream[elementNumber + 4].pitches), '[A4, C5, F5]')

            x = rnStream[elementNumber + 4].pitches[2].accidental
            if x == None: x = pitch.Accidental('natural')
            self.assertEqual(x.alter, 0)

            self.assertEqual(rnStream[elementNumber + 5].figure, 'iv6')
            self.assertEqual(str(rnStream[elementNumber + 5].pitches), '[B-4, D5, G5]')

            self.assertEqual(rnStream[elementNumber + 5].pitches[0].accidental.displayStatus, True)



        from music21.romanText import testFiles
        s = converter.parse(testFiles.monteverdi_3_13)
        m25 = s.measure(25)
        rn = m25.flat.getElementsByClass('RomanNumeral')
        self.assertEqual(rn[1].figure, 'III')
        self.assertEqual(str(rn[1].scale), 'd minor')

        # TODO: this is getting the F#m even though the key and figure are 
        # correect
        #self.assertEqual(str(rn[1].pitches), '[F4, A4, C5]')

        #s.show()
        

    def testOpus(self):
        from music21 import stream
        from music21 import romanText
        from music21.romanText import testFiles

        o = romanTextToStreamOpus(testFiles.mozartK279)
        self.assertEqual(o.scores[0].metadata.movementNumber, '1')
        self.assertEqual(o.scores[0].metadata.composer, 'Mozart')
        self.assertEqual(o.scores[1].metadata.movementNumber, '2')
        self.assertEqual(o.scores[1].metadata.composer, 'Mozart')
        self.assertEqual(o.scores[2].metadata.movementNumber, '3')
        self.assertEqual(o.scores[2].metadata.composer, 'Mozart')


        # test using converter.
        from music21 import converter
        s = converter.parse(testFiles.mozartK279)
        self.assertEqual('Opus' in s.classes, True)
        self.assertEqual(len(s.scores), 3)

        # make sure a normal file is still a Score
        s = converter.parse(testFiles.riemenschneider001)
        self.assertEqual('Score' in s.classes, True)
        

#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof
