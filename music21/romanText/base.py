# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         romanText/base.py
# Purpose:      music21 classes for processing roman numeral analysis text files
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


'''Objects for processing roman numeral analysis text files, as defined and demonstrated by Dmitri Tymoczko.
'''

import unittest
import re
import codecs
try:
    import StringIO # python 2 
except:
    from io import StringIO # python3 (also in python 2.6+)


import music21

from music21 import common
from music21 import environment
_MOD = 'romanText.base.py'
environLocal = environment.Environment(_MOD)


# alternate endings might end with a,b,c for non 
# zero or more for everything after the first number
reMeasureTag = re.compile('m[0-9]+[a-b]*-*[0-9]*[a-b]*')
reVariant = re.compile('var[0-9]+')
reVariantLetter = re.compile('var([A-Z]+)')
reNoteTag = re.compile('[Nn]ote:')

reOptKeyOpenAtom = re.compile('\?\([A-Ga-g]+[b#]*:')
reOptKeyCloseAtom = re.compile('\?\)[A-Ga-g]+[b#]*:?')
reKeyAtom = re.compile('[A-Ga-g]+[b#]*;:')
reAnalyticKeyAtom = re.compile('[A-Ga-g]+[b#]*:')
reKeySignatureAtom = re.compile('KS\-?[0-7]')
# must distinguish b3 from bVII; there may be b1.66.5
reBeatAtom = re.compile('b[1-9.]+')



#-------------------------------------------------------------------------------
class RomanTextException(music21.Music21Exception):
    pass
class RTTokenException(music21.Music21Exception):
    pass
class RTHandlerException(music21.Music21Exception):
    pass
class RTFileException(music21.Music21Exception):
    pass



#-------------------------------------------------------------------------------
class RTToken(object):
    '''
    Stores each linear, logical entity of a RomanText.

    A multi-pass parsing procedure is likely necessary, as RomanText permits variety of groupings and markings.

    '''
    def __init__(self, src=u''):
        self.src = src # store source character sequence

    def __repr__(self):
        return '<RTToken %r>' % self.src

    def isComposer(self):
        return False

    def isTitle(self):
        return False

    def isPiece(self):
        return False

    def isAnalyst(self):
        return False

    def isProofreader(self):
        return False

    def isTimeSignature(self):
        return False

    def isKeySignature(self):
        return False

    def isNote(self):
        return False

    def isForm(self):
        '''Occasionally found in header.
        '''
        return False

    def isMeasure(self):
        return False

    def isPedal(self):
        return False

    def isWork(self):
        return False

    def isMovement(self):
        return False

    def isAtom(self):
        '''Atoms are any untagged data; generally only found inside of a measure definition. 
        '''
        return False


class RTTagged(RTToken):
    '''In roman text, some data elements are tagged: there is tag, followed by some data. In other elements, there is just data.

    All tagged tokens are subclasses of this class. Examples are Title:
    '''
    def __init__(self, src =u''):
        RTToken.__init__(self, src)
        # try to split off tag from data
        self.tag = ''
        self.data = ''
        if ':' in src:
            iFirst = src.find(':') # first index found at
            self.tag = src[:iFirst].strip()
            # add one to skip colon
            self.data = src[iFirst+1:].strip()
        else: # we do not have a clear tag; perhaps store all as data
            self.data = src

    def __repr__(self):
        return '<RTTagged %r>' % self.src


    def isComposer(self):
        '''
        >>> from music21 import *
        >>> rth = romanText.RTTagged('Composer: Claudio Monteverdi')
        >>> rth.isComposer()
        True
        >>> rth.isTitle()
        False
        >>> rth.isWork()
        False
        >>> rth.data 
        'Claudio Monteverdi'
        '''
        if self.tag.lower() in ['composer']:
            return True
        return False

    def isTitle(self):
        if self.tag.lower() in ['title']:
            return True
        return False

    def isPiece(self):
        if self.tag.lower() in ['piece']:
            return True
        return False

    def isAnalyst(self):
        if self.tag.lower() in ['analyst']:
            return True
        return False

    def isProofreader(self):
        if self.tag.lower() in ['proofreader', 'proof reader']:
            return True
        return False

    def isTimeSignature(self):
        '''TimeSignature header data can be found intermingled with measures. 
        '''
        if self.tag.lower() in ['timesignature', 'time signature']:
            return True
        return False

    def isKeySignature(self):
        '''
        KeySignatures are a type of tagged data found outside of measures, such as"Key Signature: Bb," meaning one flat.
        
        Note: this is not the same as a key definition found inside of a Measure: these are represented by RTKey objects, defined below, and are not RTTagged objects, but RTAtom subclasses. 
        '''
        if self.tag.lower() in ['keysignature', 'key signature']:
            return True
        else:
            return False
    
    def isNote(self):
        if self.tag.lower() in ['note']:
            return True
        return False


    def isForm(self):
        if self.tag.lower() in ['form']:
            return True
        return False

    def isPedal(self):
        if self.tag.lower() in ['pedal']:
            return True
        return False

    def isWork(self):
        '''
        The "work" is not defined as a header tag, but is used 
        to represent all tags, often placed after Composer, for 
        the work or pieces designation. 

        >>> from music21 import *
        >>> rth = romanText.RTTagged('Madrigal: 4.12')
        >>> rth.isTitle()
        False
        >>> rth.isWork()
        True
        >>> rth.tag
        'Madrigal'
        >>> rth.data 
        '4.12'

        '''
        if self.tag == 'Work' or self.tag == 'Madrigal':
            return True
        else:
            return False

    def isMovement(self):
        if self.tag.lower() in ['movement']:
            return True
        return False



