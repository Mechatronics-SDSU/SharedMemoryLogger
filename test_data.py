import shared_memory
from logger import Logger
from multiprocessing import Value, Array, Process
import random
import time
from plotter import Plotter
import numpy as np
from os import listdir
from os import remove
from os.path import join
from functools import partial

# ============================================================================ #
#                                   HELPER SHIT                                #
# ============================================================================ #


# Wrappers for the types of these fckin ctypes
__SMO_ARR3 = type(Array('d', 3))
__SMO_VAL = type(Value('d'))

def t_print(name, mode, err=None):
    if mode=='start':
        print('||| Testing {} |||'.format(name))
    if mode=='success':
        print('||| Test completed for {} |||\n\n'.format(name))
    if mode=='fail':
        print('||| ERROR in Test {} |||:\n\t{}'.format(name, err))

def mock_data_generator(value):
    if isinstance(value, float):
        return random.uniform(-0.1, 0.1)
    elif isinstance(value, int):
        return value

def i_print(msg, mode='p'):
    # p for straight printing, 
    # i for input

    if mode == 'p':
        print(msg)

    if mode == 'i':
        input(msg)

def get_log_file():
    return join('logs/', 
                listdir('logs/')[0]
                )

def clear_logs():
    for file in listdir('./logs'):
        inp = input(f'Are you sure you want to remove {file}? [Y/N]')
        if inp == 'Y':
            remove(join('./logs', file))

def get_sinusoid_v(t, frequency=0, phase=0, amplitude=0, bias=0):
    frequency = frequency * 2 * np.pi # Convert from hz to rad
    return float(
            amplitude * np.sin(t * frequency + phase) + bias
            )


def get_sinusoid_c(t, frequency=0, phase=0, amplitude = 0, bias = 0):
   frequency = frequency * 2 * np.pi # Convert from hz to rad
   v = float(amplitude * np.sin(t * frequency + phase) + bias)
   vals = [0, 0, 0]
   for i in range(3):
       vals[i] = (1 / 3) * (i + 1) * v 
   return vals
       


def get_sinusoid(frequency, phase, c_type, amplitude=1, bias=0) : 
    # Helper function to return sinusoids parameterized by the frequency and
    # phase. Also accounts for the data type going in to shared memory.

    if c_type == 'V':
        return partial(get_sinusoid_v, frequency=frequency, phase=phase, amplitude=amplitude, bias=bias)

    if c_type == 'A':
        return partial(get_sinusoid_c, frequency=frequency, phase=phase, amplitude=amplitude, bias=bias)

    

# ============================================================================ #
#                                   LOGGER TESTING                             #
# ============================================================================ #

def test_unwrap(_print_test=False):

    t_print('unwrap', 'start')
    test_arr = [0.123, 0.456, 0.789]

    val_test = Value('d', 0.0)
    arr_test = Array('d', test_arr)

    val_test = Logger._unwrap(val_test)
    arr_test = Logger._unwrap(arr_test)

    if _print_test:
        print('Val: {}\nArr: {}'.format(val_test, arr_test))
    t_print('unwrap', 'success')

def test_get_var_names(f_name, print_vals=False):
    t_print('get_var_names', 'start')
    
    try:
        names = Logger.get_var_names(f_name)
        if print_vals:
            for name in names:
                print(name)

        print(f'Length: {len(names)}')
    except Exception as E:
        t_print('get_var_names', 'fail', E)
        raise E

    t_print('get_var_names', 'success')


def test_get_vars(print_vals = False):
    t_print('get_vars', 'start')
    S = shared_memory.SharedMemoryWrapper()
    var_names = Logger.get_var_names(None)
    out = Logger.get_vars(S, var_names)
    if print_vals:
        print(out)
    t_print('get_vars', 'success')

def __get_vals_s(mem_v):
    # Function to get a string representation of the memory contained by mem_v
    if type(mem_v) == __SMO_ARR3:
        ret = ''
        for i in range(len(mem_v)):
            ret += str(mem_v[i])
        return ret
    
    if type(mem_v) == __SMO_VAL:
        ret = str(mem_v.value)
        return ret

    return None

