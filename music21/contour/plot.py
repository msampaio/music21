# import unittest, doctest
# import random, math, sys, os

import music21
from music21.graph import Graph
from music21.graph import getColor

try:
    import matplotlib
    import matplotlib.pyplot as plt
except ImportError:
    pass


class GraphPlot(Graph):
    '''Graph the count of a single element.

    Data set is simply an ordered list of y elements.

    >>> import music21.contour.plot
    >>> data = [3, 4, 8, 2, 9]
    >>> g = music21.contour.plot.GraphPlot(doneAction=None)
    >>> g.setData(data)
    >>> g.process()

    .. image:: images/GraphPlot.*
        :width: 600

    '''

    def __init__(self, *args, **keywords):

        Graph.__init__(self, *args, **keywords)
        self.axisKeys = ['x', 'y']
        self._axisInit()

    def process(self):
        # figure size can be set w/ figsize=(5,10)
        self.fig = plt.figure()
        self.fig.subplots_adjust(left=0.15)

        self.setAxisLabel('y', 'C-point value')
        self.setAxisLabel('x', 'C-point position')

        ax = self.fig.add_subplot(1, 1, 1)

        x = range(len(self.data))
        y = self.data

        self.setTicks('x', [[a, str(a)] for a in x])
        self.setTicks('y', [[b, str(b)] for b in range(min(y), max(y) + 1)])

        ax.plot(x, y, 'o-', color=getColor(self.colors[0]), linewidth=1.8, label=str(self.data))
        ax.legend(prop=matplotlib.font_manager.FontProperties(size=10))

        self._adjustAxisSpines(ax)
        self._applyFormatting(ax)
        self.done()
