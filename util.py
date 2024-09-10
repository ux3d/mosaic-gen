import math
import os
import re

def sort_input_files(inputs):
    # Find the numbers in the input files and sort by them
    prefix = os.path.commonprefix(inputs)
    # Get the first number in the file name that is different for each file
    suffixes = [i[len(prefix):] for i in inputs]
    regex = re.compile(r"(\d+)")
    numbers = [int(regex.search(i[len(prefix):]).group(1)) for i in inputs]
    sorted_inputs = [x for _, x in sorted(zip(numbers, inputs))]
    return sorted_inputs


def find_closest_factors(n) -> tuple[int, int]:
    test_factor = math.floor(math.sqrt(n))
    while n % test_factor != 0:
        test_factor = test_factor - 1
    return (test_factor, n // test_factor)

def build_ffmpeg_layout(rows, columns, num_inputs):
    
    row_offsets = []
    for i in range(1, rows):
        previous_offset = [row_offsets[-1]] if row_offsets else []
        current_offset = "+".join(previous_offset + ["h" + str(i - 1)])
        row_offsets.append(current_offset)
    row_offsets = ["0"] + row_offsets

    column_offsets = []
    for i in range(1, columns):
        previous_offset = [column_offsets[-1]] if column_offsets else []
        current_offset = "+".join(previous_offset + ["w" + str(i - 1)])
        column_offsets.append(current_offset)
    column_offsets = ["0"] + column_offsets

    layout = []
    for row, row_offset in enumerate(row_offsets):
        for column, column_offset in enumerate(column_offsets):
            layout.append(f"{column_offset}_{row_offset}")
        
    layout = layout[:num_inputs]

    layout = "|".join(layout)
    return layout