class RTMeasure(RTToken):
    '''In roman text, measures are given one per line and always start with 'm'.

    Measure ranges can be used and copied, such as m3-4=m1-2

    Variants are not part of the tag, but are read into an attribute: m1var1 ii
    '''
    def __init__(self, src =u''):
        '''
        >>> from music21 import *
        >>> rtm = romanText.RTMeasure('m15 V6 b1.5 V6/5 b2 I b3 viio6')
        >>> rtm.data
        'V6 b1.5 V6/5 b2 I b3 viio6'
        >>> rtm.number
        [15]
        '''
        RTToken.__init__(self, src)
        # try to split off tag from data
        self.tag = '' # the measure number or range
        self.data = '' # only chord, phrase, and similar definitions
        self.number = [] # one or more measure numbers
        self.repeatLetter = [] # one or more repeat letters
        self.variantNumber = None # a one-measure or short variant
        self.variantLetter = None # a longer-variant that defines a different way of reading a large section 
        # store boolean if this measure defines copying another range
        self.isCopyDefinition = False
        # store processed tokens associated with this measure
        self.atoms = []

        if len(src) > 0:
            self._parseAttributes(src)

    def _getMeasureNumberData(self, src):
        '''Return the number or numbers as a list, as well as any repeat indications. 

        >>> from music21 import *
        >>> rtm = romanText.RTMeasure()
        >>> rtm._getMeasureNumberData('m77')
        ([77], [''])
        >>> rtm._getMeasureNumberData('m123b-432b')
        ([123, 432], ['b', 'b'])
        '''
        # note: this is separate procedure b/c it is used to get copy
        # boundaries
        if '-' in src: # its a range
            mnStart, mnEnd = src.split('-')
            proc = [mnStart, mnEnd]
        else:
            proc = [src] # treat as one
        number = []
        repeatLetter = []
        for mn in proc:
            # append in order, start, end
            numStr, alphaStr = common.getNumFromStr(mn)
            number.append(int(numStr))
            # remove all 'm' in alpha
            alphaStr = alphaStr.replace('m', '')
            repeatLetter.append(alphaStr)    
        return number, repeatLetter

    def _parseAttributes(self, src):
        # assume that we have already checked that this is a measure
        g = reMeasureTag.match(src)
        if g is None: # not measure tag found
            raise RTHandlerException('found no measure tag: %s' % src)
        iEnd = g.end() # get end index
        rawTag = src[:iEnd].strip()
        self.tag = rawTag
        rawData = src[iEnd:].strip() # may have variant

        # get the number list from the tag
        self.number, self.repeatLetter = self._getMeasureNumberData(rawTag)
 
        # strip a variant indication off of rawData if found
        g = reVariant.match(rawData)
        if g is not None: # there is a variant tag
            varStr = g.group(0)
            self.variantNumber = int(common.getNumFromStr(varStr)[0])
            self.data = rawData[g.end():].strip()
        else:
            self.data = rawData
        g = reVariantLetter.match(rawData)
        if g is not None: # there is a variant letter tag
            varStr = g.group(1)
            self.variantLetter = varStr
            self.data = rawData[g.end():].strip()
            

        if self.data.startswith('='):
            self.isCopyDefinition = True

    def __repr__(self):
        if len(self.number) == 1:
            numberStr = '%s' % self.number[0]
        else:
            numberStr = '%s-%s' % (self.number[0], self.number[1])

        return '<RTMeasure %s>' % numberStr

    def isMeasure(self):
        return True

    def getCopyTarget(self):
        '''If this measure defines a copy operation, return two lists defining the measures to copy; the second list
        has the repeat data.

        >>> from music21 import *
        >>> rtm = romanText.RTMeasure('m35-36 = m29-30')
        >>> rtm.number
        [35, 36]
        >>> rtm.getCopyTarget()
        ([29, 30], ['', ''])

        >>> rtm = romanText.RTMeasure('m4 = m1')
        >>> rtm.number
        [4]
        >>> rtm.getCopyTarget()
        ([1], [''])
        '''
        # remove equal sign
        rawData = self.data.replace('=', '').strip()
        return self._getMeasureNumberData(rawData)


