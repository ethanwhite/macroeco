#!/usr/bin/python

'''Convert .mat files of species counts in a spatial grid to a .csv file in d,x,y format.

'''


import scipy.io
import sys
import pylab

__author__ = "Chloe Lewis"
__copyright__ = "Copyright 2012, Regents of the University of California"
__credits__ = ["John Harte"]
__license__ = Null
__version__ = "0.5"
__maintainer__ = "Chloe Lewis"
__email__ = "chlewis@berkeley.edu"
__status__ = "Development"

def load_matfile(filename):
    ''' Open the .mat file as a numpy array.'''
    return scipy.io.loadmat(filename)
     


def explore_matfile(filename):
    '''Interactively decide which data in the .mat file to translate to d,x,y format.

    Will name the sub-elements of the mat file and, if requested,
    show a heat map of their layers and write tables to the .csv format
    that the rest of macroeco uses.
'''
    grid = scipy.io.loadmat(filename)
    print 'Contents:'
    for k in  grid.keys():
        try:
            print k, ', size: ', grid[k].shape
        except:
            print k, type(grid[k])

    donext = raw_input("See image of element? ")
    while donext in grid.keys():
        try:
            print 'shape: ', grid[donext].shape
            fig = pylab.figure()
            ax = fig.add_axes([0.1,0.1,.8,.8])

            if len(grid[donext].shape) == 3:
                layer = raw_input('Image which layer? ')
                im = ax.imshow(grid[donext][:,:,layer],interpolation='nearest')
            if len(grid[donext].shape) == 2:
                im = ax.imshow(grid[donext],interpolation='nearest')
            cax = fig.add_axes([.9,.1,.03,.8])
            fig.colorbar(im, cax=cax)
            pylab.show()
        except:
            print grid[k]
        donext = raw_input("See image of element? ")
    print 'Did not find that name in data structure. '
    donext = raw_input("Convert a table to dxy format? ")
    while donext in grid.keys():
        make_xy(grid[donext], donext)
        donext = raw_input("Convert a table to dxy format? ")
                
def  make_xy(data_array, subname):     
    '''Given data_array of species observations, write a csv file.

    File will have n rows
           m,x,y
    if there were n observations of species m at offset x,y.
    Missing and 0 observations get no rows.
    '''
    with open(subname.rstrip()+'_xy.csv', 'w') as xyfile:
        ymax,xmax,d = data_array.shape
        cumulative = 0
        for species in range(d): 
            for x in range(xmax):
                for y in range(ymax):
                    for count in range(data_array[y,x,species]):
                        xyfile.writelines(','.join(map(str,(species,x,y)))+'\n')
                    cumulative += data_array[y,x,species]
    print 'Wrote ', cumulative, ' rows to ', subname+'_xy.csv'
                                

def look_at_pieces(filename):  
    '''Show heatmaps of a species map divided into quadrants.

    '''
    grid = scipy.io.loadmat(filename)
    fig1 = pylab.figure()
    partialaxes = {}
    for xcorner, xbdry in [('Left',.1),('Right',.5)]:
        for ycorner, ybdry in [('upper', .5),('lower',.1)]:
            data = grid[''.join(('maps1998_',ycorner,xcorner))][:,:,0]
            print 'min, max of ',ycorner,xcorner,min(data.flatten()),max(data.flatten())
            partialaxes[ycorner+xcorner] = fig1.add_axes([xbdry, ybdry, .4, .4])
            partialaxes[ycorner+xcorner].imshow(data, vmin=0, vmax=200, interpolation='nearest')
            partialaxes[ycorner+xcorner].set_title(ycorner+xcorner)
    fig2 = pylab.figure()
    axw = fig2.add_axes([0.1, 0.1, 0.7, 0.7])
    data = grid['maps1998_wholePlot'][:,:,0]
    im = axw.imshow(data, vmin=0, vmax=200, interpolation='nearest')
    axw.set_title('Whole Plot')
    print 'min, max of  whole Plot', min(data.flatten()), max(data.flatten())
    for f in fig1, fig2:
        cax = f.add_axes([.9, .1, .03, .8])
        f.colorbar(im, cax=cax)
    pylab.show()

                       

def get_conversion_values():
    '''Placeholder to know how to translate offsets, name columns.
    '''
    return ((0,0), 1, 1, None) #TODO: get the corners in the right orientation, eg negative y-stride.

def convert_to_datum(xy, scale):
    '''Conversion to standard ?? datum: not implemented. TODO

    '''
    pass

if __name__=="__main__":
    explore_matfile(sys.argv[1])


    

