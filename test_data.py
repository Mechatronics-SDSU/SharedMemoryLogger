import shared_memory
from multiprocessing import Value, Array
import random
import time

def mock_data_generator(value):
    if isinstance(value, float):
        return random.uniform(-0.1, 0.1)
    elif isinstance(value, int):
        return value

def test_shared_memory(shared_memory_object):
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
    