class RTAtom(RTToken):
    '''In roman text, within each measure are definitions of chords, phrases boundaries, open/close parenthesis, and beat indicators. These will be called Atoms, as they are data that is not tagged.

    Store a reference to the container (a RTMeasure) in each atom.
    '''
    def __init__(self, src =u'', container=None):
        '''
        >>> from music21 import *
        '''
        # this stores the source
        RTToken.__init__(self, src)
        self.container = container

    def __repr__(self):
        return '<RTAtom %r>' % self.src

    def isAtom(self):
        return True

    # for lower level distinctions, use isinstance(), as each type has its own subclass.


class RTChord(RTAtom):
    def __init__(self, src =u'', container=None):
        '''
        >>> from music21 import *
        '''
        RTAtom.__init__(self, src, container)

        # store offset within measure
        self.offset = None
        # store a quarterlength duration
        self.quarterLength = None

    def __repr__(self):
        return '<RTChord %r>' % self.src


class RTBeat(RTAtom):
    def __init__(self, src =u'', container=None):
        '''
        >>> from music21 import *
        '''
        RTAtom.__init__(self, src, container)

    def __repr__(self):
        return '<RTBeat %r>' % self.src

    def getOffset(self, timeSignature):
        '''Given a time signature, return the offset position specified by this beat.

        >>> from music21 import *
        >>> rtb = romanText.RTBeat('b1.5')
        >>> rtb.getOffset(meter.TimeSignature('3/4'))
        0.5
        >>> rtb.getOffset(meter.TimeSignature('6/8'))
        0.75
        >>> rtb.getOffset(meter.TimeSignature('2/2'))
        1.0

        >>> rtb = romanText.RTBeat('b2')
        >>> rtb.getOffset(meter.TimeSignature('3/4'))
        1.0
        >>> rtb.getOffset(meter.TimeSignature('6/8'))
        1.5

        >>> rtb = romanText.RTBeat('b1.66')
        >>> rtb.getOffset(meter.TimeSignature('6/8'))
        1.0
        >>> rtc = romanText.RTBeat('b1.66.5')
        >>> rtc.getOffset(meter.TimeSignature('6/8'))
        1.25
        

        '''
        from music21 import meter
        beatStr = self.src.replace('b', '')
        # there may be more than one decimal in the number, such as
        # 1.66.5, to show halfway through 2/3rd of a beat
        if '.' in beatStr:
            parts = beatStr.split('.')
            if len(parts) == 2:
                beat = int(parts[0]) + common.nearestCommonFraction(
                                    '.' + parts[1])
            # assume not more than 2 decimals are given
            elif len(parts) == 3:
                if parts[1] == '66' and parts[2] == '5':
                    add = .833333333333333333333
                elif parts[1] == '0' and parts[2] == '5':
                    add = .16666666666666666666
                else: 
                    raise RTTokenException('cannot handle specification: %s' %  self.src)
                beat = int(parts[0]) + add
                # TODO: need to treat the third part as a fraction of the beat division that has just been specified
                environLocal.printDebug(['discarding beat specification for beat indication: %s' % self.src])
            else:
                environLocal.printDebug(['got unexpected beat: %s' % self.src])
                raise RTTokenException('cannot handle specification: %s' %  self.src)
        else: # assume it is an integer
            beat = int(beatStr)
        #environLocal.printDebug(['using beat value:', beat])
        # TODO: check for exceptions/errors if this beat is bad
        try:
            post = timeSignature.getOffsetFromBeat(beat)
        except meter.TimeSignatureException:
            environLocal.printDebug(['bad beat specification: %s in a meter of %s' % (self.src, timeSignature)])
            post = 0.0 

        return post

class RTKeyTypeAtom(RTAtom):
    '''
    RTKeyTypeAtoms contain utility
    functions for all Key-type tokens
    i.e., RTKey, RTAnalyticKey. (no longer KeySignature)
    '''
    def __repr__(self):
        return '<RTKeyTypeAtom %r>' % self.src

    def getKey(self):
        '''
        This returns a Key, not a KeySignature object
        '''
        from music21 import key
        myKey = self.src.rstrip(self.footerStrip)
        myKey = key.convertKeyStringToMusic21KeyString(myKey)
        return key.Key(myKey)

    def getKeySignature(self):
        '''Get a KeySignature object.
        '''
        from music21 import key
        myKey = self.getKey()
        return key.KeySignature(myKey.sharps) 

