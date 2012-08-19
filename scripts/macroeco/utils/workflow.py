#!/usr/bin/python

'''
Manages the details of a reproducible workflow within macroeco. Main Workflow 
class is called with one argument, required_params, and the surrounding script 
must be called with a single sys.argv with the output directory.

Classes
-------
- `Workflow` -- tracks the analysis, data requested, and parameters; maps sites
- `Parameters` -- finds/asks for and stores run names and parameters
'''

import xml.etree.ElementTree as etree
import sys, os, logging
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import metadata as metadata

__author__ = "Chloe Lewis"
__copyright__ = "Copyright 2012, Regents of the University of California"
__credits__ = []
__license__ = None
__version__ = "0.5"
__maintainer__ = "Chloe Lewis"
__email__ = "chlewis@berkeley.edu"
__status__ = "Development"

paramfile = 'parameters.xml'  # Name of parameter file found in output dir
logfile   = 'logfile.txt'  # Name of logfile to save in output dir


class Workflow:
    '''
    Manages the details of a reproducible workflow with macroeco scripts.

    Arguments
    ---------
    required_params : dictionary
        Parameters needed for analysis, in form of 
        'parameter_name':'short_description'. All of these parameters must be 
        present in params file in output directory, or analysis will not run. 
        This argument is empty only when no data or parameters are required for 
        a script to run.
        
    Attributes
    ----------
    script_name : string
        Name of script originating the workflow
    output_path : string
        Path to output directory
    interactive : bool
        Whether the script can pause for user interaction
    runs : dict
        If parameters are needed, sets of parameter values are named runs
    '''

    def __init__(self, required_params={}):

        # Store script name from command line call
        script_path, script_extension = os.path.splitext(sys.argv[0])
        self.script_name = os.path.split(script_path)[-1]

        # Store output directory path - contains params file, log, results
        # TODO: If dir does not exist, create it? What if low level typo?
        # TODO: Make more robust to non-absolute path entries
        output_path = sys.argv[1]
        self.output_path = output_path

        # Prepare logger
        logging.basicConfig(filename=self.output_path + logfile, 
                            level=logging.INFO, format='''%(asctime)s | 
                            %(levelname)s | %(filename)s:%(lineno)d | 
                            %(message)s''', datefmt='%H:%M:%S')

        # Get parameters from file, including data paths
        assert type(required_params) == type({})

        try:
            self.parameters = Parameters(self.script_name, required_params)
            self.interactive = self.parameters.interactive
        except:  # If no params file exists
            logging.info('''No parameter file found at %s, proceeding without 
                         parameters''' % output_path)
            self.parameters = None
            self.interactive = False            
        
    def single_datasets(self):
        '''
        Generator that yields data files and descriptive parameters.

        Special parameter 'data_paths' is a list of locations of data files to 
        use for analysis - if present, map of sites will be generated for each 
        run.

        Yields
        ------
        data_path : string
            Full path to data to analyze
        output_ID : string
            Concatenates script and dataset identifiers
        run_params : dict
            Dictionary of parameters for each script_name and run
        '''

        def clean_name(fp):  # Extract file name from path
            return os.path.splitext(os.path.split(fp)[-1])[0]

        # Run script on all runs (parameter sets), and data sets
        for run_name in self.parameters.params.keys():
        # TODO: Check for output_ID conflicts (must be unique)

            # Make map of sites if data file paths given in parameters
            if 'data_paths' in self.parameters.params[run_name].keys():
                make_map(self.parameters.params['data_paths'])
            else:
                logging.debug('''No data paths given for run %s, no map of 
                              sites created''' % run_name)
                
            # Loop through each dataset and yield values for dataset and run
            for data_path in self.parameters.params[run_name]['data_paths']:
                output_ID = '_'.join([self.script_name, clean_name(data_path), 
                                      run_name])
                logging.info('Beginning %s' % output_ID)
                yield data_path, output_ID, self.parameters.params[run_name]

        