def __update_vals(mem_v, inp=None):
    # Intelligently write the value provided by inp to the shared ctypes
    # object mem_v

    # It is assumed that if inp is provided, it is the same shape as mem_v

    if type(mem_v) not in [__SMO_ARR3, __SMO_VAL]:
        raise Exception('Error in __update_vals; unrecognized type for mem_v: {}'.format(type(mem_v)))

    # First, handle the case where this is called without a specified
    # value. We want default behavior to be to zero out the mem_v
    if not inp:
        if type(mem_v) == __SMO_ARR3:
            for i in range(len(mem_v)):
                mem_v[i] = 0

        else:
            mem_v.value = 0

        return

    # Then, do the same thing in the case that inp is not none
    if type(mem_v) == __SMO_ARR3:
        for i in range(len(mem_v)):
            mem_v[i] = inp[i]

    if type(mem_v) == __SMO_VAL:
        mem_v.value = inp

def test_update_vals():
    # Dirty test to confirm __update_vals behaves properly 

    t_print('__update_vals', 'start')
    v = Value('d')
    a = Array('d', 3)
    print('Setting values: ')
    __update_vals(v, 1)
    __update_vals(a, [3, 2, 1])
    print(f'v: {v.value}\t a: {[x for x in a]}\n')

    print('Zeroing out values: ')
    __update_vals(v, None)
    __update_vals(a, None)
    print(f'v: {v.value}\t a: {[x for x in a]}\n')

    t_print('__update_vals', 'success')

def test_get_sinusoid():
    # Quick n dirty test to confirm get_sinusoid works

    t_print('get_sinusoid', 'start')
    v = get_sinusoid(1, 0, 'V')
    a = get_sinusoid(1, 0, 'A')
    print('V: {}'.format(v(np.pi/4)))
    print('A: {}'.format(a(np.pi/4)))
    t_print('get_sinusoid', 'success')




def test_shared_memory(SMO, History, target_FPS = 100, timeout = 5, print_vals = False) :

    # Params:
    # SMO : Shared memory object to be updated

    # History : Dict containing var_name : function pairs. Functions must accept a time
    #   parameter and nothing else (this being the time since start of the main loop)
    #   function returns a value that will "play nicely" with the SMO variable in question

    # target_FPS : Target framerate, in frames per second

    # timeout : Time, in seconds, before the function returns

    t_print('test_shared_memory', 'start')

    start_time = time.time()
    target_delta = 1 / target_FPS # time, in ms, to wait

    count = 0

    while (timeout > 0):
        curr_time = time.time() 
        curr_delta = curr_time - start_time
        if curr_delta > timeout:
            print('Foo!')
            break

        if (count % (target_FPS / 2)) == 0 and print_vals:
            print('Count: {}'.format(count))
            print('Current time: {}'.format(curr_delta))
            for k, v in SMO.__dict__.items():
                print('key: {} \tval: {}'.format(k, __get_vals_s(v)))

        for k, v in SMO.__dict__.items():
            # Edge case to catch zeroing out the "running" value 
            if k == 'running':
                continue
            if k not in History.keys():
                __update_vals(v, None) # Zero corresponding value
            else:
                __update_vals(v, History[k](curr_delta))
           

        # Stall if needed to hit target FPS
        while (time.time() - curr_time) < target_delta:
            pass

        count += 1



# TODO: DELETE
def __test_shared_memory(shared_memory_object, signal=None, timeout=3, print_vals=False):
    # Function responsible for mocking behavior of the shared memory object. 
    # May be passed a dictionary containing a signal for an object to follow, 
    # for example if you wanted to mock the linear position following a sinusoidal pattern
    # Any values not provided a signal will be set to a (seeded) random value
    # Default behavior is for all values to be seeded random

    # Timeout is in seconds since process start; past this point, the shared 
    # memory object will not be udpated.

    t_print('test_shared_memory', 'start')
    start_time = time.time()
    curr_time = time.time() - start_time
    count=0
    while (shared_memory_object.running.value and (curr_time < timeout)) : 
        for k, v in shared_memory_object.__dict__.items():
            __update_vals(signal, (k, v))

        if count % 50 == 0 and print_vals:
            for k, v in shared_memory_object.__dict__.items():
                print(f'{k} ||| {Logger._unwrap(v)}')

        # Short time delay
        time.sleep(0.01)
        curr_time = time.time() - start_time
        count += 1

    t_print('test_shared_memory', 'success')