class RTKey(RTKeyTypeAtom):
    footerStrip = ';:'

    def __init(self, src = u'', container=None):
        '''
        An RTKey(RTAtom) defines both a change
        in KeySignature and a change in the analyzed Key
        
        
        They are defined by ";:" after the Key.
        
              
        
        >>> from music21 import *
        >>> gminor = romanText.RTKey('g;:')
        >>> gminor
        <RTKey 'g;:'>
        >>> gminor.getKey()
        <music21.key.Key of g minor>


        >>> bminor = romanText.RTKey('bb;:')
        >>> bminor
        <RTKey 'bb;:'>
        >>> bminor.getKey()
        <music21.key.Key of b- minor>
        >>> bminor.getKeySignature()
        <music21.key.KeySignature of 5 flats>


        >>> eflatmajor = romanText.RTKey('Eb;:')
        >>> eflatmajor
        <RTKey 'Eb;:'>
        >>> eflatmajor.getKey()
        <music21.key.Key of E- major>
        '''
        RTAtom.__init__(self, src, container)

    def __repr__(self):
        return '<RTKey %r>' % self.src



class RTAnalyticKey(RTKeyTypeAtom):
    footerStrip = ':'

    def __init__(self, src =u'', container=None):
        '''
        An RTAnalyticKey(RTKeyTypeAtom) only defines
        a change in the key being analyzed.  It
        does not in itself create a :class:~'music21.key.Key'
        object
        
        >>> from music21 import *
        >>> gminor = romanText.RTAnalyticKey('g:')
        >>> gminor
        <RTAnalyticKey 'g:'>
        >>> gminor.getKey()
        <music21.key.Key of g minor>


        >>> bminor = romanText.RTAnalyticKey('bb:')
        >>> bminor
        <RTAnalyticKey 'bb:'>
        >>> bminor.getKey()
        <music21.key.Key of b- minor>

        '''
        RTAtom.__init__(self, src, container)
    
    def __repr__(self):
        return '<RTAnalyticKey %r>' % self.src


class RTKeySignature(RTAtom):
    def __init__(self, src =u'', container=None):
        '''
        An RTKeySignature(RTAtom) only defines
        a change in the KeySignature.  It
        does not in itself create a :class:~'music21.key.Key'
        object, nor does it change the analysis
        taking place.
        
        The number after KS defines the number of sharps (negative for flats)
        
        
        >>> from music21 import *
        >>> gminor = romanText.RTKeySignature('KS-2')
        >>> gminor
        <RTKeySignature 'KS-2'>
        >>> gminor.getKeySignature()
        <music21.key.KeySignature of 2 flats>
        
        >>> Amajor = romanText.RTKeySignature('KS3')
        >>> Amajor.getKeySignature()
        <music21.key.KeySignature of 3 sharps>
        
        '''
        RTAtom.__init__(self, src, container)

    def __repr__(self):
        return '<RTKeySignature %r>' % self.src

    def getKeySignature(self):
        numSharps = int(self.src[2:])
        return music21.key.KeySignature(numSharps)

class RTOpenParens(RTAtom):
    def __init__(self, src =u'(', container=None):
        '''
        >>> from music21 import *
        '''
        RTAtom.__init__(self, src, container)

    def __repr__(self):
        return '<RTOpenParens %r>' % self.src


class RTCloseParens(RTAtom):
    def __init__(self, src =u')', container=None):
        '''
        >>> from music21 import *
        '''
        RTAtom.__init__(self, src, container)

    def __repr__(self):
        return '<RTCloseParens %r>' % self.src

class RTOptionalKeyOpen(RTAtom):
    def __init__(self, src=u'', container=None):
        '''
        Marks the beginning of an optional Key area which does not
        affect the roman numeral analysis.  (For instance, it is
        possible to analyze in Bb major, while remaining in g minor)
        
        >>> from music21 import *
        >>> possibleKey = romanText.RTOptionalKeyOpen('?(Bb:')
        >>> possibleKey
        <RTOptionalKeyOpen '?(Bb:'>
        >>> possibleKey.getKey()
        <music21.key.Key of B- major>
        '''
        RTAtom.__init__(self, src, container)

    def __repr__(self):
        return '<RTOptionalKeyOpen %r>' % self.src
    
    def getKey(self):
        from music21 import key
        # alter flat symbol
        if self.src == '?(b:':
            return key.Key('b')
        else:   
            keyStr = self.src.replace('b', '-')
            keyStr = keyStr.replace(':', '')
            keyStr = keyStr.replace('?', '')
            keyStr = keyStr.replace('(', '')
            #environLocal.printDebug(['create a key from:', keyStr])
            return key.Key(keyStr)
        
