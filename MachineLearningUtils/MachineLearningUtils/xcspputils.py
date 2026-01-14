import numpy as np

def fill_none_elements(arr):
    """For each None element in the array, replace it with the last non-None value."""

    # Check if the first element is None and set it to the first non-None value
    if arr[0] is None:
        first_non_none_index = next((i for i, x in enumerate(arr) if x is not None), -1)
        if first_non_none_index != -1:
            arr[:first_non_none_index] = [arr[first_non_none_index]] * first_non_none_index

    # Fill None elements with the last non-None value
    for i in range(1, len(arr)):
        if arr[i] is None:
            arr[i] = arr[i - 1]

def running_average(data, window_size):
    '''Given a list of data with None elements, returns a list of running averages
    with the same length as the input data, where None elements are replaced with
    nearest valid calculated averages. We get the same length by appending
    window_size - 1 copies of the first valid average to the beginning of the list.
    '''
    valid_data = [item for item in data if item is not None]
    valid_data_sums = np.convolve(valid_data, np.ones(window_size), mode='valid')
    valid_data_sums = np.concatenate((np.full(window_size - 1, valid_data_sums[0]), valid_data_sums))
    valid_data_sums = valid_data_sums / window_size
    indices = np.where(np.array(data) != None)[0]
    averaged_data = np.full(len(data), None, dtype=object)
    averaged_data[indices] = valid_data_sums
    fill_none_elements(averaged_data)
    return averaged_data