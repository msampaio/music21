.. _overviewFormats:


Overview: Importing File and Data Formats
===================================================

Music21 can import and export a variety of musical data formats. Many examples of these formats are distributed with music21 as part of the corpus module (see :ref:`moduleCorpus.base`). 

The converter module, as well as the module function :func:`music21.converter.parse` handle importing all supported formats. For complete documentation on file and data formats, see :ref:`moduleConverter`.



Parsing MusicXML Files
-----------------------

We can parse a MusicXML file by providing the :func:`music21.converter.parse` function with a local file path or an URL to a file path. The function will determine the file format. An appropriate :class:`~music21.stream.Stream`  or Stream subclass will be returned. For example, given a MusicXML file stored at the file path "/Volumes/xdisc/_scratch/bwv1007-01.xml", a Stream can be created from the file with the following.

>>> from music21 import *
>>> sBach = converter.parse('/Volumes/xdisc/_scratch/bwv1007-01.xml') # doctest: +SKIP
>>> sBach.show()  # doctest: +SKIP

.. image:: images/overviewFormats-01.*
    :width: 600

Alternative, we can provide a URL to the :func:`music21.converter.parse` function that points to the desired file. Assuming proper system configuration (see :ref:`environment`), the file will be downloaded and parsed.

>>> url = 'http://kern.ccarh.org/cgi-bin/ksdata?l=cc/bach/cello&file=bwv1007-01.krn&f=xml'
>>> sAlt = converter.parse(url) 


Note that presently music21 offers limited support for compressed .mxl MusicXML files; this feature will be expanded in the future.



Getting MusicXML Files
-----------------------

Numerous MusicXML files can be found at the following URLs.

http://www.wikifonia.org

http://kern.ccarh.org

http://www.gutenberg.org





Parsing Humdrum Files
-----------------------

Parsing Humdrum files is exactly as parsing other data formats. Simply call the :func:`music21.converter.parse` function on the desired file path or URL.

>>> sLassus = converter.parse('/Volumes/xdisc/_scratch/matona.krn') # doctest: +SKIP




Getting Humdrum Files
-----------------------

Over one hundred thousand Kern files can be found at the following URL.

http://kern.humdrum.net/






Parsing ABC Files
-----------------------

Parsing ABC files is exactly as parsing other data formats. Simply call the :func:`music21.converter.parse` function on the desired file path or URL.

>>> from music21 import *
>>> o = converter.parse('/Volumes/xdisc/_scratch/oVenusBant.abc') # doctest: +SKIP

Note that many ABC files define more than one complete musical work. If an ABC file defines more than one work, an :class:`~music21.stream.Opus` object is returned. Opus objects, a Stream subclass, provide convenience methods for accessing multiple Score objects.

Reference work numbers (e.g., the "X:" metadata tag in ABC) are stored in :class:`~music21.metadata.Metadata` objects in each contained Score. Access to these numbers from the Opus is available with the :meth:`music21.stream.Opus.getNumbers` method. Additionally, the :class:`~music21.stream.Score` object can be directly obtained with the :meth:`~music21.stream.Opus.getScoreByNumber` method.

>>> from music21 import *
>>> o = corpus.parse('josquin/ovenusbant')
>>> o.getNumbers()
['1', '2', '3']
>>> s = o.getScoreByNumber(2)
>>> s.metadata.title
'O Venus bant'

Direct access to Score objects contained in an Opus by title is available with the :meth:`~music21.stream.Opus.getScoreByTitle` method.

>>> from music21 import *
>>> o = corpus.parse('essenFolksong/erk5')
>>> s = o.getScoreByTitle('Vrienden, kommt alle gaere')

In some cases an ABC file may define individual parts each as a separate score. When parsed, these parts can be combined from the Opus into a single Score with the :meth:`music21.stream.Opus.mergeScores` method. 

>>> from music21 import *
>>> o = corpus.parse('josquin/milleRegrets')
>>> s = o.mergeScores()
>>> s.metadata.title
'Mille regrets'
>>> len(s.parts)
4



Getting ABC Files
-----------------------

Large collections of ABC are available from numerous on-line repositories. The following links are just a few of the many resources available. 

http://abcnotation.com

http://www.serpentpublications.org








Parsing Musedata Files
------------------------

Both stage 1 and stage 2 Musedata file formats are supported by Music21. Multi-part Musedata (stage 2) files, zipped archives, and directories containing individual files for each part (stage 1 or stage 2) can be imported with the :func:`music21.converter.parse` function on the desired file path or URL.

>>> from music21 import *
>>> s = converter.parse('http://www.musedata.org/cgi-bin/mddata?composer=corelli&edition=chry&genre=trio/op1&work=op1n08&format=stage2&movement=01')

If a directory or zipped archive is passed to the :func:`music21.converter.parse` function, the contained files will be treated as a collection of Musedata parts.

>>> corpus.getWork('bach/bwv1080/16')  # doctest: +SKIP
'/Users/ariza/_x/src/music21/music21/corpus/bach/bwv1080/16.zip'
>>> s = corpus.parse('bach/bwv1080/16')


Getting Musedata Files
------------------------

Large collections of Musedata files are available from musedata.org, sponsored by the Center for Computer Assisted Research in the Humanities at Stanford University.

http://www.musedata.org/





Parsing MIDI Files
-----------------------

MIDI input and output is handled in the same was other formats. Simply call the :func:`music21.converter.parse` function on the desired file path or URL.