def integration_test(config_f=None, test_time=5) :
    # Spin up the SMO and processes required to fully integration test the logger
    
    t_print('integration_test', 'start')

    shared_memory_object = shared_memory.SharedMemoryWrapper()
    shared_memory_object.running.value=1

    logger_obj = Logger(shared_memory_object, var_names_f=config_f)
    num_vars = len(shared_memory_object.__dict__.keys())

    logger_P = Process(target=logger_obj.log_shared_memory, kwargs={'curr_format' : '%(message)s'})

    # Set up a time history for the shared memory to follow
    h = {}
    h['imu_orientation']    = get_sinusoid(1, 0, 'A', amplitude=1)
    h['dvl_yaw']            = get_sinusoid(4, 0, 'V', amplitude=0.25, bias=0.125)
    h['dvl_pitch']          = get_sinusoid(0.25, np.pi/2, 'V', amplitude=2)
    h['dvl_roll']           = get_sinusoid(1, np.pi, 'V', bias=2)

    # Only two hard things in computer science: cache invalidation, naming things and oof-by-one errs
    test_mem_P = Process(target=test_shared_memory, 
                         args=(shared_memory_object, h), 
                         kwargs={'timeout' : test_time, 'target_FPS' : 100, 'print_vals' : False}
                     )

    # Important testing note!

    test_mem_P.start()


    logger_P.start()
    # Naptime, bitch
    time.sleep(test_time)

    # Stop everything
    shared_memory_object.running.value=0

    logger_P.join()
    test_mem_P.join()

    t_print('integration_test', 'success')


def test_logger():
    # test_unwrap(True)
    # test_get_vars(True)

    # test_get_var_names('test.ini', True)

    # S = shared_memory.SharedMemoryWrapper()
    # num_copies = len(S.__dict__.keys())
    # test_shared_memory(S, signal=get_sinusoid(num_copies=num_copies), print_vals=True)

    integration_test(config_f='test.ini', test_time=5)

# ============================================================================ #
#                              PLOTTER TESTING                                 #
# ============================================================================ #

def test_parse_data(f_name=None, debug=True):

    t_print('parse_input_file', 'start')

    # Test error handling:
    print('This should error, but not crash: ')
    ret = Plotter.parse_input_file('foo', debug)
    if ret:
        t_print('parse_input_file', 'fail', f'Should return None, returned {ret}')

    if not f_name:
        f_name = get_log_file()

    # Test functionality
    ret = Plotter.parse_input_file(f_name, debug)

    print(f'Output type: {type(ret)}')
    for k, v in ret.items():
        if (type(v) == np.ndarray) and debug:
            print(f'Shape of {k}: \n\t{np.shape(v)}')
        elif debug:
            print('!! WARNING !! - Data type is not ndarray!')
            input(f'k: {k} \t\t v: {v}')
        

    t_print('parse_input_file', 'success')


# FIXME: BROKEN, EXPECTS PARSED DATA TO FUNCTION
def test_parse_config(f_name='test.ini', debug=False):

    t_print('parse_config_file', 'start')

    ret = Plotter.parse_config_file(f_name)
    if debug:
        print(ret)

    t_print('parse_config_file', 'success')

def test_plotter_init(log_f, config_f, out_f, mode='p', debug=False):

    t_print('__init__', 'start')

    if not log_f:
        log_f = get_log_file()

    p = Plotter(log_f, config_f, out_f)

    if debug:

        i_print(f'Plotter data: {p.data} \n\n', mode)
        i_print(f'Plotter config: {p.config} \n\n', mode)
        i_print(f'Plotter out_f: {p.out_f} \n\n', mode)
        i_print(f'Plotter type: {p.plot_type} \n\n', mode)

    t_print('__init__', 'success')

    return p

def test_plotter_plot(plotter):

    t_print('plotting', 'start')

    plotter.plot()

    t_print('plotting', 'success')


def test_plotter():
    test_parse_data(debug=False)
    # test_parse_config(debug=False)
    p = test_plotter_init(None, 'test.ini', 'out.png')
    test_plotter_plot(p)



if __name__ == '__main__':
    clear_logs()
    test_logger()
    test_plotter()
    
