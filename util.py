import math
import os
import re

def sort_input_files(inputs):
    # If there's only one input, no need to sort
    if len(inputs) == 1:
        return inputs
    
    # Find the numbers in the input files and sort by them
    prefix = os.path.commonprefix(inputs)
    
    # If the prefix is the entire filename (which happens with single files), 
    # fall back to sorting by the entire filename
    if any(len(i) == len(prefix) for i in inputs):
        # Try to extract numbers from the full filenames instead
        regex = re.compile(r"(\d+)")
        numbers = []
        for inp in inputs:
            match = regex.search(os.path.basename(inp))
            if match:
                numbers.append(int(match.group(1)))
            else:
                # If no number found, use 0 as default
                numbers.append(0)
        sorted_inputs = [x for _, x in sorted(zip(numbers, inputs))]
        return sorted_inputs
    
    # Original logic for when we have a meaningful prefix
    suffixes = [i[len(prefix):] for i in inputs]
    regex = re.compile(r"(\d+)")
    numbers = []
    for i in inputs:
        suffix = i[len(prefix):]
        match = regex.search(suffix)
        if match:
            numbers.append(int(match.group(1)))
        else:
            # If no number found in suffix, use 0 as default
            numbers.append(0)
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

def extract_tiles_from_mosaic(input_file, source_rows, source_cols):
    """
    Extract individual tiles from a mosaic video/image file.
    Returns a list of ffmpeg input streams, each representing one tile.
    """
    import ffmpeg
    
    # Create the base input
    input_stream = ffmpeg.input(input_file)
    
    # We need to calculate tile dimensions - this will be done at runtime by FFmpeg
    # Each tile will be w/source_cols wide and h/source_rows tall
    tile_width_expr = f"iw/{source_cols}"
    tile_height_expr = f"ih/{source_rows}"
    
    tiles = []
    for row in range(source_rows):
        for col in range(source_cols):
            # Calculate the x,y position for this tile
            x_expr = f"{col}*{tile_width_expr}"
            y_expr = f"{row}*{tile_height_expr}"
            
            # Crop this tile from the source
            tile = ffmpeg.crop(input_stream, 
                             x=x_expr, 
                             y=y_expr, 
                             width=tile_width_expr, 
                             height=tile_height_expr)
            tiles.append(tile)
    
    return tiles

def apply_aspect_ratio_padding(input_stream, target_aspect_ratio):
    """
    Apply aspect ratio padding to an input stream using FFmpeg's pad filter.
    Adds black borders to make the video match the target aspect ratio.
    
    Args:
        input_stream: FFmpeg input stream
        target_aspect_ratio: String in format "width:height" (e.g., "16:9")
    
    Returns:
        FFmpeg stream with aspect ratio padding applied
    """
    import ffmpeg
    
    # Parse the target aspect ratio
    try:
        width_ratio, height_ratio = map(int, target_aspect_ratio.split(':'))
        target_ratio = width_ratio / height_ratio
    except (ValueError, ZeroDivisionError):
        raise ValueError(f"Invalid aspect ratio format: {target_aspect_ratio}. Use format 'width:height' like '16:9'")
    
    # Calculate padding using FFmpeg expressions
    # We'll use the pad filter with dynamic calculations
    # The logic: if input is wider than target, add top/bottom padding; if taller, add left/right padding
    
    # Calculate target dimensions based on input
    # If input_ratio > target_ratio: input is too wide, need top/bottom padding
    # If input_ratio < target_ratio: input is too tall, need left/right padding
    
    # For width: if we need vertical padding, width stays same; if horizontal padding, width = height * target_ratio
    # For height: if we need horizontal padding, height stays same; if vertical padding, height = width / target_ratio
    
    width_expr = f"if(gt(iw/ih,{target_ratio}),iw,ih*{target_ratio})"
    height_expr = f"if(gt(iw/ih,{target_ratio}),iw/{target_ratio},ih)"
    
    # Center the content
    x_expr = f"(ow-iw)/2"
    y_expr = f"(oh-ih)/2"
    
    # Apply padding with black background
    padded_stream = ffmpeg.filter(input_stream, 'pad', 
                                 width=width_expr,
                                 height=height_expr, 
                                 x=x_expr, 
                                 y=y_expr,
                                 color='black')
    
    return padded_stream
