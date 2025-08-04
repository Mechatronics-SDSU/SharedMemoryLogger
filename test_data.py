import shared_memory
from logger import Logger
from multiprocessing import Value, Array, Process
import random
import time

def t_print(name, mode=None):
    if mode=='start':
        print('||| Testing {} |||'.format(name))
    if mode=='success':
        print('||| Test completed for {} |||\n\n'.format(name))
    if mode=='fail':
        #FIXME: IMPLEMENT
        print('FIXME: IMPLEMENT in t_print')

def mock_data_generator(value):
    if isinstance(value, float):
        return random.uniform(-0.1, 0.1)
    elif isinstance(value, int):
        return value

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

# FIXME: DELETE
def __test_shared_memory(shared_memory_object):
    while (shared_memory_object.running.value):
        items = list(shared_memory_object.__dict__.items())
        # Iterate through all attributes of the shared memory object
        # and update their values with mock data
        # This simulates real-time data updates for testing purposes
        for _, value in items:
            if isinstance(value, type(Array('d', 3))):
                for i in range(len(value)):
                    value[i] = mock_data_generator(value[i])
            else:
                value.value = mock_data_generator(value.value)

        # Simulate a short delay to mimic real-time data updates
        time.sleep(0.1)
        # print(items)
    print("Shared memory test completed successfully.")

def test_get_vars(print_vals = False):
    t_print('get_vars', 'start')
    S = shared_memory.SharedMemoryWrapper()
    var_names = Logger.get_var_names(None)
    out = Logger.get_vars(S, var_names)
    if print_vals:
        print(out)
    t_print('get_vars', 'success')

def __update_vals(signal, t):
    k, v = t
    if not signal:
        if isinstance(v, type(Array('d', 3))):
            for i in range(len(v)):
                v[i] = mock_data_generator(v[i])

        elif isinstance(v, type(Value('d'))):
            v.value = mock_data_generator(v.value)

        else :
            raise Exception('ERROR in __update_vals: type not recognized!\nActual type: {}'.format(
                type(v)))

    else:
        raise Exception('FIXME: IMPLEMENT SIGNAL in __update_vals')

def test_shared_memory(shared_memory_object, signal=None, timeout=3, print_vals=False):
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
            # FIXME: IMPLEMENT SIGNAL
            __update_vals(signal, (k, v))

        if count % 50 == 0 and print_vals:
            for k, v in shared_memory_object.__dict__.items():
                print(f'{k} ||| {Logger._unwrap(v)}')

        # Short time delay
        time.sleep(0.1)
        curr_time = time.time() - start_time

    t_print('test_shared_memory', 'success')


def integration_test(config_f=None, test_time=5) :
    # Spin up the SMO and processes required to fully integration test the logger
    
    t_print('integration_test', 'start')

    shared_memory_object = shared_memory.SharedMemoryWrapper()
    logger_obj = Logger(shared_memory_object)

    logger_P = Process(target=logger_obj.log_shared_memory, kwargs={'curr_format' : '%(message)s'})

    # Only two hard things in computer science: cache invalidation, naming things and oof-by-one errs
    test_mem_P = Process(target=test_shared_memory, args=(shared_memory_object,), kwargs={'timeout' : test_time + 1})

    test_mem_P.start()


    logger_P.start()
    # Naptime, bitch
    time.sleep(test_time)

    # Stop everything
    shared_memory_object.running.value=0

    logger_P.join()
    test_mem_P.join()

    t_print('integration_test', 'success')



def main():
    test_unwrap(True)
    test_get_vars(True)

    # S = shared_memory.SharedMemoryWrapper()
    # test_shared_memory(S, print_vals=True)

    integration_test(test_time=1)


if __name__ == '__main__':
    main()
    
