from multiprocessing                        import Process, Value
from shared_memory                          import SharedMemoryWrapper
from logger                                 import Logger    
from test_data                              import test_shared_memory
import time

"""
    discord: @kialli
    github: @kchan5071
    
    This is the main file that will be run to start the program.
    Combined the old launch.py with the launch.py.DVL_Test
    
"""
def main():
    # create shared memory
    shared_memory_object = SharedMemoryWrapper()
    # set deadzone
    temp_x_hard_deadzone = 400 #FIXME
    # set mode
    mode = "normal"

    if (mode == "normal"): 
        # create objects
        logger_object = Logger(shared_memory_object)
        # set shared memory values
        
        #create processes
        logger_process = Process(target=logger_object.log_shared_memory)
        test_shared_memory_process = Process(target=test_shared_memory, args=(shared_memory_object,))


        # start processes
        logger_process.start()
        test_shared_memory_process.start()

        time.sleep(10)
        # stop processes
        shared_memory_object.running.value = 0

        # wait for processes to finish
        logger_process.join()
        test_shared_memory_process.join()

    #END
    print("Program has finished")


if __name__ == '__main__':
    print("RUN FROM LAUNCH")
    main()