class RTOptionalKeyClose(RTAtom):
    def __init__(self, src=u'', container=None):
        '''
        Marks the end of an optional Key area which does not
        affect the roman numeral analysis.  (For instance, it is
        possible to analyze in Bb major, while remaining in g minor)
        
        >>> from music21 import *
        >>> possibleKey = romanText.RTOptionalKeyClose('?)Bb:')
        >>> possibleKey
        <RTOptionalKeyClose '?)Bb:'>
        >>> possibleKey.getKey()
        <music21.key.Key of B- major>
        '''
        RTAtom.__init__(self, src, container)

    def __repr__(self):
        return '<RTOptionalKeyClose %r>' % self.src
    
    def getKey(self):
        from music21 import key
        # alter flat symbol
        if self.src == '?)b:' or self.src == '?)b':
            return key.Key('b')
        else:
            keyStr = self.src.replace('b', '-')
            keyStr = keyStr.replace(':', '')
            keyStr = keyStr.replace('?', '')
            keyStr = keyStr.replace(')', '')
            #environLocal.printDebug(['create a key from:', keyStr])
            return key.Key(keyStr)


class RTPhraseMarker(RTAtom):
    def __init__(self, src=u'', container=None):
        RTAtom.__init__(self, src, container)
        

class RTPhraseBoundary(RTPhraseMarker):
    def __init__(self, src =u'||', container=None):
        '''
        >>> from music21 import *
        >>> phrase = romanText.RTPhraseBoundary('||')
        >>> phrase
        <RTPhraseBoundary '||'>
        '''
        RTPhraseMarker.__init__(self, src, container)

    def __repr__(self):
        return '<RTPhraseBoundary %r>' % self.src

class RTEllisonStart(RTPhraseMarker):
    def __init__(self, src =u'|*', container=None):
        '''
        >>> from music21 import *
        >>> phrase = romanText.RTEllisonStart('|*')
        >>> phrase
        <RTEllisonStart '|*'>
        '''
        RTPhraseMarker.__init__(self, src, container)

    def __repr__(self):
        return '<RTEllisonStart %r>' % self.src

class RTEllisonStop(RTPhraseMarker):
    def __init__(self, src =u'|*', container=None):
        '''
        >>> from music21 import *
        >>> phrase = romanText.RTEllisonStop('*|')
        >>> phrase
        <RTEllisonStop '*|'>
        '''
        RTPhraseMarker.__init__(self, src, container)

    def __repr__(self):
        return '<RTEllisonStop %r>' % self.src



