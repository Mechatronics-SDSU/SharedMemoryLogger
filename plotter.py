import numpy as np
from matplotlib import pyplot as plt


# ============================================================================ #
#                           # CLASS DEFINITION #                               #
# ============================================================================ #

class Plotter:

    log_f : str = None                  # String representing the name of the 
                                        # file to plot the log of.

    config_f : str = None               # String representing the .ini file 
                                        # controlling which data to be plotted

    out_f : str = None                  # String representing the name of the
                                        # dir where the output plot(s?) will 
                                        # be stored

    plot_type : str = None
                                        # String representing whether the plot
                                        # is to be used in a static or a
                                        # dynamic configuration

    def __init__(self, log_f, config_f, out_f, plot_type='s'):

        self.data = Plotter.parse_input_file(log_f)
        self.config = Plotter.parse_config_file(config_f)
        self.out_f = out_f

        if plot_type not in ['s', 'd'] : # Static, dynamic
            raise Exception('ERROR initializing Plotter - field plot_type' + 
            " not recognized!")

        self.plot_type = plot_type
        self.fig, self.ax = plt.subplots(
                (len(self.config.keys()), 1) # Get the number of plots
                )


    def parse_input_file(log_f, debug=False) :

        # Method responsible for reading the log and config files and
        # returning data in a format suited for plotting

        # Args: 
        #   log_f -     filename of the file to be read
        #   debug -     boolean indicating whether print debugging statements
        #               should be used 

        # Returns: dict(var_name, np.array((-1, 2)))
        # Contains name : data pairs, where the each row in the data is 
        # in the format of [time, value]

        # Error value indicated by returning None

        raw_data = []
        try:
            log = open(log_f)
            raw_data += log.readlines()[1:-1] # Remove the "Logger started" and 
                                          # "Logger stopped" 
            log.close()

        except Exception as E:

            # FIXME: MORE ROBUST ERROR HANDLING
            print(f"ERROR trying to open file {log_f}: \n\t{E}")
            return None 

   
        # Split the file into semantically useful "chunks" - e.g. timesteps 
        data_chunks = []
        chunk = []
        for line in raw_data:
            if debug:
                print(f'Current line: {line}')
            if 'break' in line:
                if debug:
                    print(f'Current chunk: \n{chunk}')
                data_chunks.append(chunk)
                chunk = []
            else:
                chunk.append(line)

        # Set up dict with all the var names
        cooked_data = {}
        for line in data_chunks[0]:
            var_name = [x.strip(' ') for x in line.split(':')][1]
            cooked_data[var_name] = []

        if debug:
            print(f'Var names: {[k for k, v in cooked_data.items()]}')

        
        # Parse each entry in each chunk to get the data
        for chunk in data_chunks:
            for line in chunk:

                # Split the line according to ':' delimiter, strip
                # leading and trailing whitespace
                data = [x.strip(' ') for x in line.split(':')]

                time = float(data[0])
                var_name = data[1]
                val = float(data[2])

                cooked_data[var_name].append([time, val])


        # Convert all of the list[list] into np.array
        for k, v in cooked_data.items():
            cooked_data[k] = np.array(v)

        return cooked_data

    def parse_config_file(config_f):
        # Read a config file given by config_f and return
        # a dict containing {plot_name : [var_names]}
        
        try:
            cf = open(config_f)
            lines = cf.readlines()
            cf.close()

        except Exception as E:
            print('Failed to open config file!')
            # FIXME: HANDLE GRATEFULLY
            raise E

        out = {}
        for line in lines:
            tmp = line.split(':')
            plot_name = tmp[0].strip()
            var_names = [x.strip() for x in tmp[1].split(',')]
            out[plot_name] = var_names

        return out

        

    def plot(self) : 

        # Function responsible for plotting and saving all of the data
        # read from the log file

        data = self.data

        for ax, cf in zip(self.axes, self.config.items()):
            
            plot_name, var_names = cf
            for name in var_names:
                xs = data[name][0:, 0]
                ys = data[name][0:, 1]
                ax.plot(xs, ys, label=name)

            ax.set_title(plot_name) # TODO: MODIFY CONFIG DATA STRUCTURE TO SUPPORT PROPERTIES
            ax.set_xlabel('Time (s)')

        # Plot
        plt.show()