class Parameters:
    '''
    Load parameters from parameter file at output_path and make available as 
    self.params. Checks that all required_params are present and loaded.

    Arguments
    ---------
    script_name : string
        Name of script originating the workflow
    required_params : dictionary
        Parameters needed for analysis, in form of 
        'parameter_name':'short_description'. All of these parameters must be 
        present in params file in output directory for this script_name and 
        run, or analysis will not run. This argument is empty only when no data 
        or parameters are required for a script to run.

    Attributes
    ----------
    script_name : string
        Name of script originating the workflow
    interactive : bool
        Whether the script can pause for user interaction
    params : dict
        Dictionary of dictionaries, with each outer key a run name and each 
        outer value a dictionary of parameter names and values for each run.
        
    '''
    
    def __init__(self, script_name, required_params):

        # Store initial attributes
        self.script_name = script_name
        self.interactive = None
        self.params = {}

        # Read parameter file
        logging.info('Reading parameters from %s' % (output_path + paramfile))
        self.read_from_xml()

        # Check that all required parameters present in all runs
        if not self.required_params_present(required_params):
            raise IOError('Required parameters missing')
        logging.info('Parameters: %s' % str(self.params))

        # Evaluate param values into appropriate types
        self.eval_params()

         
    def read_from_xml(self):
        ''' Read parameters from xml file into self.params dictionary. '''

        # Define class for checking keys
        class AllEntities:
            def __getitem__(self, key):
                return key

        # Check that parameter file is present and can be read
        # TODO: Should this and try statements below just raise error w/o log?
        try:
            pf = open(output_path + paramfile, 'r')
            pf.close()
        except IOError:
            logging.error('Could not open parameter file %s' % (output_path + 
                                                                paramfile))
            raise

        # Declare parser object
        # TODO: Without next line, works in iPython, console, not script ??
        parser = etree.XMLParser()
        parser.parser.UseForeignDTD(True)
        parser.entity = AllEntities()

        # Try to open paramfile from output_path
        # TODO: Integration test
        try:
            pml = etree.parse(output_path + paramfile, parser=parser).getroot() 
        except etree.ParseError:
            logging.error('ParseError trying to read %s' % (output_path + 
                                                            paramfile))
        except:
            logging.error(sys.exc_info()[0])
        
        # Create params dictionary
        if len(pml) == 0:  # Error if no analyses in param file
            raise IOError('Parameter file %s contains no valid analyses' % 
                          (output_path + paramfile))

        for analysis in pml:  # Loop analyses looking for script_name
            if analysis.get('script_name') == self.script_name:

                if 'interactive' in analysis.attrib:  # Set interactive
                    ia = analysis.get('interactive')
                    if ia in ['T', 'True', 't', 'true']:
                        self.interactive = True
                    else:
                        self.interactive = False
                else:
                    self.interactive = False

                if len(analysis) == 0:  # Error if no runs in analysis
                    raise IOError('''Analysis found for this script, but no 
                                  valid runs found''')

                for run in analysis.getchildren():  # Loop runs
                    run_name = run.get('name')
                    self.params[run_name] = {}
                    for elt in run.getchildren():  # Loop params in run
                        if elt.tag == 'param':
                            param = elt.get('name')
                            value = elt.get('value')
                            self.params[run_name][param] = value

                            
    def required_params_present(self, req_params):
        ''' Check if any required parameters missing from any runs. '''

        for run_name in self.params.keys():
            run_params = self.params[run_name]
            if not set(run_params.keys()).issubset(set(req_params.keys())):
                return False
        return True


    def eval_params(self):
        '''
        Attempts to evaluate parameters to appropriate types.
        
        If eval() fails, parameter will stay a string, possibly leading to 
        cryptic errors later if there is a typo in a param value.
        '''

        for run_name in self.params.keys():
            for param_name in self.params[run_name].keys():
                try:
                    value = eval(self.params[run_name][param_name])
                    self.params[run_name][param_name] = value
                    value_type = str(type(value)).split("'")[1]
                    self.logger.debug('In run %s, parameter %s evaluated to %s' 
                                      % (run_name, param_name, value_type))
                except:
                    self.logger.debug('In run %s, parameter %s left as string' 
                    % (run_name, param_name))

            
def make_map(datalist, mapname=None, whole_globe=False):
    '''
    Makes a map of all sites in analysis.

    Parameter
    ---------
    datalist:  list of absolute paths to data files *.csv;
               data location will be extracted from corresponding *.xml

    mapname:  optional filename of the map (do not include extension)

    Returns
    -------
    True if no file with the names of all these datasets exists and one was created
    False if a file already existed
    '''
    lats = []
    lons = []
    names = []
    for f in datalist:
        x = f[:-3]+'xml'
        fname, fext = os.path.splitext(os.path.split(f)[-1])
        names.append(fname[:4])
        
    # Normalize so we can check for an existing file
    names.sort()
    if not mapname:
        mapname = 'map_' + '_'.join(names)
    mapname = mapname + '.png'
    if os.path.isfile(mapname):
        return False
    
    for f in datalist:
        x = f[:-3]+'xml'
        meta = metadata.Metadata(x)
        bounds = meta.get_coverage_region()

        lats.append(bounds[0])
        lons.append(bounds[1])

    print('Making map projection...')
    if whole_globe:
        m = Basemap(projection='cyl',
                    resolution='i')
                    
    else:
        print('Min and max coords found:\n'+str((min(lats),min(lons),max(lats),max(lons))))
        m = Basemap(projection='cyl', lat_0=50, lon_0=-100,
            llcrnrlon=min(lons)-10, llcrnrlat=min(lats)-10,
            urcrnrlon=max(lons)+10, urcrnrlat=max(lats)+10,
            resolution='l')

    print('Drawing blue-marble background...')
    m.bluemarble()
    m.drawcoastlines()
    m.drawcountries()
    #m.fillcontinents(color='beige') #Not with bluemarble
    m.drawmapboundary()

    print('Plotting research sites...')
    x, y = m(lons, lats)
    m.plot(x, y, 'yo')
    for n, xpt, ypt in zip(names,x,y):
        if n == 'BCIS': ypt += 1 #Cleanup for crowded areas 
        if n == 'SHER': ypt += 2
        plt.text(xpt+.5,ypt+.5,n,color='yellow')
    plt.title('Field sites')
    plt.savefig(mapname)
    plt.close()
    #plt.show()
    return True