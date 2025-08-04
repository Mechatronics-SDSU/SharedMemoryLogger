import logging
from datetime import datetime
import time
import shared_memory
import os
from matplotlib import pyplot as plt
from multiprocessing import Array, Value


class Logger:
    def __init__(self, shared_memory_object, log_file=None, log_frequency=.1,log_dir='logs', var_names_f = None):
        
        self.log_file = Logger._get_log_file(log_file)
        self.logger = None # Placeholder, initialized later
        # FIXME: BAD PRACTICE
        self.shared_memory_object = shared_memory_object
        self.log_frequency = log_frequency
        self.log_dir = log_dir
        # FIXME: IMPLEMENT
        self.var_names = Logger.get_var_names(
                    var_names_f
                ) # File controlling which variables to be logged. Used in conjuction with plotter.

        self.__START_TIME = time.time()

    def print(self):
        print(f'Log file: {self.log_file}')
        print(f'Shared memory object: {self.shared_memory_object}')
        print(f'Log frequency: {self.log_frequency}')
        print(f'Log dir: {self.log_dir}')
        print(f'Variable names: {self.var_names}')
        print(f'Start time: {self.__START_TIME}')

    def _get_log_file(log_file):
        # Wrapper responsible for returning the log filename. If None is provided (default), 
        # returns a string representation of the day/time 

        if not log_file:
            # Create a pathname from the day/time at invocation
            return os.path.normpath(
                        datetime.now().strftime('%m%d%y_%H_%M_%S.log')
                    )

        return log_file

    def _unwrap(var) : # Helper function to unwrap (potentially high dimensional) values from shared memory
        # Return string

        # If it's an array
        if isinstance(var, type(Array('d', [3]))):
            out = ""
            for x in list(var):
                out += str(x) + ' '

            return out

        # If it's a value
        if isinstance(var, type(Value('d', 1.0))):
            return var.value

        raise Exception('var was neither of type Array nor Value\nType: {}'.format(type(var)))

    def get_var_names(var_names_f : str = None) -> list:
        # Should try to read from a file, if one exists. Returns a list of attributes
        # to read from.

        if var_names_f:
            # FIXME: IMPLEMENT
            pass
        else:
            return ['dvl_yaw', 'dvl_pitch', 'dvl_roll', 'dvl_x', 'dvl_y', 'dvl_z']

    def get_vars(shared_mem, var_names):
        attrs = shared_mem.__dict__
        ret = [k for k in attrs.keys() if k in var_names]
        return ret

    def log_shared_memory(self, curr_format='%(asctime)s %(levelname)s:%(message)s'):
        # Set up logging
        logging.basicConfig(filename=self.log_file, level=logging.DEBUG,
                            format=curr_format)  # Format parameterized cause I think its silly as is
        self.logger = logging.getLogger()
        self.logger.info('Logger started.')
        
        while (self.shared_memory_object.running.value):
            # Log the values from shared memory
            # Sleep for a short duration to avoid excessive logging
            curr_time = time.time() - self.__START_TIME
            vars_to_log = Logger.get_vars(self.shared_memory_object, self.var_names)
            for k in vars_to_log:
                val = getattr(self.shared_memory_object, k)
                self.logger.debug(f'{curr_time} : {k} : {Logger._unwrap(val)}')
            time.sleep(self.log_frequency)
            self.logger.debug('break')
        self.logger.info('Logger stopped.')

        # Close the logger, move the log file to the specified directory
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
            handler.close()

        self.move_log_file()

    def move_log_file(self):
        # Move the log file to the specified directory
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        new_log_file_path = os.path.join(self.log_dir, self.log_file)
        os.rename(self.log_file, new_log_file_path)
        self.log_file = new_log_file_path
        print(f"Log file moved to {self.log_dir}")

    def graph_logs(self):
        self.logger.setLevel(logging.WARNING)
        # Read the log file and plot the values
        with open(self.log_file, 'r') as f:
            lines = f.readlines()

        # Extract values from the log file
        imu_lin_acc = []
        imu_ang_vel = []
        distance_from_object = []
        depth = []
        dvl_status = []
        dvl_velocity_valid = []

        for line in lines:
            if 'imu_lin_acc[0]' in line:
                imu_lin_acc.append(eval(line.split(': ')[1]))
            elif 'imu_ang_vel[0]' in line:
                imu_ang_vel.append(eval(line.split(': ')[1]))
            elif 'distance_from_object' in line:
                distance_from_object.append(float(line.split(': ')[1]))
            elif 'depth' in line:
                depth.append(float(line.split(': ')[1]))
            elif 'running' in line:
                dvl_status.append(bool(line.split(': ')[1]))
            elif 'dvl_velocity_valid' in line:
                dvl_velocity_valid.append(bool(line.split(': ')[1]))

        # Plot the values
        plt.figure(figsize=(10, 6))
        plt.subplot(3, 2, 1)
        plt.plot(imu_lin_acc)
        plt.title('IMU Linear Acceleration')

        plt.subplot(3, 2, 2)
        plt.plot(imu_ang_vel)
        plt.title('IMU Angular Velocity')

        plt.subplot(3, 2, 3)
        plt.plot(distance_from_object)
        plt.title('Distance from Object')

        plt.subplot(3, 2, 4)
        plt.plot(depth)
        plt.title('Depth')

        plt.subplot(3, 2, 5)
        plt.plot(dvl_status)
        plt.title('DVL Status')

        plt.subplot(3, 2, 6)
        plt.plot(dvl_velocity_valid)
        plt.title('DVL Velocity Valid')

        plt.tight_layout()
        plt.show()
        print("Graphing complete.")
        self.logger.info('Graphing complete.')
        


