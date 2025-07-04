

import argparse
import ffmpeg
import json

import os
import re
from util import find_closest_factors, build_ffmpeg_layout, sort_input_files, extract_tiles_from_mosaic

parser = argparse.ArgumentParser(description='Combine input video / images to a mosaic for use on a 3D Global multiview monitor')
parser.add_argument( "-i", "--inputs", nargs='+', help="List of files to combine to a mosaic", required=True)
parser.add_argument("-o", "--output", help="Name or path to the output file. If the file doesn't contain a mosaic pattern, it will be added to the file before the last dot character (e.g. out.mosaic.3x3.mp4). If it contains a mosaic pattern (e.g. 3x3) or Looking Glass format (e.g. 8x6a0.75), the dimensions will be extracted. If the number of input files exceeds ROWS * COLUMNS, some input files will not be considered in the final output", required=True)
parser.add_argument("--debug-text", action="store_true", help="Display a text overlay for the views")
parser.add_argument("-f", "--filter-views", type=str, help="Filter specific views to include in the output. Specify as a JSON array of view indices (0-based), e.g., '[16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]' for a 4x4 grid from views 16-31")
parser.add_argument("-y", "--overwrite", action="store_true", help="Overwrite output files")
parser.add_argument("--dry", action="store_true", help="Print the ffmpeg command instead of running it")
args = parser.parse_args()

inputs = args.inputs
output = args.output

inputs = sort_input_files(inputs)

# Check if we have a single input that is itself a mosaic (like Looking Glass format)
is_mosaic_input = False
source_rows = 0
source_cols = 0
if len(inputs) == 1:
    input_filename = os.path.basename(inputs[0])
    input_looking_glass_match = re.search(r"(\d+)x(\d+)a[\d.]+", input_filename)
    if input_looking_glass_match:
        # Single input is a Looking Glass mosaic
        is_mosaic_input = True
        source_cols = int(input_looking_glass_match.group(1))
        source_rows = int(input_looking_glass_match.group(2))
        print(f"Detected Looking Glass input: {source_cols}x{source_rows} grid")

# Determine target grid dimensions from output filename
output_filename = os.path.basename(output)

# Check for Looking Glass mosaic pattern (e.g. 8x6a0.75) in output filename
looking_glass_match = re.search(r"(\d+)x(\d+)a[\d.]+", output_filename)
if looking_glass_match:
    cols = int(looking_glass_match.group(1))  # Looking Glass format is COLSxROWS
    rows = int(looking_glass_match.group(2))
elif "mosaic" in output_filename:
    # Extract the row and column from the mosaic file name (e.g. out.mosaic.3x3.mp4)
    output_identifiers = output_filename.split(".")
    mosaic_index = output_identifiers.index("mosaic")
    match = re.compile(r"(\d+)x(\d+)").match(output_identifiers[mosaic_index + 1])
    if not match:
        raise ValueError("The mosaic pattern must be in the format ROWSxCOLUMNS")
    rows = int(match.group(1))
    cols = int(match.group(2))
else:
    # Use default grid dimensions
    if is_mosaic_input:
        # For mosaic inputs, use the source dimensions as default
        rows, cols = source_rows, source_cols
    else:
        rows, cols = find_closest_factors(len(inputs))

# Always ensure output filename has mosaic pattern
if "mosaic" not in output_filename and not re.search(r"\d+x\d+a[\d.]+", output_filename):
    output_path = os.path.dirname(output) + "/" if os.path.dirname(output) else ""
    output_identifiers = output_filename.split(".")
    output = output_path + F'{".".join(output_identifiers[:-1])}.mosaic.{rows}x{cols}.{output_identifiers[-1]}'



# Create input streams
if is_mosaic_input:
    # Extract tiles from the single mosaic input
    input_streams = extract_tiles_from_mosaic(inputs[0], source_rows, source_cols)
else:
    # Use individual input files
    input_streams = [ffmpeg.input(i) for i in inputs]

# Apply view filtering if specified
if args.filter_views:
    try:
        filter_indices = json.loads(args.filter_views)
        if not isinstance(filter_indices, list):
            raise ValueError("Filter views must be a JSON array")
        
        # Filter the input streams based on the specified indices
        filtered_streams = []
        for idx in filter_indices:
            if 0 <= idx < len(input_streams):
                filtered_streams.append(input_streams[idx])
            else:
                print(f"Warning: View index {idx} is out of range (0-{len(input_streams)-1}), skipping")
        
        if not filtered_streams:
            raise ValueError("No valid view indices provided")
            
        input_streams = filtered_streams
        print(f"Filtered to {len(input_streams)} views: {filter_indices}")
        
        # Recalculate grid dimensions based on filtered views
        rows, cols = find_closest_factors(len(input_streams))
        
        # Update output filename with new dimensions
        if "mosaic" in output:
            # Replace existing mosaic pattern with new dimensions
            output = re.sub(r'\.mosaic\.\d+x\d+\.', f'.mosaic.{rows}x{cols}.', output)
        elif not re.search(r"\d+x\d+a[\d.]+", os.path.basename(output)):
            # Add mosaic pattern if none exists
            output_path = os.path.dirname(output) + "/" if os.path.dirname(output) else ""
            output_identifiers = os.path.basename(output).split(".")
            output = output_path + F'{".".join(output_identifiers[:-1])}.mosaic.{rows}x{cols}.{output_identifiers[-1]}'
            
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Invalid filter views format: {e}. Use JSON array format like '[0, 1, 2, 3]'")

if len(input_streams) > rows * cols:
    input_streams = input_streams[:rows * cols]

if args.debug_text: 
    input_streams = [ffmpeg.drawtext(s, text=F"{i+1}", fontcolor="white", x="(w-text_w)/2",  y="(h-text_h)/2", fontsize=64) for i, s in enumerate(input_streams)]

# Handle single input vs multiple inputs differently
if len(input_streams) == 1:
    # For single input, just output directly (no stacking needed)
    output_stream = ffmpeg.output(input_streams[0], output)
else:
    # For multiple inputs, use xstack
    layout = build_ffmpeg_layout(rows, cols, len(input_streams))
    output_stream = ffmpeg \
        .filter(input_streams, 'xstack', inputs=F"{len(input_streams)}", layout=layout) \
        .output(output)

if args.overwrite:
    output_stream = ffmpeg.overwrite_output(output_stream)

if args.dry:
    print(output_stream.compile())
    exit()

# Finished building the command --> run ffmpeg
output_stream.run()
