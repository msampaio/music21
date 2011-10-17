# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         volume.py
# Purpose:      Objects for representing volume, amplitude, and related 
#               parameters
#
# Authors:      Christopher Ariza
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''This module defines the object model of Volume, covering all representation of amplitude, volume, velocity, and related parameters.  
'''
 
import unittest

import music21
from music21 import common
from music21 import dynamics

from music21 import environment
_MOD = "volume.py"  
environLocal = environment.Environment(_MOD)



#-------------------------------------------------------------------------------
class VolumeException(music21.Music21Exception):
    pass

#-------------------------------------------------------------------------------
class Volume(object):
    '''The Volume object lives on NotRest objects and subclasses. It is not a Music21Object subclass. 

    >>> from music21 import *
    >>> v = volume.Volume()     
    '''
    def __init__(self, parent=None, velocity=None, velocityScalar=None, 
                velocityIsRelative=True):

        # store a reference to the parent, as we use this to do context 
        # will use property; if None will leave as None
        self._parent = None
        self.parent = parent    
        self._velocity = None
        if velocity is not None:
            self.velocity = velocity
        elif velocityScalar is not None:
            self.velocityScalar = velocityScalar

        self._cachedRealized = None

        #  replace with a property
        self.velocityIsRelative = velocityIsRelative

    def __deepcopy__(self, memo=None):
        '''Need to manage copying of weak ref; when copying, do not copy weak ref, but keep as a reference to the same object. 
        '''
        new = self.__class__()
        new.mergeAttributes(self) # will get all numerical values
        # keep same weak ref object
        new._parent = self._parent
        return new


    def __repr__(self):
        return "<music21.volume.Volume realized=%s>" % round(self.realized, 2)

    #---------------------------------------------------------------------------
    # properties
        
    def _getParent(self):
        if self._parent is None:
            return None
        post = common.unwrapWeakref(self._parent)
        if post is None:
            # set attribute for speed
            self._parent = None
        return post

    def _setParent(self, parent):
        if parent is not None:
            if hasattr(parent, 'classes') and 'NotRest' in parent.classes:
                self._parent = common.wrapWeakref(parent)
        else:
            self._parent = None

    parent = property(_getParent, _setParent, doc = '''
        Get or set the parent, which must be a note.NotRest subclass. The parent is wrapped in a weak reference.
        ''')


    def _getVelocity(self):
        return self._velocity
        
    def _setVelocity(self, value):
        if not common.isNum(value):
            raise VolumeException('value provided for velocity must be a number, not %s' % value)
        if value < 0:
            self._velocity = 0
        elif value > 127:
            self._velocity = 127
        else:
            self._velocity = value

    velocity = property(_getVelocity, _setVelocity, doc = '''
        Get or set the velocity value, a numerical value between 0 and 127 and available setting amplitude on each Note or Pitch in chord. 

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.volume.velocity = 20
        >>> n.volume.parent == n
        True
        >>> n.volume.velocity 
        20
        ''')


    def _getVelocityScalar(self):
        # multiplying by 1/127. for performance
        return self._velocity * 0.007874015748031496
        
    def _setVelocityScalar(self, value):
        if not common.isNum(value):
            raise VolumeException('value provided for velocityScalar must be a number, not %s' % value)
        if value < 0:
            scalar = 0
        elif value > 1:
            scalar = 1
        else:
            scalar = value
        self._velocity = int(round(scalar * 127))

    velocityScalar = property(_getVelocityScalar, _setVelocityScalar, doc = '''
        Get or set the velocityScalar value, a numerical value between 0 and 1 and available setting amplitude on each Note or Pitch in chord. This value is mapped to the range 0 to 127 on output.

        Note that this value is derived from the set velocity value. Floating point error seen here will not be found in the velocity value. 

        When setting this value, an integer-based velocity value will be derived and stored. 

        >>> from music21 import *
        >>> n = note.Note()
        >>> n.volume.velocityScalar = .5
        >>> n.volume.velocity
        64
        >>> n.volume.velocity = 127
        >>> n.volume.velocityScalar
        1.0
        ''')

    #---------------------------------------------------------------------------
    # high-level methods

    def getContextByClass(self, className, sortByCreationTime=False,         
            getElementMethod='getElementAtOrBefore'):
        '''Simulate get context by class method as found on parent NotRest object.
        '''
        p = self.parent # unwrap weak ref
        if p is None:
            raise VolumeException('cannot call getContextByClass because parent is None.')
        # call on parent object
        return p.getContextByClass(className, serialReverseSearch=True,
            callerFirst=None, sortByCreationTime=sortByCreationTime, prioritizeActiveSite=True, getElementMethod=getElementMethod, 
            memo=None)

    def getDynamicContext(self):
        '''Return the dynamic context of this Volume, based on the position of the NotRest parent of this object.
        '''
        # TODO: find wedges and crescendi too
        return self.getContextByClass('Dynamic')

    def mergeAttributes(self, other):
        '''Given another Volume object, gather all attributes except parent. Values are always copied, not passed by reference. 

        >>> from music21 import *
        >>> n1 = note.Note()
        >>> v1 = volume.Volume()
        >>> v1.velocity = 111
        >>> v1.parent = n1

        >>> v2 = volume.Volume()
        >>> v2.mergeAttributes(v1)
        >>> v2.parent == None
        True
        >>> v2.velocity
        111
        '''
        if other is not None:      
            self._velocity = other._velocity
            self.velocityIsRelative = other.velocityIsRelative
        

    def getRealized(self, useDynamicContext=True, useVelocity=True,
        useArticulations=True, baseLevel=0.5, clip=True):
        '''Get a realized unit-interval scalar for this Volume. This scalar is to be applied to the dynamic range of whatever output is available, whatever that may be. 

        The `baseLevel` value is a middle value between 0 and 1 that all scalars modify. This also becomes the default value for unspecified dynamics. When scalars (between 0 and 1) are used, their values are doubled, such that mid-values (around .5, which become 1) make no change. 
 
        This can optionally take into account `dynamicContext`, `useVelocity`, and `useArticulation`.

        If `useDynamicContext` is True, a context search for a dynamic will be done, else dynamics are ignored. Alternatively, the useDynamicContext may supply a Dyanmic object that will be used instead of a context search.

        The `velocityIsRelative` tag determines if the velocity value includes contextual values, such as dynamics and and accents, or not. 

        >>> from music21 import stream, volume, note
        >>> s = stream.Stream()
        >>> s.repeatAppend(note.Note('d3', quarterLength=.5), 8)
        >>> s.insert([0, dynamics.Dynamic('p'), 1, dynamics.Dynamic('mp'), 2, dynamics.Dynamic('mf'), 3, dynamics.Dynamic('f')])

        >>> s.notes[0].volume.getRealized()
        0.42519...
        >>> s.notes[1].volume.getRealized()
        0.42519...
        >>> s.notes[2].volume.getRealized()
        0.63779...
        >>> s.notes[7].volume.getRealized()
        0.99212...

        >>> # velocity, if set, will be scaled by dyanmics
        >>> s.notes[7].volume.velocity = 20
        >>> s.notes[7].volume.getRealized()
        0.22047...

        >>> # unless we set the velocity to not be relative
        >>> s.notes[7].volume.velocityIsRelative = False
        >>> s.notes[7].volume.getRealized()
        0.1574803...
        '''
        #velocityIsRelative might be best set at import. e.g., from MIDI, 
        # velocityIsRelative is False, but in other applications, it may not 
        # be

        val = baseLevel
        dm = None  # no dynamic mark
 
        # velocity is checked first; the range between 0 and 1 is doubled, 
        # to 0 to 2. a velocityScalar of .7 thus scales the base value of 
        # .5 by 1.4 to become .7
        if useVelocity:
            if self._velocity is not None:
                if not self.velocityIsRelative:
                    # if velocity is not relateive 
                    # it should fully determines output independent of anything
                    # else
                    val = self.velocityScalar
                else:
                    val = val * (self.velocityScalar * 2.0)
            # this value provides a good default velocity, as .5 is low
            # this not a scalar application but a shift.
            else: # target :0.70866
                val += 0.20866

        # only change the val from here if velocity is relative 
        if self.velocityIsRelative:                    
            if useDynamicContext is not False:
                if hasattr(useDynamicContext, 
                    'classes') and 'Dynamic' in useDynamicContext.classes:
                    dm = useDynamicContext # it is a dynamic
                elif self.parent is not None:
                    dm = self.getDynamicContext() # dm may be None
                else:
                    environLocal.pd(['getRealized():', 
                    'useDynamicContext is True but no dynamic supplied or found in context'])
                if dm is not None:
                    # double scalare (so range is between 0 and 1) and scale 
                    # t he current val (around the base)
                    val = val * (dm.volumeScalar * 2.0)
            # userArticulations can be a list of 1 or more articulation objects
            # as well as True/False
            if useArticulations is not None:
                pass
            
        if clip: # limit between 0 and 1
            if val > 1:
                val = 1.0
            elif val < 0:
                val = 0.0
        # might to rebalance range after scalings       

        # always update cached result each time this is called
        self._cachedRealized = val
        return val

    def getRealizedStr(self, useDynamicContext=True, useVelocity=True,
        useArticulations=True, baseLevel=0.5, clip=True):
        '''Return the realized as rounded and formatted string value. Useful for testing. 

        >>> from music21 import *
        >>> v = volume.Volume(velocity=64)
        >>> v.getRealizedStr()
        '0.5'
        '''  
        val = self.getRealized(useDynamicContext=useDynamicContext, 
                    useVelocity=useVelocity, useArticulations=useArticulations, 
                    baseLevel=baseLevel, clip=clip)
        return str(round(val, 2))


    realized = property(getRealized, doc='''
        Return the realized unit-interval scalar for this Volume

        >>> from music21 import *
        >>> 
        ''')

    
    def _getCachedRealized(self):
        if self._cachedRealized is None:
            self._cachedRealized = self.getRealized()
        return self._cachedRealized

    cachedRealized = property(_getCachedRealized, doc='''
        Return the cached realized value of this volume. This will be the last realized value or, if that value has not been set, a newly realized value. If the caller knows that the realized values have all been recently set, using this property will add significant performance boost.

        >>> from music21 import *
        >>> v = volume.Volume(velocity=128)
        >>> v.cachedRealized
        1.0
        ''')

    def _getCachedRealizedStr(self):
        return str(round(self._getCachedRealized(), 2))

    cachedRealizedStr = property(_getCachedRealizedStr, doc='''
        Convenience property for testing.

        >>> from music21 import *
        >>> v = volume.Volume(velocity=128)
        >>> v.cachedRealizedStr
        '1.0'
        ''')

#-------------------------------------------------------------------------------
# utility stream processing methods


def realizeVolume(srcStream, setAbsoluteVelocity=False,         
            useDynamicContext=True, useVelocity=True, useArticulations=True):
    '''Given a Stream with one level of dynamics (e.g., a Part, or two Staffs that share Dyanmics), destructively modify it to set all realized volume levels. These values will be stored in the Volume object as `cachedRealized` values. 

    This is a top-down routine, as opposed to bottom-up values available with context searches on Volume. This thus offers a performance benefit. 

    This is always done in place; for the option of non-in place processing, see Stream.realizeVolume().

    If setAbsoluteVelocity is True, the realized values will overwrite all existing velocity values, and the Volume objects velocityIsRelative parameters will be set to False.

    
    '''
    # get dynamic map
    flatSrc = srcStream.flat # assuming sorted

    # check for any dyanmics
    dyanmicsAvailable = False
    if len(flatSrc.getElementsByClass('Dynamic')) > 0:
        dyanmicsAvailable = True
    else: # no dynamics available
        if useDynamicContext is True: # only if True, and non avail, override
            useDynamicContext = False

    if dyanmicsAvailable:
        # extend durations of all dyanmics
        # doing this in place as this is a destructive opperation
        boundaries = flatSrc.extendDurationAndGetBoundaries('Dynamic', inPlace=True)
        bKeys = boundaries.keys()
        bKeys.sort() # sort

    # assuming stream is sorted
    # storing last releven index lets us always start form the last-used
    # key, avoiding searching through entire list every time
    lastRelevantKeyIndex = 0
    for e in flatSrc: # iterate over all elements
        if hasattr(e, 'volume') and 'NotRest' in e.classes:
            # try to find a dynamic
            eStart = e.getOffsetBySite(flatSrc)
    
            # get the most recent dynamic
            if dyanmicsAvailable and useDynamicContext is True:
                dm = False # set to not search dynamic context
                for k in range(lastRelevantKeyIndex, len(bKeys)):
                    start, end = bKeys[k]
                    if eStart >= start and eStart < end:
                        # store so as to start in the same position
                        # for next element
                        lastRelevantKeyIndex = k
                        dm = boundaries[bKeys[k]]
                        break
            else: # permit supplying a single dynamic context for all materia
                dm = useDynamicContext
            # this returns a value, but all we need to do is to set the 
            # cached values stored internally
            val = e.volume.getRealized(useDynamicContext=dm, useVelocity=True, 
                  useArticulations=True)
            if setAbsoluteVelocity:
                e.volume.velocityIsRelative = False
                # set to velocity scalar
                e.volume.velocityScalar = val


        
#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testBasic(self):
        from music21 import volume, note

        n1 = note.Note()
        v = volume.Volume(parent=n1)
        self.assertEqual(v.parent, n1)
        del n1
        # weak ref does not exist
        self.assertEqual(v.parent, None)


    def testGetContextSearchA(self):
        from music21 import stream, note, volume, dynamics
        
        s = stream.Stream()
        d1 = dynamics.Dynamic('mf')
        s.insert(0, d1)
        d2 = dynamics.Dynamic('f')
        s.insert(2, d2)

        n1 = note.Note('g')
        v1 = volume.Volume(parent=n1)
        s.insert(4, n1)

        # can get dyanmics from volume object
        self.assertEqual(v1.getContextByClass('Dynamic'), d2)
        self.assertEqual(v1.getDynamicContext(), d2)


    def testGetContextSearchB(self):
        from music21 import stream, note, volume, dynamics
        
        s = stream.Stream()
        d1 = dynamics.Dynamic('mf')
        s.insert(0, d1)
        d2 = dynamics.Dynamic('f')
        s.insert(2, d2)

        n1 = note.Note('g')
        s.insert(4, n1)

        # can get dyanmics from volume object
        self.assertEqual(n1.volume.getDynamicContext(), d2)


    def testDeepCopyA(self):
        import copy
        from music21 import volume, note    
        n1 = note.Note()

        v1 = volume.Volume()
        v1.velocity = 111
        v1.parent = n1
        
        v1Copy = copy.deepcopy(v1)
        self.assertEqual(v1.velocity, 111)
        self.assertEqual(v1Copy.velocity, 111)

        self.assertEqual(v1.parent, n1)
        self.assertEqual(v1Copy.parent, n1)


    def testGetRealizedA(self):
        from music21 import volume, dynamics

        v1 = volume.Volume(velocity=64)
        self.assertEqual(v1.getRealizedStr(), '0.5')

        d1 = dynamics.Dynamic('p')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.3')

        d1 = dynamics.Dynamic('ppp')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.1')


        d1 = dynamics.Dynamic('fff')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.91')


        # if vel is at max, can scale down with a dyanmic
        v1 = volume.Volume(velocity=127)
        d1 = dynamics.Dynamic('fff')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '1.0')

        d1 = dynamics.Dynamic('ppp')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.2')
        d1 = dynamics.Dynamic('mp')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.9')
        d1 = dynamics.Dynamic('p')
        self.assertEqual(v1.getRealizedStr(useDynamicContext=d1), '0.6')


    def testRealizeVolumeA(self):
        from music21 import stream, dynamics, note, volume

        s = stream.Stream()
        s.repeatAppend(note.Note('g3'), 16)

        # before insertion of dyanmics
        match = [n.volume.cachedRealizedStr for n in s.notes]
        self.assertEqual(match, ['0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71'])

        for i, d in enumerate(['pp', 'p', 'mp', 'f', 'mf', 'ff', 'ppp', 'mf']):
            s.insert(i*2, dynamics.Dynamic(d))

        # cached will be out of date in regard to new dynamics
        match = [n.volume.cachedRealizedStr for n in s.notes]
        self.assertEqual(match, ['0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71', '0.71'])

        # calling realize will set all to new cached values
        volume.realizeVolume(s)
        match = [n.volume.cachedRealizedStr for n in s.notes]
        self.assertEqual(match, ['0.21', '0.21', '0.43', '0.43', '0.64', '0.64', '0.99', '0.99', '0.78', '0.78', '1.0', '1.0', '0.14', '0.14', '0.78', '0.78'])

        # we can get the same results without using realizeVolume, though
        # this uses slower context searches
        s = stream.Stream()
        s.repeatAppend(note.Note('g3'), 16)

        for i, d in enumerate(['pp', 'p', 'mp', 'f', 'mf', 'ff', 'ppp', 'mf']):
            s.insert(i*2, dynamics.Dynamic(d))
        match = [n.volume.cachedRealizedStr for n in s.notes]
        self.assertEqual(match, ['0.21', '0.21', '0.43', '0.43', '0.64', '0.64', '0.99', '0.99', '0.78', '0.78', '1.0', '1.0', '0.14', '0.14', '0.78', '0.78'])

        # loooking at raw velocity values
        match = [n.volume.velocity for n in s.notes]
        self.assertEqual(match, [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None])

        # can set velocity with realized values
        volume.realizeVolume(s, setAbsoluteVelocity=True)
        match = [n.volume.velocity for n in s.notes]
        self.assertEqual(match, [27, 27, 54, 54, 81, 81, 126, 126, 99, 99, 127, 127, 18, 18, 99, 99])

        #s.show('midi')


#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = []


if __name__ == "__main__":
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof




