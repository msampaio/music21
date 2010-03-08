#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:         base.py
# Purpose:      Music21 base classes and important utilities
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    (c) 2009-2010 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''
Music21 base classes and important utilities.

base -- the convention within music21 is that __init__ files contain:

   from base import *
   
so everything in this file can be accessed as music21.XXXX

'''


import copy
import unittest, doctest
import sys
import types
import time
import inspect

from music21 import common
from music21 import environment
_MOD = 'music21.base.py'
environLocal = environment.Environment(_MOD)


#-------------------------------------------------------------------------------
VERSION = (0, 2, 4)  # increment any time picked versions will be obsolete.
VERSION_STR = '.'.join([str(x) for x in VERSION]) + 'a1'
WEAKREF_ACTIVE = True

#-------------------------------------------------------------------------------
class Music21Exception(Exception):
    pass

class RelationsException(Exception):
    pass

class Music21ObjectException(Exception):
    pass

class ElementException(Exception):
    pass

class GroupException(Exception):
    pass

#-------------------------------------------------------------------------------
# make subclass of set once that is defined properly
class Groups(list):   
    '''A list of strings used to identify associations that an element might 
    have. Enforces that all elements must be strings
    
    >>> g = Groups()
    >>> g.append("hello")
    >>> g[0]
    'hello'
    
    >>> g.append(5)
    Traceback (most recent call last):
    GroupException: Only strings can be used as list names
    '''
    def append(self, value):
        if isinstance(value, basestring):
            list.append(self, value)
        else:
            raise GroupException("Only strings can be used as list names")
            

    def __setitem__(self, i, y):
        if isinstance(y, basestring):
            list.__setitem__(self, i, y)
        else:
            raise GroupException("Only strings can be used as list names")
        

    def __eq__(self, other):
        '''Test Group equality. In normal lists, order matters; here it does not. 

        >>> a = Groups()
        >>> a.append('red')
        >>> a.append('green')
        >>> b = Groups()
        >>> b.append('green')
        >>> b.append('red')
        >>> a == b
        True
        '''
        if not isinstance(other, Groups):
            return False
        if (list.sort(self) == other.sort()):
            return True
        else:
            return False

    def __ne__(self, other):
        '''In normal lists, order matters; here it does not. 
        '''

        if other is None or not isinstance(other, Groups):
            return True
        if (list.sort(self) == other.sort()):
            return False
        else:
            return True





#-------------------------------------------------------------------------------
class DefinedContexts(object):
    '''An object, stored within a Music21Object, that provides a collection of objects that may be contextually relevant.

    Some of these objects are locations; these DefinedContext additional store an offset value, used for determining position within a Stream. 

    DefinedContexts are one of many ways that context can be found; context can also be found through searching (using objects in DefinedContexts). 

    '''
    #TODO: make locations, by default, use weak refs
    # make contexts, by default, not use weak refs

    def __init__(self):
        # a dictionary of dictionaries
        self._definedContexts = {} 
        # store idKeys in lists for easy access
        # the same key may be both in locationKeys and contextKeys
        self._locationKeys = []

    def __len__(self):
        '''Return the total number of references.

        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> len(aContexts) 
        1
        '''
        return len(self._definedContexts)

    def __deepcopy__(self, memo=None):
        '''This produces a new, independent DefinedContexts object.
        This does not, however, deepcopy site references stored therein

        >>> import copy
        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> bContexts = copy.deepcopy(aContexts)
        >>> len(aContexts.get()) == 1
        True
        >>> len(bContexts.get()) == 1
        True
        >>> aContexts.get() == bContexts.get()
        True
        '''
        new = self.__class__()
        for idKey in self._definedContexts.keys():
            dict = self._definedContexts[idKey]
            new.add(dict['obj'], dict['offset'], dict['name'], 
                    dict['time'], idKey)
        return new


    def clear(self):
        '''Clear all data.
        '''
        self._definedContexts = {} 
        self._locationKeys = []

    def _prepareObject(self, obj, domain):
        '''Prepare an object for storage
        '''
        # can have this perform differently based on domain
        if WEAKREF_ACTIVE:
            if obj is None: # leave None alone
                objRef = obj
            else:
                objRef = common.wrapWeakref(obj)
        else: # a references
            objRef = site
        return objRef

    def add(self, obj, offset=None, name=None, timeValue=None, idKey=None):
        '''Add a reference
        if offset is None, it is interpreted as a context
        if offset is a value, it is intereted as location

        NOTE: offset follows obj here, unlike with add() in old DefinedContexts
        '''
        if offset == None: domain = 'contexts'
        else: domain = 'locations'

        # note: if we want both context and locations to exists
        # for the same object, may need to append character code to id
        if idKey == None and obj != None:
            idKey = id(obj)
        # a None object will have a key of None
        elif idKey == None and obj == None:
            idKey = None

        #environLocal.printDebug(['adding obj', obj, idKey])
        objRef = self._prepareObject(obj, domain)
        add = False
        update = False
        if idKey not in self._definedContexts.keys():
            add = True
        else:
            update = True

        if domain == 'locations': # the dictionary may already be a context
            if add: # already know that it is new
                self._locationKeys.append(idKey)
            elif idKey not in self._locationKeys: # check 
                self._locationKeys.append(idKey)

        dict = {}
        dict['obj'] = objRef
        # offset can be None for contexts
        dict['offset'] = offset
        if name == None:
            dict['name'] = type(obj).__name__
        else:
            dict['name'] = name
        if timeValue == None:
            dict['time'] = time.time()
        else:
            dict['time'] = timeValue

        if add:
            self._definedContexts[idKey] = dict
        if update: # add new/missing information to dictionary
            self._definedContexts[idKey].update(dict)

    def remove(self, site):
        '''Remove the entry specified by sites

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aSite, 23)
        >>> len(aContexts)
        1
        >>> aContexts.add(bSite, 233)
        >>> len(aContexts)
        2
        >>> aContexts.add(cSite, 232223)
        >>> len(aContexts)
        3
        >>> aContexts.remove(aSite)
        >>> len(aContexts)
        2

        OMIT_FROM_DOCS
        >>> len(aContexts._locationKeys)
        2

        '''
        siteId = None
        if site is not None: 
            siteId = id(site)
        try:
            del self._definedContexts[siteId]
        except:    
            raise RelationsException('an entry for this object (%s) is not stored in DefinedContexts' % site)
        
        if siteId in self._locationKeys:
            self._locationKeys.pop(self._locationKeys.index(siteId))


    def removeById(self, idKey):
        del self._definedContexts[idKey]
        if idKey in self._locationKeys:
            self._locationKeys.pop(self._locationKeys.index(idKey))


    def get(self, locationsTrail=False):
        '''Get references; unwrap from weakrefs; place in order from 
        most recently added to least recently added

        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> cObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(cObj, 345)
        >>> aContexts.add(aObj)
        >>> aContexts.add(bObj)
        >>> aContexts.get() == [cObj, aObj, bObj]
        True
        >>> aContexts.get(locationsTrail=True) == [aObj, bObj, cObj]
        True
        '''
        post = []
        if locationsTrail:
            keys = []
            for key in self._definedContexts.keys():
                if key not in self._locationKeys: # skip these
                    keys.append(key) # others first
            keys += self._locationKeys # now locations are at end
        else:
            keys = self._definedContexts.keys()
            
        for key in keys:
            dict = self._definedContexts[key]
            # need to check if these is weakref
            if common.isWeakref(dict['obj']):
                post.append(common.unwrapWeakref(dict['obj']))
            else:
                post.append(dict['obj'])
        return post

    #---------------------------------------------------------------------------
    # for dealing with locations
    def getSites(self):
        '''Get parents for locations; unwrap from weakrefs

        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj, 234)
        >>> aContexts.add(bObj, 3000)
        >>> len(aContexts._locationKeys) == 2
        True
        >>> len(aContexts.getSites()) == 2
        True
        '''
        # use pre-collected keys
        post = []
        for idKey in self._locationKeys:
            try:
                s1 = self._definedContexts[idKey]['obj']
            except KeyError:
                raise RelationsException('no such site: %s' % idKey)
            if s1 is None or WEAKREF_ACTIVE == False: # leave None alone
                post.append(s1)
            else:
                post.append(common.unwrapWeakref(s1))
        return post
    
    def hasSiteId(self, site):
        '''Return True or False if this DefinedContexts object already has this site defined as a location
        '''
        if site in self._locationKeys:
            return True
        else:
            return False


    def getOffsets(self):
        '''Return a list of all offsets.

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> dSite = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 0)
        >>> aLocations.add(cSite) # a context
        >>> aLocations.add(bSite, 234) # can add at same offset or another
        >>> aLocations.add(dSite) # a context
        >>> aLocations.getOffsets()
        [0, 234]
        '''
        # here, already having location keys may be an advantage
        return [self._definedContexts[x]['offset'] for x in self._locationKeys] 

    def getOffsetBySite(self, site):
        '''For a given site return its offset.

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cParent = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 23)
        >>> aLocations.add(bSite, 121.5)
        >>> aLocations.getOffsetBySite(aSite)
        23
        >>> aLocations.getOffsetBySite(bSite)
        121.5
        '''
        siteId = None
        if site is not None:
            siteId = id(site)
        post = self._definedContexts[siteId]['offset']
        if post == None: # 
            raise RelationsException('an entry for this object (%s) is not stored in DefinedContexts' % siteId)
        return self._definedContexts[siteId]['offset']


    def getOffsetBySiteId(self, siteId):
        '''For a given site id, return its offset.

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cParent = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 23)
        >>> aLocations.add(bSite, 121.5)
        >>> aLocations.getOffsetBySiteId(id(aSite))
        23
        >>> aLocations.getOffsetBySiteId(id(bSite))
        121.5
        '''
        post = self._definedContexts[siteId]['offset']
        if post == None: # 
            raise RelationsException('an entry for this object (%s) is not stored in DefinedContexts' % siteId)
        return self._definedContexts[siteId]['offset']
    def setOffsetBySite(self, site, value):
        '''
        Changes the offset of the site specified.  Note that this can also be
        done with add, but the difference is that if the site is not in 
        DefinedContexts, it will raise an exception.
        
        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 23)
        >>> aLocations.add(bSite, 121.5)
        >>> aLocations.setOffsetBySite(aSite, 20)
        >>> aLocations.getOffsetBySite(aSite)
        20
        >>> aLocations.setOffsetBySite(cSite, 30)        
        Traceback (most recent call last):
        RelationsException: ...
        '''
        siteId = None
        if site is not None:
            siteId = id(site)
        # will raise an index error if the siteId does not exist
        try:
            self._definedContexts[siteId]['offset'] = value
        except KeyError:
            raise RelationsException('an entry for this object (%s) is not stored in DefinedContexts' % site)
            

#         if siteId in self._definedContexts.keys(): 
#             #environLocal.printDebug(['site already defined in this DefinedContexts object', site])
#             # order is the same as in coordinates
#             
#         else:

    def getSiteByOffset(self, offset):
        '''For a given offset return the parent

        # More than one parent may have the same offset; 
        # this can return the last site added by sorting time

        No - now we use a dict, so there's no guarantee that the one you want will be there -- need orderedDicts!

        >>> class Mock(Music21Object): pass
        >>> aSite = Mock()
        >>> bSite = Mock()
        >>> cSite = Mock()
        >>> aLocations = DefinedContexts()
        >>> aLocations.add(aSite, 23)
        >>> aLocations.add(bSite, 23121.5)
        >>> aSite == aLocations.getSiteByOffset(23)
        True
        '''
        match = None
        for siteId in self._definedContexts.keys():
            # might need to use almost equals here
            if self._definedContexts[siteId]['offset'] == offset:
                match = self._definedContexts[siteId]['obj']
                break
        if WEAKREF_ACTIVE:
            if match is None:
                return match
            if not common.isWeakref(match):
                raise RelationsException('site on coordinates is not a weak ref: %s' % match)
            return common.unwrapWeakref(match)
        else:
            return match


    #---------------------------------------------------------------------------
    # for dealing with contexts or getting other information

    def getByClass(self, className, callerFirst=None, memo=None):
        '''Return the most recently added reference based on className. Class name can be a string or the real class name.

        This will recursively search the defined contexts of existing defined context.

        Caller here can be the object that is hosting this DefinedContexts
        object (such as a Stream). This is necessary when, later on, we need
        a flat representation. If no caller is provided, the a reference to
        this DefinedContexts instances is based (from where locations can be 
        looked up if necessary).

        callerFirst is simply used to pass a reference of the first caller; this
        is necessary if we are looking within a Stream for a flat offset position.

        >>> class Mock(Music21Object): pass
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> aContexts.add(bObj)
        >>> aContexts.getByClass('mock') == aObj
        True
        >>> aContexts.getByClass(Mock) == aObj
        True

        OMIT_FROM_DOCS
        TODO: not sure if memo is properly working: need a test case
        '''
        # in general, this should not be the first caller, as this method
        # is called from a Music21Object, not directly on the DefinedContexts
        # isntance. Nontheless, if this is the first caller, it is the first
        # caller. 
        if callerFirst == None: # this is the first caller
            callerFirst = self
        if memo == None:
            memo = {} # intialize

        environLocal.printDebug(['call getByClass from:', self, 
                                 'callerFirst:', callerFirst])
        #environLocal.printDebug(['call getByClass from', self])
        post = None

        # search any defined contexts first
        # TODO: get here should return non-locations first
        for obj in self.get(locationsTrail=True):
            #environLocal.printDebug(['memo', memo])
            if obj is None: continue # in case the reference is dead
            if common.isStr(className):
                if type(obj).__name__.lower() == className.lower():
                    post = obj       
                    break
            elif isinstance(obj, className):
                    post = obj       
                    break
            # if after trying to match name, look in the defined contexts' 
            # defined contexts [sic!]
            # note that this does not complete searching at the first level
            # before recursing: might want to change this
            if post == None: # no match yet
                # access public method to recurse
                if id(obj) not in memo.keys():
                    if hasattr(obj, 'getContextByClass'):
                        post = obj.getContextByClass(className,
                               callerFirst=callerFirst, memo=memo)
                        # after searching, store this obj in memo
                        memo[id(obj)] = obj
                        if post != None:
                            break
                    else: # this is not a music21 object
                        environLocal.printDebug['cannot call getContextByClass on obj stored in DefinedContext:', obj]
                else: # objec has already been searched
                    environLocal.printDebug['skipping searching of object already searched:', obj]
            else: 
                return None
        return post

    def getAttrByName(self, attrName):
        '''Given an attribute name, search all objects and find the first
        that matches this attribute name; then return a reference to this attribute.

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> aObj.attr1 = 234
        >>> bObj = Mock()
        >>> bObj.attr1 = 98
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> len(aContexts)
        1
        >>> aContexts.getAttrByName('attr1') == 234
        True
        >>> aContexts.removeById(id(aObj))
        >>> aContexts.add(bObj)
        >>> aContexts.getAttrByName('attr1') == 98
        True
        '''
        post = None
        for obj in self.get():
            if obj is None: 
                continue # in case the reference is dead
            try:
                post = getattr(obj, attrName)
                return post
            except AttributeError:
                pass

    def setAttrByName(self, attrName, value):
        '''Given an attribute name, search all objects and find the first
        that matches this attribute name; then return a reference to this attribute.

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> bObj = Mock()
        >>> bObj.attr1 = 98
        >>> aContexts = DefinedContexts()
        >>> aContexts.add(aObj)
        >>> aContexts.add(bObj)
        >>> aContexts.setAttrByName('attr1', 'test')
        >>> aContexts.getAttrByName('attr1') == 'test'
        True
        '''
        post = None
        for obj in self.get():
            if obj is None: continue # in case the reference is dead
            try:
                junk = getattr(obj, attrName) # if attr already exists
                setattr(obj, attrName, value) # if attr already exists
            except AttributeError:
                pass

#     def find(self, classList, recursive=True, hasAttr=None):
#         pass





#-------------------------------------------------------------------------------
class Music21Object(object):
    '''
    Base class for all music21 objects.
    
    All music21 objects encode 7 pieces of information:
    
    (1) id        : unique identification string (optional)
    (2) groups    : a Groups object: which is a list of strings identifying 
                    internal subcollections
                    (voices, parts, selections) to which this element belongs
    (3) duration  : Duration object representing the length of the object
    (4) locations : a DefinedContexts object (see above) that specifies connections of
                    this object to one location in another object
    (5) parent    : a reference or weakreference to a currently active Location
    (6) offset    : a float or duration specifying the position of the object in parent 
    (7) contexts  : a list of references or weakrefs for current contexts 
                    of the object (similar to locations but without an offset)
    (8) priority  : int representing the position of an object among all
                    objects at the same offset.


    Each of these may be passed in as a named keyword to any music21 object.
    Some of these may be intercepted by the subclassing object (e.g., duration within Note)
    '''

    _duration = None
    _definedContexts = None
    id = None
    _priority = 0
    _overriddenLily = None
    # None is stored as the internal location of an obj w/o a parent
    _currentParent = None
    _currentParentId = None # cached id in case the weakref has gone away...

    # define order to present names in documentation; use strings:
    # deepcopy does not like actual method names
    _DOC_ORDER = ['searchParent', 'getContextAttr', 'setContextAttr']
    _DOC_ATTR = {'id': 'Unique identification string.',
                 'groups': 'An instance of a Group object.'
                     }

    def __init__(self, *arguments, **keywords):

        # an offset keyword arg should set the offset in location
        # not in a local parameter
#         if "offset" in keywords and not self.offset:
#             self.offset = keywords["offset"]

        if "id" in keywords and not self.id:
            self.id = keywords["id"]            
        else:
            self.id = id(self)
        
        if "duration" in keywords and self.duration is None:
            self.duration = keywords["duration"]
        
        if "groups" in keywords and keywords["groups"] is not None and \
            (not hasattr(self, "groups") or self.groups is None):
            self.groups = keywords["groups"]
        elif not hasattr(self, "groups"):
            self.groups = Groups()
        elif self.groups is None:
            self.groups = Groups()

        # TODO: propery key word should be definedContexts
        if "locations" in keywords and self._definedContexts is None:
            self._definedContexts = keywords["locations"]
        else:
            self._definedContexts = DefinedContexts()
            # set up a default location for self at zero
            # use None as the name of the site
            self._definedContexts.add(None, 0.0)

        if "parent" in keywords and self.parent is None:
            self.parent = keywords["parent"]
        
#         if ("definedContexts" in keywords and 
#             keywords["definedContexts"] is not None and 
#             self._definedContexts is None):
#             self._definedContexts = keywords["definedContexts"]
#         elif self._definedContexts is None:
#             self._definedContexts = []
    


    def __deepcopy__(self, memo=None):
        '''
        Helper method to copy.py's deepcopy function.  Call it from there

        memo=None is the default as specified in copy.py

        Problem: if an attribute is defined with an understscore (_priority) but
        is also made available through a property (e.g. priority)  using dir(self) 
        results in the copy happening twice. Thus, __dict__.keys() is used.

        >>> from copy import deepcopy
        >>> from music21 import note, duration
        >>> n = note.Note('A')
        >>> n.offset = 1.0 #duration.Duration("quarter")
        >>> n.groups.append("flute")
        >>> n.groups
        ['flute']

        >>> b = deepcopy(n)
        >>> b.offset = 2.0 #duration.Duration("half")
        
        >>> n is b
        False
        >>> n.accidental = "-"
        >>> b.name
        'A'
        >>> n.offset
        1.0
        >>> b.offset
        2.0
        >>> n.groups[0] = "bassoon"
        >>> ("flute" in n.groups, "flute" in b.groups)
        (False, True)
        '''
        # call class to get a new, empty instance
        new = self.__class__()
        #for name in dir(self):
        for name in self.__dict__.keys():

            if name.startswith('__'):
                continue
           
            part = getattr(self, name)
            
            # attributes that require special handling
            if name == '_currentParent':
                #environLocal.printDebug(['creating parent reference'])
                newValue = self.parent # keep a reference, not a deepcopy
                setattr(new, name, newValue)
            # this is an error check, particularly for object that inherit
            # this object and place a Stream as an attribute
            elif hasattr(part, '_elements'):
                environLocal.printDebug(['found stream in dict keys', self,
                    part, name])
                raise Music21Exception('streams as attributes requires special handling when deepcopying')
            else: # use copy.deepcopy, will call __deepcopy__ if available
                newValue = copy.deepcopy(part, memo)
                #setattr() will call the set method of a named property.
                setattr(new, name, newValue)
                
        return new

    def __setattr__(self, a, b):
        c = 5 + 10.0
        object.__setattr__(self, a, b)


    def isClass(self, className):
        '''
        returns bool depending on if the object is a particular class or not
        
        here, it just returns isinstance, but for Elements it will return true
        if the embedded object is of the given class.  Thus, best to use it throughout
        music21 and only use isinstance if you really want to see if something is
        an ElementWrapper or not.
        '''
        if isinstance(self, className):
            return True
        else:
            return False

    
    #---------------------------------------------------------------------------
    # look at this object for an atttribute; if not here
    # look up to parents

    def searchParent(self, attrName):
        '''If this element is contained within a Stream or other Music21 element, 
        searchParent() permits searching attributes of higher-level
        objects. The first encountered match is returned, or None if no match.
        '''
        found = None
        try:
            found = getattr(self.parent, attrName)
        except AttributeError:
            # not sure of passing here is the best action
            environLocal.printDebug(['searchParent call raised attribute error for attribute:', attrName])
            pass
        if found is None:
            found = self.parent.searchParent(attrName)
        return found
        

    def getOffsetBySite(self, site):
        '''If this class has been registered in a container such as a Stream, 
        that container can be provided here, and the offset in that object
        can be returned. 

        Note that this is different than the getOffsetByElement() method on 
        Stream in that this can never access the flat representation of a Stream.

        >>> a = Music21Object()
        >>> a.offset = 30
        >>> a.getOffsetBySite(None)
        30.0
        '''
#         if site == self:
#             site = None # shortcut
        return self._definedContexts.getOffsetBySite(site)

    def getContextAttr(self, attr):
        '''Given the name of an attribute, search Conctexts and return 
        the best match.

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> aObj.attr1 = 'test'
        >>> a = Music21Object()
        >>> a.addContext(aObj)
        >>> a.getContextAttr('attr1')
        'test'
        '''
        return self._definedContexts.getAttrByName(attr)

    def setContextAttr(self, attrName, value):
        '''Given the name of an attribute, search Conctexts and return 
        the best match.

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> aObj.attr1 = 'test'
        >>> a = Music21Object()
        >>> a.addContext(aObj)
        >>> a.getContextAttr('attr1')
        'test'
        >>> a.setContextAttr('attr1', 3000)
        >>> a.getContextAttr('attr1')
        3000
        '''
        return self._definedContexts.setAttrByName(attrName, value)

    def addContext(self, obj):
        '''Add an ojbect as a context reference, placed with the object's DefinedContexts object.

        >>> class Mock(Music21Object): attr1=234
        >>> aObj = Mock()
        >>> aObj.attr1 = 'test'
        >>> a = Music21Object()
        >>> a.addContext(aObj)
        >>> a.getContextAttr('attr1')
        'test'
        '''
        return self._definedContexts.add(obj)


    def getContextByClass(self, className, serialReverseSearch=True,
                          callerFirst=None, memo=None):
        '''Search both DefinedContexts as well as associated objects to find a matching class.

        The a reference to the caller is required to find the offset of the 
        object of the caller. This is needed for serialReverseSearch.

        The caller may be a DefinedContexts reference from a lower-level object.
        If so, we can access the location of that lower-level object. However, 
        if we need a flat representation, the caller needs to be the source 
        Stream, not its DefinedContexts reference.

        The callerFirst is the first object from which this method was called. This is needed in order to determine the final offset from which to search. 
        '''
        environLocal.printDebug(['call getContextByClass from:', self, 'parent:', self.parent, 'callerFirst:', callerFirst])
    
        # this method will be called recursively on all object levels, ascending
        # thus, to do serial reverse search we need to 
        # look at parent flat and track back to first encountered class match

        if callerFirst == None: # this is the first caller
            callerFirst = self
        if memo == None:
            memo = {} # intialize

        post = None
        # first, if this obj is a Stream, we see if the class exists at or
        # before where the offsetOfCaller
        if serialReverseSearch:
            # if this is a Stream and we have a caller
            # callerFirst must also be not None; this is assured if caller      
            # is not None
            if hasattr(self, "elements") and callerFirst != None: 
                # find the offset of the callerFirst
                # if this is a Stream, we need to find the offset relative
                # to this Stream; it may only be available within a flat
                # representaiton

                #note: cannt use self.flat.getOffsetBySite() here 
                # alternative method:
                #offsetOfCaller = callerFirst.getOffsetBySite(self.flat)
                # most error tolerant: returns None
                offsetOfCaller = self.flat.getOffsetByElement(callerFirst)

                # in some cases it migth be necessary and/or faster 
                # to search the 
                # offsetOfCaller = caller.flat.getOffsetBySite(self)
                # offsetOfCaller = caller.getOffsetBySite(self)

                if offsetOfCaller != None:
                    post = self.flat.getElementAtOrBefore(offsetOfCaller, 
                               [className])

                environLocal.printDebug(['results of serialReverseSearch:', post, 'searching for:', className, 'starting from offset', offsetOfCaller])

        if post == None: # still no match
            # this will call this method on all defined contexts;
            # if this is a stream, this will be the next level up, recursing
            # a reference to the callerFirst is continuall passed
            post = self._definedContexts.getByClass(className,
                                   callerFirst=callerFirst, memo=memo)
        return post


    #---------------------------------------------------------------------------
    # properties

    def _getParent(self):
        # can be None
        if WEAKREF_ACTIVE:
            if self._currentParent is None: #leave None
                return self._currentParent
            else:
                return common.unwrapWeakref(self._currentParent)
        else:
            return self._currentParent
    
    def _setParent(self, site):
        siteId = None
        if site is not None: 
            siteId = id(site)
        if site is not None and not self._definedContexts.hasSiteId(siteId):
#             siteId not in self._definedContexts.coordinates:
            self._definedContexts.add(site, self.offset, idKey=siteId) 
        
        if WEAKREF_ACTIVE:
            if site is None: # leave None alone
                self._currentParent = None
                self._currentParentId = None
            else:
                self._currentParent = common.wrapWeakref(site)
                self._currentParentId = siteId
        else:
            self._currentParent = site
            self._currentParentId = siteId


    parent = property(_getParent, _setParent, 
        doc='''A reference to the most-recent object used to contain this object. In most cases, this will be a Stream or Stream sub-class. In most cases, an object's parent attribute is automatically set when an the object is attached to a Stream. 
        ''')

    def addLocationAndParent(self, offset, parent, parentWeakRef = None):
        '''
        ADVANCED: a speedup tool that adds a new location element and a new parent.  Called
        by Stream.insert -- this saves some dual processing.  Does not do safety checks that
        the siteId doesn't already exist etc., because that is done earlier.
        
        This speeds up things like stream.getElementsById substantially.

        Testing script (N.B. manipulates Stream._elements directly -- so not to be emulated)
        >>> from stream import Stream
        >>> st1 = Stream()
        >>> o1 = Music21Object()
        >>> st1_wr = common.wrapWeakref(st1)
        >>> offset = 20.0
        >>> st1._elements = [o1]
        >>> o1.addLocationAndParent(offset, st1, st1_wr)
        >>> o1.parent is st1
        True
        >>> o1.getOffsetBySite(st1)
        20.0
        '''
        parentId = id(parent)
        self._definedContexts.add(parent, offset, idKey=parentId) 
        
        if WEAKREF_ACTIVE:
                if parentWeakRef is None:
                    parentWeakRef = common.wrapWeakref(parent)
                self._currentParent = parentWeakRef
                self._currentParentId = parentId
        else:
            self._currentParent = parent
            self._currentParentId = parentId
        

    def _getOffset(self):
        '''

        '''
        #there is a problem if a new parent is being set and no offsets have 
        # been provided for that parent; when self.offset is called, 
        # the first case here would match

        parentId = None
        if self.parent is not None:
            parentId = id(self.parent)
        elif self._currentParentId is not None:
            parentId = self._currentParentId
        
        if parentId is not None and self._definedContexts.hasSiteId(parentId):
        # if parentId is not None and parentId in self._definedContexts.coordinates:
            return self._definedContexts.getOffsetBySiteId(parentId)
            #return self._definedContexts.coordinates[parentId]['offset']
        elif self.parent is None: # assume we want self
            return self._definedContexts.getOffsetBySite(None)
        else:
            raise Exception('request for offset cannot be made with parent of %s (id: %s)' % (self.parent, parentId))            

    def _setOffset(self, value):
        if common.isNum(value):
            # if a number assume it is a quarter length
            # self._offset = duration.DurationUnit()
            # MSC: We can change this when we decide that we want to return
            #      something other than quarterLength

            offset = float(value)
        elif hasattr(value, "quarterLength"):
            # probably a Duration object, but could be something else -- in any case, we'll take it.
            offset = value.quarterLength
        else:
            raise Exception('We cannot set  %s as an offset' % value)
 
        self._definedContexts.setOffsetBySite(self.parent, offset)
#        if self.parent is None:
            # a None parent gets the offset at self
#            self._definedContexts.setOffsetBySite(None, offset)
            #self.disconnectedOffset = offset
#        else:
#            self._definedContexts.setOffsetBySite(self.parent, offset)
    
    offset = property(_getOffset, _setOffset, 
        doc = '''The offset property sets the position of this object from the start of its container (a Stream or Stream sub-class) in quarter lengths.
        ''')


    def _getDuration(self):
        '''
        Gets the DurationObject of the object or None

        '''
        return self._duration

    def _setDuration(self, durationObj):
        '''
        Set the offset as a quarterNote length
        '''
        if hasattr(durationObj, "quarterLength"):
            # we cannot directly test to see isInstance(duration.DurationCommon) because of
            # circular imports; so we instead just take any object with a quarterLength as a
            # duration
            self._duration = durationObj
        else:
            # need to permit Duration object assignment here
            raise Exception('this must be a Duration object, not %s' % durationObj)

    duration = property(_getDuration, _setDuration, 
        doc = '''Get and set the duration of this object as a Duration object.
        ''')

    def _getPriority(self):
        return self._priority

    def _setPriority(self, value):
        '''
        value is an int.
        '''
        if not isinstance(value, int):
            raise ElementException('priority values must be integers.')
        self._priority = value

    priority = property(_getPriority, _setPriority,
        doc = '''Get and set the priority integer value. 

        Priority specifies the order of processing from left (lowest number) to right (highest number) of objects at the same offset.  For instance, if you want a key change and a clef change to happen at the same time but the key change to appear first, then set: keySigElement.priority = 1; clefElement.priority = 2 this might be a slightly counterintuitive numbering of priority, but it does mean, for instance, if you had two elements at the same offset, an allegro tempo change and an andante tempo change, then the tempo change with the higher priority number would apply to the following notes (by being processed second).

        Default priority is 0; thus negative priorities are encouraged to have Elements that appear non-priority set elements.

        In case of tie, there are defined class sort orders defined in music21.stream.CLASS_SORT_ORDER.  For instance, a key signature change appears before a time signature change before a note at the same offset.  This produces the familiar order of materials at the start of a musical score.
        
        >>> a = Music21Object()
        >>> a.priority = 3
        >>> a.priority = 'high'
        Traceback (most recent call last):
        ElementException: priority values must be integers.
        ''')


    #---------------------------------------------------------------------------
    def write(self, fmt='musicxml', fp=None):
        '''Write a file.
        
        A None file path will result in temporary file
        '''
        format, ext = common.findFormat(fmt)
        if format is None:
            raise Music21ObjectException('bad format (%s) provided to write()' % fmt)
        elif format == 'text':
            if fp is None:
                fp = environLocal.getTempFile(ext)
            dataStr = self._reprText()
        elif format == 'musicxml':
            if fp is None:
                fp = environLocal.getTempFile(ext)
            dataStr = self.musicxml
        else:
            raise Music21ObjectException('cannot support writing in this format, %s yet' % format)
        f = open(fp, 'w')
        f.write(dataStr)
        f.close()
        return fp


    def _reprText(self):
        '''Retrun a text representation. This methods can be overridden by
        subclasses to provide alternative text representations.
        '''
        return self.__repr__()


    def show(self, fmt='musicxml'):
        '''
        Displays an object in the given format (default: musicxml) using the default display
        tools.
        
        This might need to return the file path.
        '''
        format, ext = common.findFormat(fmt)
        if format == 'text':
            print(self._reprText())
        else: # a format that writes a file
            environLocal.launch(format, self.write(format))



#-------------------------------------------------------------------------------
class ElementWrapper(Music21Object):
    '''
    An element wraps an object so that the same object can
    be positioned within a stream.
    
    The object is always available as element.obj -- however, calls to
    the ElementWrapper will call 
    
    Object is now mandatory -- calls to ElementWrapper without an object fail,
    because in the new (11/29) object model, ElementWrapper should only be used
    to wrap an object.
    
    '''
    obj = None
    _id = None

    def __init__(self, obj):
        Music21Object.__init__(self)
        self.obj = obj # object stored here        
        self._unlinkedDuration = None

    def isClass(self, className):
        '''
        Returns true if the object embedded is a particular class.

        Used by getElementsByClass in Stream

        >>> import note
        >>> a = ElementWrapper(None)
        >>> a.isClass(note.Note)
        False
        >>> a.isClass(types.NoneType)
        True
        >>> b = ElementWrapper(note.Note('A4'))
        >>> b.isClass(note.Note)
        True
        >>> b.isClass(types.NoneType)
        False
        '''
        if isinstance(self.obj, className):
            return True
        else:
            return False

    def __copy__(self):
        '''
        Makes a copy of this element with a reference
        to the SAME object but with unlinked offset, priority
        and a cloned Groups object

        >>> import note
        >>> import duration
        >>> n = note.Note('A')
        
        >>> a = ElementWrapper(obj = n)
        >>> a.offset = duration.Duration("quarter")
        >>> a.groups.append("flute")

        >>> b = copy.copy(a)
        >>> b.offset = duration.Duration("half")
        
        '''
#         >>> a.obj.accidental = "-"
#         >>> b.name
#         'A-'
#         >>> a.obj is b.obj
#         True

#         >>> a.offset.quarterLength
#         1.0
#         >>> a.groups[0] = "bassoon"
#         >>> ("flute" in a.groups, "flute" in b.groups)
#         (False, True)

        new = self.__class__(self.obj)
        #for name in dir(self):
        for name in self.__dict__.keys():
            if name.startswith('__'):
                continue
            part = getattr(self, name)
            newValue = part # just provide a reference
            setattr(new, name, newValue)

        # it is assumed that we need new objects for groups, contexts
        # and locations in order to position / group this object
        # independently
        new.groups = copy.deepcopy(self.groups)
        new._definedContexts = copy.deepcopy(self._definedContexts)
        new._definedContexts = copy.deepcopy(self._definedContexts)
        return new

    def __deepcopy__(self, memo=None):
        '''
        similar to copy but also does a deepcopy of
        the object as well.
        
        (name is all lowercase to go with copy.deepcopy convention)

        >>> import copy    
        >>> from music21 import note, duration
        >>> n = note.Note('A')
        
        >>> a = ElementWrapper(obj = n)
        >>> a.offset = 1.0 # duration.Duration("quarter")
        >>> a.groups.append("flute")

        >>> b = copy.deepcopy(a)
        >>> b.offset = 2.0 # duration.Duration("half")
        
        >>> a.obj is b.obj
        False
        >>> a.obj.accidental = "-"
        >>> b.obj.name
        'A'
        >>> a.offset
        1.0
        >>> b.offset
        2.0
        >>> a.groups[0] = "bassoon"
        >>> ("flute" in a.groups, "flute" in b.groups)
        (False, True)
        '''
        new = self.__copy__()
        # this object needs a new locations object
        new._definedContexts = copy.deepcopy(self._definedContexts)
        new.obj = copy.deepcopy(self.obj)
        return new

    #---------------------------------------------------------------------------
    # properties

    def getId(self):
        if self.obj is not None:
            if hasattr(self.obj, "id"):
                return self.obj.id
            else:
                return self._id
        else:
            return self._id

    def setId(self, newId):
        if self.obj is not None:
            if hasattr(self.obj, "id"):
                self.obj.id = newId
            else:
                self._id = newId
        else:
            self._id = newId

    id = property (getId, setId)


    def _getDuration(self):
        '''
        Gets the duration of the ElementWrapper (if separately set), but
        normal returns the duration of the component object if available, otherwise
        returns None.

        >>> import note
        >>> n = note.Note('F#')
        >>> n.quarterLength = 2.0
        >>> n.duration.quarterLength 
        2.0
        >>> el1 = ElementWrapper(n)
        >>> el1.duration.quarterLength
        2.0

        ADVANCED FEATURE TO SET DURATION OF ELEMENTS AND STREAMS SEPARATELY
        >>> class KindaStupid(object):
        ...     pass
        >>> ks1 = ElementWrapper(KindaStupid())
        >>> ks1.obj.duration
        Traceback (most recent call last):
        AttributeError: 'KindaStupid' object has no attribute 'duration'
        
        >>> import duration
        >>> ks1.duration = duration.Duration("whole")
        >>> ks1.duration.quarterLength
        4.0
        >>> ks1.obj.duration  # still not defined
        Traceback (most recent call last):
        AttributeError: 'KindaStupid' object has no attribute 'duration'
        '''
        if self._unlinkedDuration is not None:
            return self._unlinkedDuration
        elif hasattr(self, "obj") and hasattr(self.obj, 'duration'):
            return self.obj.duration
        else:
            return None

    def _setDuration(self, durationObj):
        '''
        Set the offset as a quarterNote length
        '''
        if not hasattr(durationObj, "quarterLength"):
            raise Exception('this must be a Duration object, not %s' % durationObj)
        
        if hasattr(self.obj, 'duration'):
            # if a number assume it is a quarter length
            self.obj.duration = durationObj
        else:
            self._unlinkedDuration = durationObj
            
    duration = property(_getDuration, _setDuration)

    offset = property(Music21Object._getOffset, Music21Object._setOffset)

    #---------------------------------------------------------------------------
    def __repr__(self):
        shortObj = (str(self.obj))[0:30]
        if len(str(self.obj)) > 30:
            shortObj += "..."
            
        if self.id is not None:
            return '<%s id=%s offset=%s obj="%s">' % \
                (self.__class__.__name__, self.id, self.offset, shortObj)
        else:
            return '<%s offset=%s obj="%s">' % \
                (self.__class__.__name__, self.offset, shortObj)


    def __eq__(self, other):
        '''Test ElementWrapper equality

        >>> import note
        >>> n = note.Note("C#")
        >>> a = ElementWrapper(n)
        >>> a.offset = 3.0
        >>> b = ElementWrapper(n)
        >>> b.offset = 3.0
        >>> a == b
        True
        >>> a is not b
        True
        >>> c = ElementWrapper(n)
        >>> c.offset = 2.0
        >>> c.offset
        2.0
        >>> a == c
        False
        '''
        if not hasattr(other, "obj") or \
           not hasattr(other, "offset") or \
           not hasattr(other, "priority") or \
           not hasattr(other, "id") or \
           not hasattr(other, "groups") or \
           not hasattr(other, "parent") or \
           not hasattr(other, "duration"):
            return False


        if (self.obj == other.obj and \
            self.offset == other.offset and \
            self.priority == other.priority and \
            self.id == other.id and \
            self.groups == other.groups and \
            self.parent == other.parent and \
            self.duration == self.duration):
            return True
        else:
            return False

    def __ne__(self, other):
        '''
        '''
        return not self.__eq__(other)


    def __setattr__(self, name, value):
        #environLocal.printDebug(['calling __setattr__ of ElementWrapper', name, value])

        if name in self.__dict__:  # if in the ElementWrapper already, set that first
            object.__setattr__(self, name, value)
        
        # if not, change the attribute in the stored object
        storedobj = object.__getattribute__(self, "obj")
        if name not in ['offset', '_offset', '_currentParent'] and \
            storedobj is not None and hasattr(storedobj, name):
            setattr(storedobj, name, value)
        # unless neither has the attribute, in which case add it to the ElementWrapper
        else:  
            object.__setattr__(self, name, value)

    def __getattr__(self, name):
        '''This method is only called when __getattribute__() fails.
        Using this also avoids the potential recursion problems of subclassing
        __getattribute__()_
        
        see: http://stackoverflow.com/questions/371753/python-using-getattribute-method for examples
         
        '''
        storedobj = Music21Object.__getattribute__(self, "obj")
        if storedobj is None:
            raise AttributeError("Could not get attribute '" + name + "' in an object-less element")
        else:
            return object.__getattribute__(storedobj, name)



    def isTwin(self, other):
        '''
        a weaker form of equality.  a.isTwin(b) is true if
        a and b store either the same object OR objects that are equal
        and a.groups == b.groups 
        and a.id == b.id (or both are none) and duration are equal.
        but does not require position, priority, or parent to be the same
        In other words, is essentially the same object in a different context
             
        >>> import note
        >>> aE = ElementWrapper(obj = note.Note("A-"))
        >>> aE.id = "aflat-Note"
        >>> aE.groups.append("out-of-range")
        >>> aE.offset = 4.0
        >>> aE.priority = 4
        
        >>> bE = copy.copy(aE)
        >>> aE is bE
        False
        >>> aE == bE
        True
        >>> aE.isTwin(bE)
        True

        >>> bE.offset = 14.0
        >>> bE.priority = -4
        >>> aE == bE
        False
        >>> aE.isTwin(bE)
        True
        '''
        if not hasattr(other, "obj") or \
           not hasattr(other, "id") or \
           not hasattr(other, "duration") or \
           not hasattr(other, "groups"):
            return False

        if (self.obj == other.obj and \
            self.id == other.id and \
            self.duration == self.duration and \
            self.groups == other.groups):
            return True
        else:
            return False





#-------------------------------------------------------------------------------
class TestMock(Music21Object):
    def __init__(self):
        Music21Object.__init__(self)

class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copyinng all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)


    def testObjectCreation(self):
        a = TestMock()
        a.groups.append("hello")
        a.id = "hi"
        a.offset = 2.0
        assert(a.offset == 2.0)

    def testElementEquality(self):
        from music21 import note
        n = note.Note("F-")
        a = ElementWrapper(n)
        a.offset = 3.0
        c = ElementWrapper(n)
        c.offset = 3.0
        assert (a == c)
        assert (a is not c)
        b = ElementWrapper(n)
        b.offset = 2.0
        assert (a != b)

    def testNoteCreation(self):
        from music21 import note, duration
        n = note.Note('A')
        n.offset = 1.0 #duration.Duration("quarter")
        n.groups.append("flute")

        b = copy.deepcopy(n)
        b.offset = 2.0 # duration.Duration("half")
        
        self.assertFalse(n is b)
        n.accidental = "-"
        self.assertEqual(b.name, "A")
        self.assertEqual(n.offset, 1.0)
        self.assertEqual(b.offset, 2.0)
        n.groups[0] = "bassoon"
        self.assertFalse("flute" in n.groups)
        self.assertTrue("flute" in b.groups)

    def testOffsets(self):
        from music21 import note
        a = ElementWrapper(note.Note('A#'))
        a.offset = 23.0
        self.assertEqual(a.offset, 23.0)

    def testObjectsAndElements(self):
        from music21 import note, stream
        note1 = note.Note("B-")
        note1.type = "whole"
        stream1 = stream.Stream()
        stream1.append(note1)
        subStream = stream1.getNotes()

    def testLocationsRefs(self):
        aMock = TestMock()
        bMock = TestMock()

        loc = DefinedContexts()
        loc.add(aMock, 234)
        loc.add(bMock, 12)
        
#        self.assertEqual(loc.getOffsetByIndex(-1), 12)
        self.assertEqual(loc.getOffsetBySite(aMock), 234)
        self.assertEqual(loc.getSiteByOffset(234), aMock)
#        self.assertEqual(loc.getSiteByIndex(-1), bMock)

        #del aMock
        # if the parent has been deleted, the None will be returned
        # even though there is still an entry
        #self.assertEqual(loc.getSiteByIndex(0), None)


    def testLocationsNone(self):
        '''Test assigning a None to parent
        '''
        loc = DefinedContexts()
        loc.add(None, 0)



    def testM21BaseDeepcopy(self):
        '''Test copying
        '''
        a = Music21Object()
        a.id = 'test'
        b = copy.deepcopy(a)
        self.assertNotEqual(a, b)
        self.assertEqual(b.id, 'test')

    def testM21BaseLocations(self):
        '''Basic testing of M21 base object
        '''
        a = Music21Object()
        b = Music21Object()

        # storing a single offset does not add a DefinedContexts entry  
        a.offset = 30
        # all offsets are store in locations
        self.assertEqual(len(a._definedContexts), 1)
        self.assertEqual(a.getOffsetBySite(None), 30.0)
        self.assertEqual(a.offset, 30.0)

        # assigning a parent directly
        a.parent = b
        # now we have two offsets in locations
        self.assertEqual(len(a._definedContexts), 2)

        a.offset = 40
        # still have parent
        self.assertEqual(a.parent, b)
        # now the offst returns the value for the current parent 
        self.assertEqual(a.offset, 40.0)

        # assigning a parent to None
        a.parent = None
        # properly returns original offset
        self.assertEqual(a.offset, 30.0)
        # we still have two locations stored
        self.assertEqual(len(a._definedContexts), 2)
        self.assertEqual(a.getOffsetBySite(b), 40.0)


    def testM21BaseLocationsCopy(self):
        '''Basic testing of M21 base object
        '''
        a = Music21Object()
        a.id = "a obj"
        b = Music21Object()
        b.id = "b obj"

        post = []
        for x in range(30):
            b.id = 'test'
            b.parent = a
            c = copy.deepcopy(b)
            c.id = "c obj"
            post.append(c)

        # have two locations: None, and that set by assigning parent
        self.assertEqual(len(b._definedContexts), 2)
        g = post[-1]._definedContexts
        self.assertEqual(len(post[-1]._definedContexts), 2)

        # this now works
        self.assertEqual(post[-1].parent, a)


        a = Music21Object()

        post = []
        for x in range(30):
            b = Music21Object()
            b.id = 'test'
            b.parent = a
            b.offset = 30
            c = copy.deepcopy(b)
            c.parent = b
            post.append(c)

        self.assertEqual(len(post[-1]._definedContexts), 3)

        # this works because the parent is being set on the object
        self.assertEqual(post[-1].parent, b)
        # the copied parent has been deepcopied, and cannot now be accessed
        # this fails! post[-1].getOffsetBySite(a)



    def testDefinedContexts(self):
        from music21 import base, note, stream, corpus, clef

        m = stream.Measure()
        m.measureNumber = 34
        n = note.Note()
        m.append(n)
        
        n.pitch.addContext(m)
        n.pitch.addContext(n) 
        self.assertEqual(n.pitch.getContextAttr('measureNumber'), 34)
        n.pitch.setContextAttr('lyric',  
                               n.pitch.getContextAttr('measureNumber'))
        self.assertEqual(n.lyric, 34)


        violin1 = corpus.parseWork("beethoven/opus18no1", 
                                3, 'xml').getElementById("Violin I")
        lastNote = violin1.flat.notes[-1]
        lastNoteClef = lastNote.getContextByClass(clef.Clef)
        self.assertEqual(isinstance(lastNoteClef, clef.TrebleClef), True)



    def testDefinedContextsSearch(self):
        from music21 import note, stream, clef

        n1 = note.Note('A')
        n2 = note.Note('B')
        c1 = clef.TrebleClef()
        c2 = clef.BassClef()
        
        s1 = stream.Stream()
        s1.insert(10, n1)
        s1.insert(100, n2)
        
        s2 = stream.Stream()
        s2.insert(0, c1)
        s2.insert(100, c2)
        s2.insert(10, s1) # placing s1 here should result in c2 being before n2
        
        self.assertEqual(s1.getOffsetBySite(s2), 10)
        # make sure in the context of s1 things are as we expect
        self.assertEqual(s2.flat.getElementAtOrBefore(0), c1)
        self.assertEqual(s2.flat.getElementAtOrBefore(100), c2)
        self.assertEqual(s2.flat.getElementAtOrBefore(20), n1)
        self.assertEqual(s2.flat.getElementAtOrBefore(110), n2)
        
        # note: we cannot do this
        #self.assertEqual(s2.flat.getOffsetBySite(n2), 110)
        # we can do this:
        self.assertEqual(n2.getOffsetBySite(s2.flat), 110)
        
        # this seems more idiomatic
        self.assertEqual(s2.flat.getOffsetByElement(n2), 110)
        
        # both notes can find the treble clef in the parent stream
        post = n1.getContextByClass(clef.TrebleClef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)
        
        post = n2.getContextByClass(clef.TrebleClef)
        self.assertEqual(isinstance(post, clef.TrebleClef), True)
        
        # n1 cannot find a bass clef
        post = n1.getContextByClass(clef.BassClef)
        self.assertEqual(post, None)
        
        # n2 can find a bass clef, due to its shifted position in s2
        post = n2.getContextByClass(clef.BassClef)
        self.assertEqual(isinstance(post, clef.BassClef), True)


    def testDefinedContextsPitch(self):
        # TODO: this form does not yet work
        from music21 import base, note, stream, clef
        m = stream.Measure()
        m.measureNumber = 34
        n = note.Note()
        m.append(n)
        
        #pitchMeasure = n.pitch.getContextAttr('measureNumber')
        #n.pitch.setContextAttr('lyric', pitchMeasure)
        #self.assertEqual(n.lyric, 34)




#-------------------------------------------------------------------------------
# define presented order in documentation
DOC_ORDER = [Music21Object, ElementWrapper, DefinedContexts]


def mainTest(*testClasses):
    '''
    Takes as its arguments modules (or a string 'noDocTest')
    and runs all of these modules through a unittest suite
    
    unless 'noDocTest' is passed as a module, a docTest
    is also performed on __main__.  Hence the name "mainTest"
    
    run example (put at end of your modules)
    
        import unittest
        class Test(unittest.TestCase):
            def testHello(self):
                hello = "Hello"
                self.assertEqual("Hello", hello)
    
        import music21
        if __name__ == '__main__':
            music21.mainTest(Test)
    
    '''
    
    if ('noDocTest' in testClasses):
        s1 = unittest.TestSuite()
    else: 
        s1 = doctest.DocTestSuite('__main__', optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE))

    if ('verbose') in testClasses:
        verbosity = 2
    else:
        verbosity = 1

    for thisClass in testClasses:
        if isinstance(thisClass, str):
            pass
        else:
            s2 = unittest.defaultTestLoader.loadTestsFromTestCase(thisClass)
            s1.addTests(s2) 
    runner = unittest.TextTestRunner()
    runner.verbosity = verbosity
    runner.run(s1)  

if __name__ == "__main__":
    mainTest(Test)