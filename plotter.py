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
        self.config = Plotter.parse_config_file(config_f, self.data)
        self.num_plots = len(self.config.keys())
        self.out_f = out_f

        if plot_type not in ['s', 'd'] : # Static, dynamic
            raise Exception('ERROR initializing Plotter - field plot_type' + 
            " not recognized!")

        self.plot_type = plot_type
        self.fig, self.axes = plt.subplots(
                self.num_plots, 1 # Get the number of plots
                )
    
        # This is actually pretty stupid, it's here to fix the
        # fact that the axes are in the form of an iterable UNLESS
        # there's only one Axes object created (e.g. plotting only one graph)
        if self.num_plots == 1:
            self.axes = [self.axes]


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
            
            # Check if you're at the end of a timestep
            if 'break' in line:
                if debug:
                    print(f'Current chunk: \n{chunk}\n')
                data_chunks.append(chunk)
                chunk = []
            else:

                # Split each line based on the ":" symbol
                # If the last entry (data) has more than 1 character, split that
                # into multiple values in a list; otherwise, just wrap it in a list

                line = [x.strip(' \n') for x in line.split(':')]
                line[2] = [x.strip(' ') for x in line[2].split(',') if x not in ['']]

                if debug:
                    print(f'Current line: {line}\n')

                # Finally, append the line to the chunk
                chunk.append(line)

        # Set up dict with all the var names
        cooked_data = {}
        for line in data_chunks[0]:
            var_name = line[1]
            vals = line[2]
            if len(vals) > 1:
                for i in range(len(vals)):
                    var_i = var_name + '_' + str(i)
                    cooked_data[var_i] = []
            else:
                cooked_data[var_name] = []

        if debug:
            print(f'Var names: {[k for k, v in cooked_data.items()]}')

        
        # Parse each entry in each chunk to get the data
        for chunk in data_chunks:
            for line in chunk:

                time = float(line[0])
                var_name = line[1]
                val = [float(x) for x in line[2]]

                # Multi-value case
                if len(val) > 1:
                    for i in range(len(val)):
                        modified_var_name = var_name + '_' + str(i)
                        cooked_data[modified_var_name].append([time] + [val[i]])

                # Single-value case
                else:
                    cooked_data[var_name].append([time] + val)


        # Convert all of the list[list] into np.array
        for k, v in cooked_data.items():
            cooked_data[k] = np.array(v)

        return cooked_data

    def parse_config_file(config_f, data):
        # Read a config file given by config_f and return
        # a dict containing {plot_name : [var_names]}
        
        try:
            cf = open(config_f)
            lines = cf.readlines()
            cf.close()

        except Exception as E:
            print('Failed to open config file!')
            # FIXME: HANDLE GRACEFULLY
            raise E

        out = {}
        for line in lines:
            tmp = line.split(':')
            plot_name = tmp[0].strip()
            raw_names = [x.strip() for x in tmp[1].split(',')]
            var_names = []
            for p in raw_names:
                for q in data.keys():
                    if p in q:
                        var_names.append(q)

            out[plot_name] = var_names
        return out

        

    def plot(self) : 

        # Function responsible for plotting and saving all of the data
        # read from the log file

        data = self.data

        # This is stinky, FIXME: REFACTOR

        # Nasty block of code to handle the fact that some variable names
        # have multiple rows associated with them


        
        for ax, cf in zip(self.axes, self.config.items()):
            
            plot_name, var_names = cf
            for name in var_names:
                xs = data[name][0:, 0]
                num_cols = np.shape(data[name])[1]
                for ys in np.hsplit(data[name][0:, 1:], num_cols - 1):
                    ys = data[name][0:, 1]
                    ax.plot(xs, ys, label=name)

            ax.set_title(plot_name) # TODO: MODIFY CONFIG DATA STRUCTURE TO SUPPORT PROPERTIES
            ax.legend()
            # ax.set_xlabel('Time (s)') # FIXME: MODIFY THE SCALE

        # Plot
        plt.show()