#-------------------------------------------------------------------------------
class RTHandler(object):

    # divide elements of a character stream into objects and handle
    # store in a list, and pass global information to compontns
    def __init__(self):
        # tokens are ABC objects in a linear stream
        # tokens are strongly divided between header and body, so can 
        # divide here
        self._tokens = []



    def _splitAtHeader(self, lines):
        '''Divide string into header and non-header; this is done before tokenization. 

        >>> from music21 import *
        >>> rth = romanText.RTHandler()
        >>> rth._splitAtHeader(['Title: s', 'Time Signature:', '', 'm1 g: i'])
        (['Title: s', 'Time Signature:', ''], ['m1 g: i'])

        '''
        # iterate over lines and find the first measure definition
        iStartBody = None
        for i, l in enumerate(lines):
            if reMeasureTag.match(l.strip()) is not None:
                # found a measure definition
                iStartBody = i
                break
        if iStartBody is None:
            raise RomanTextException("Cannot find the first measure definition in this file.  Dumping contextss: %s", lines)
        return lines[:iStartBody], lines[iStartBody:]
    
    def _tokenizeHeader(self, lines):
        '''In the header, we only have tagged tokens. 
        We can this process these all as the same class.
        '''
        post = []
        for l in lines:
            l = l.strip()
            if l == '': continue
            # wrap each line in a header token
            post.append(RTTagged(l))
        return post

    def _tokenizeAtoms(self, line, container=None):
        '''Given a line of data stored in measure consisting only of Atoms, tokenize and return a list. 

        >>> from music21 import *
        >>> rth = romanText.RTHandler()
        >>> str(rth._tokenizeAtoms('IV b3 ii7 b4 ii'))
        "[<RTChord 'IV'>, <RTBeat 'b3'>, <RTChord 'ii7'>, <RTBeat 'b4'>, <RTChord 'ii'>]"

        >>> str(rth._tokenizeAtoms('V7 b2 V13 b3 V7 iio6/5[no5]'))
        "[<RTChord 'V7'>, <RTBeat 'b2'>, <RTChord 'V13'>, <RTBeat 'b3'>, <RTChord 'V7'>, <RTChord 'iio6/5[no5]'>]"

        >>> tokenList = rth._tokenizeAtoms('I b2 I b2.25 V/ii b2.5 bVII b2.75 V g: IV')
        >>> str(tokenList)
        "[<RTChord 'I'>, <RTBeat 'b2'>, <RTChord 'I'>, <RTBeat 'b2.25'>, <RTChord 'V/ii'>, <RTBeat 'b2.5'>, <RTChord 'bVII'>, <RTBeat 'b2.75'>, <RTChord 'V'>, <RTAnalyticKey 'g:'>, <RTChord 'IV'>]"
        >>> tokenList[9].getKey()
        <music21.key.Key of g minor>

        >>> str(rth._tokenizeAtoms('= m3'))
        '[]'

        >>> tokenList = rth._tokenizeAtoms('g;: V b2 ?(Bb: VII7 b3 III b4 ?)Bb: i')
        >>> str(tokenList)
        "[<RTKey 'g;:'>, <RTChord 'V'>, <RTBeat 'b2'>, <RTOptionalKeyOpen '?(Bb:'>, <RTChord 'VII7'>, <RTBeat 'b3'>, <RTChord 'III'>, <RTBeat 'b4'>, <RTOptionalKeyClose '?)Bb:'>, <RTChord 'i'>]"
        '''
        post = []
        # break by spaces
        for word in line.split(' '):
            word = word.strip()
            if word == '': 
                continue
            elif word == '=':
                # if an = is found, this is a copy definition, and no atoms here
                break
            elif word == '||':
                post.append(RTPhraseBoundary(word, container))
            elif word == '(':
                post.append(RTOpenParens(word, container))
            elif word == ')':
                post.append(RTCloseParens(word, container))
            elif reBeatAtom.match(word) is not None:
                post.append(RTBeat(word, container))
            # from here, all that is left is keys or chords
            elif reOptKeyOpenAtom.match(word) is not None:
                post.append(RTOptionalKeyOpen(word, container))
            elif reOptKeyCloseAtom.match(word) is not None:
                post.append(RTOptionalKeyClose(word, container))
            elif reKeyAtom.match(word) is not None:
                post.append(RTKey(word, container))
            elif reAnalyticKeyAtom.match(word) is not None:
                post.append(RTAnalyticKey(word, container))
            elif reKeySignatureAtom.match(word) is not None:
                post.append(RTKeySignature(word, container))

            else: # only option is that it is a chord
                post.append(RTChord(word, container))
        return post

    def _tokenizeBody(self, lines):
        '''
        In the body, we may have measure, time signature, or 
        note declarations, as well as possible other tagged definitions
        '''
        post = []
        for l in lines:
            l = l.strip()
            if l == '': continue
            # first, see if it is a measure definition, if not, than assume it is tagged data
            if reMeasureTag.match(l) is not None:
                rtm = RTMeasure(l)                
                # note: could places these in-line, after post
                rtm.atoms = self._tokenizeAtoms(rtm.data, container=rtm)
                post.append(rtm)
            else:
                # store items in a measure tag outside of the measure
                post.append(RTTagged(l))
        return post


    def tokenize(self, src):
        '''
        Walk the RT string, creating RT objects along the way.
        '''
        # break into lines
        lines = src.split('\n')
        linesHeader, linesBody = self._splitAtHeader(lines)
        #environLocal.printDebug([linesHeader])        
        self._tokens += self._tokenizeHeader(linesHeader)        
        self._tokens += self._tokenizeBody(linesBody)        


    def process(self, src):
        '''Given an entire specification as a single source string, strSrc. This is usually provided in a file. 
        '''
        self._tokens = []
        self.tokenize(src)



    def definesMovements(self, countRequired=2):
        '''Return True if more than one movement is defined in a RT file.

        >>> from music21 import *
        >>> rth = romanText.RTHandler()
        >>> rth.process('Movement: 1 \\n Movement: 2 \\n \\n m1')
        >>> rth.definesMovements()
        True
        >>> rth.process('Movement: 1 \\n m1')
        >>> rth.definesMovements()
        False
        '''
        if len(self._tokens) == 0:
            raise RTHandlerException('must create tokens first')
        count = 0
        for t in self._tokens:
            if t.isMovement():
                count += 1
                if count >= countRequired:
                    return True
        return False

    def definesMovement(self):
        '''If this handler has 1 or more movement

        >>> from music21 import *
        >>> rth = romanText.RTHandler()
        >>> rth.process('Movement: 1 \\n \\n m1')
        >>> rth.definesMovements()
        False
        >>> rth.definesMovement()
        True
        '''
        return self.definesMovements(countRequired=1)

    def splitByMovement(self, duplicateHeader=True):
        '''If we have movements defined, return a list of RTHandler objects, representing header information and each movement, in order. 

        >>> from music21 import *
        >>> rth = romanText.RTHandler()
        >>> rth.process('Title: Test \\n Movement: 1 \\n m1 \\n Movement: 2 \\n m1')
        >>> post = rth.splitByMovement(False)
        >>> len(post)
        3
        >>> len(post[0])
        1
        >>> post[0].__class__
        <class 'music21.romanText.base.RTHandler'>
        >>> len(post[1]), len(post[2])
        (2, 2)

        >>> post = rth.splitByMovement(duplicateHeader=True)
        >>> len(post)
        2
        >>> len(post[0]), len(post[1])
        (3, 3)
        '''
        post = []
        sub = []
        for t in self._tokens:
            if t.isMovement():
                # when finding a movement, we are ending a previous 
                # and starting a new; this may just have metadata
                rth = RTHandler()
                rth.tokens = sub
                post.append(rth) 
                sub = []
            sub.append(t)
        if len(sub) > 0:
            rth = RTHandler()
            rth.tokens = sub
            post.append(rth)

        if duplicateHeader:
            alt = []
            # if no movement in this first handler, assume it is header info
            if not post[0].definesMovement():
                handlerHead = post[0]
                iStart = 1
            else:
                handlerHead = None
                iStart = 0
            for h in post[iStart:]:
                if handlerHead is not None:
                    h = handlerHead + h # add metadata
                alt.append(h)
            # reassign
            post = alt

        return post




    #---------------------------------------------------------------------------
    # access tokens

    def _getTokens(self):
        if self._tokens == []:
            raise RTHandlerException('must process tokens before calling split')
        return self._tokens

    def _setTokens(self, tokens):
        '''Assign tokens to this Handler
        '''
        self._tokens = tokens

    tokens = property(_getTokens, _setTokens,
        doc = '''Get or set tokens for this Handler
        ''')

    def __len__(self):
        return len(self._tokens)

    def __add__(self, other):
        '''Return a new handler adding the tokens in both

        >>> from music21 import *
        '''
        rth = self.__class__() # will get the same class type
        rth.tokens = self._tokens + other._tokens
        return rth






#-------------------------------------------------------------------------------
class RTFile(object):
    '''
    Roman Text File access
    '''
    
    def __init__(self): 
        pass

    def open(self, filename): 
        '''
        Open a file for reading, trying a variety of codecs and then
        trying them again with an ignore if it is not possible.
        '''
        self.file = None
        for encoding in ('utf-8', 'macintosh', 'latin-1', 'utf-16'):
            try:
                self.file = codecs.open(filename, encoding=encoding)
                if self.file is not None:
                    break
            except UnicodeDecodeError:
                pass
        if self.file is None:
            for encoding in ('utf-8', 'macintosh', 'latin-1', 'utf-16', None):
                try:
                    self.file = codecs.open(filename, encoding=encoding, errors='ignore')
                    if self.file is not None:
                        break
                except UnicodeDecodeError:
                    pass
            if self.file is None:
                raise RomanTextException("Cannot parse file %s, possibly a broken codec?" % filename)
                    
        self.filename = filename

    def openFileLike(self, fileLike):
        '''Assign a file-like object, such as those provided by StringIO, as an open file object.

        >>> fileLikeOpen = StringIO.StringIO()
        '''
        self.file = fileLike # already 'open'
    
    def __repr__(self): 
        r = "<RTFile>" 
        return r 
    
    def close(self): 
        self.file.close() 
    
    def read(self): 
        '''Read a file. Note that this calls readstring, which processes all tokens. 

        If `number` is given, a work number will be extracted if possible. 
        '''
        return self.readstr(self.file.read()) 
    
    def readstr(self, strSrc): 
        '''Read a string and process all Tokens. Returns a ABCHandler instance.
        '''
        handler = RTHandler()
        # return the handler instance
        handler.process(strSrc)
        return handler
    



#-------------------------------------------------------------------------------
class Test(unittest.TestCase):
    
    def runTest(self):
        pass
    

    def testBasicA(self):
        from music21.romanText import testFiles
        from music21 import romanText

        for fileStr in testFiles.ALL:
            f = romanText.RTFile()
            rth = f.readstr(fileStr) # get a handler from a string

    def testReA(self):
        # gets the index of the end of the measure indication
        g = reMeasureTag.match('m1 g: V b2 i')
        self.assertEqual(g.end(), 2)
        self.assertEqual(g.group(0), 'm1')

        self.assertEqual(reMeasureTag.match('Time Signature: 2/2'), None)

        g = reMeasureTag.match('m3-4=m1-2')
        self.assertEqual(g.end(), 4)
        self.assertEqual(g.start(), 0)
        self.assertEqual(g.group(0), 'm3-4')

        g = reMeasureTag.match('m123-432=m1120-24234')
        self.assertEqual(g.group(0), 'm123-432')

        g = reMeasureTag.match('m231a IV6 b4 C: V')
        self.assertEqual(g.group(0), 'm231a')

        g = reMeasureTag.match('m123b-432b=m1120a-24234a')
        self.assertEqual(g.group(0), 'm123b-432b')


        g = reNoteTag.match('Note: this is a note')
        self.assertEqual(g.group(0), 'Note:')
        g = reNoteTag.match('note: this is a note')
        self.assertEqual(g.group(0), 'note:')


        g = reMeasureTag.match('m231var1 IV6 b4 C: V')
        self.assertEqual(g.group(0), 'm231')

        # this only works if it starts the string
        g = reVariant.match('var1 IV6 b4 C: V')
        self.assertEqual(g.group(0), 'var1')

        g = reAnalyticKeyAtom.match('Bb:')
        self.assertEqual(g.group(0), 'Bb:')
        g = reAnalyticKeyAtom.match('F#:')
        self.assertEqual(g.group(0), 'F#:')
        g = reAnalyticKeyAtom.match('f#:')
        self.assertEqual(g.group(0), 'f#:')
        g = reAnalyticKeyAtom.match('b:')
        self.assertEqual(g.group(0), 'b:')
        g = reAnalyticKeyAtom.match('bb:')
        self.assertEqual(g.group(0), 'bb:')
        g = reAnalyticKeyAtom.match('g:')
        self.assertEqual(g.group(0), 'g:')

        # beats do not have a colon
        self.assertEqual(reKeyAtom.match('b2'), None)
        self.assertEqual(reKeyAtom.match('b2.5'), None)

        g = reBeatAtom.match('b2.5')
        self.assertEqual(g.group(0), 'b2.5')

        g = reBeatAtom.match('bVII')
        self.assertEqual(g, None)

        g = reBeatAtom.match('b1.66.5')
        self.assertEqual(g.group(0), 'b1.66.5')



    def testMeasureAttributeProcessing(self):
        rtm = RTMeasure('m17var1 vi b2 IV b2.5 viio6/4 b3.5 I')
        self.assertEqual(rtm.data, 'vi b2 IV b2.5 viio6/4 b3.5 I')
        self.assertEqual(rtm.number, [17])
        self.assertEqual(rtm.tag, 'm17')
        self.assertEqual(rtm.variantNumber, 1)


        rtm = RTMeasure('m17varC vi b2 IV b2.5 viio6/4 b3.5 I')
        self.assertEqual(rtm.data, 'vi b2 IV b2.5 viio6/4 b3.5 I')
        self.assertEqual(rtm.variantLetter, "C")


        rtm = RTMeasure('m20 vi b2 ii6/5 b3 V b3.5 V7')
        self.assertEqual(rtm.data, 'vi b2 ii6/5 b3 V b3.5 V7')
        self.assertEqual(rtm.number, [20])
        self.assertEqual(rtm.tag, 'm20')
        self.assertEqual(rtm.variantNumber, None)
        self.assertEqual(rtm.isCopyDefinition, False)

        rtm = RTMeasure('m0 b3 G: I')
        self.assertEqual(rtm.data, 'b3 G: I')
        self.assertEqual(rtm.number, [0])
        self.assertEqual(rtm.tag, 'm0')
        self.assertEqual(rtm.variantNumber, None)
        self.assertEqual(rtm.isCopyDefinition, False)

        rtm = RTMeasure('m59 = m57')
        self.assertEqual(rtm.data, '= m57')
        self.assertEqual(rtm.number, [59])
        self.assertEqual(rtm.tag, 'm59')
        self.assertEqual(rtm.variantNumber, None)
        self.assertEqual(rtm.isCopyDefinition, True)

        rtm = RTMeasure('m3-4 = m1-2')
        self.assertEqual(rtm.data, '= m1-2')
        self.assertEqual(rtm.number, [3,4])
        self.assertEqual(rtm.tag, 'm3-4')
        self.assertEqual(rtm.variantNumber, None)
        self.assertEqual(rtm.isCopyDefinition, True)



    def testTokenDefinition(self):
        # test that we are always getting the right number of tokens

        from music21.romanText import testFiles
        rth = RTHandler()
        rth.process(testFiles.mozartK279)

        count = 0
        for t in rth._tokens:
            if t.isMovement():
                count += 1
        self.assertEqual(count, 3)


        rth.process(testFiles.riemenschneider001)
        count = 0
        for t in rth._tokens:
            if t.isMeasure():
                #print t.src
                count += 1
        # 21, 2 variants, and one pickup
        self.assertEqual(count, 21+3)

        count = 0
        for t in rth._tokens:
            if t.isMeasure():
                for a in t.atoms:
                    if isinstance(a, RTAnalyticKey):
                        count += 1
        self.assertEqual(count, 1)






#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    # sys.arg test options will be used in mainTest()
    music21.mainTest(Test)

#------------------------------------------------------------------------------
# eof




