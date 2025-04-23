

import argparse
import ffmpeg

import os
import re
from util import find_closest_factors, build_ffmpeg_layout, sort_input_files

parser = argparse.ArgumentParser(description='Combine input video / images to a mosaic for use on a 3D Global multiview monitor')
parser.add_argument( "-i", "--inputs", nargs='+', help="List of files to combine to a mosaic", required=True)
parser.add_argument("-o", "--output", help="Name or path to the output file. If the file doesn't contain a mosaic pattern, it will be added to the file before the last dot character (e.g. out.mosaic.3x3.mp4). If it contains a mosaic pattern, the number of input files exceeds ROWS * COLUMNS, some input files will not be considered in the final output", required=True)
parser.add_argument("--debug-text", action="store_true", help="Display a text overlay for the views")
parser.add_argument("-y", "--overwrite", action="store_true", help="Overwrite output files")
parser.add_argument("--dry", action="store_true", help="Print the ffmpeg command instead of running it")
args = parser.parse_args()

inputs = args.inputs
output = args.output

inputs = sort_input_files(inputs)

rows, cols = find_closest_factors(len(inputs))

if "mosaic" in args.output:
    # Extract the row and column from the mosaic file name (e.g. out.mosaic.3x3.mp4)
    output_filename = os.path.basename(output)
    output_identifiers = output_filename.split(".")
    mosaic_index = output_identifiers.index("mosaic")
    match = re.compile(r"(\d+)x(\d+)").match(output_identifiers[mosaic_index + 1])
    if not match:
        raise ValueError("The mosaic pattern must be in the format ROWSxCOLUMNS")
    rows = int(match.group(1))
    cols = int(match.group(2))
else:
    # Add the mosaic pattern to the output file name
    output_filename = os.path.basename(output)
    output_path = os.path.dirname(output) + "/" if os.path.dirname(output) else ""
    output_identifiers = output_filename.split(".")
    output = output_path + F'{".".join(output_identifiers[:-1])}.mosaic.{rows}x{cols}.{output_identifiers[-1]}'



input_streams = [ffmpeg.input(i) for i in inputs]

if len(input_streams) > rows * cols:
    input_streams = input_streams[:rows * cols]

if args.debug_text: 
    input_streams = [ffmpeg.drawtext(s, text=F"{i+1}", fontcolor="white", x="(w-text_w)/2",  y="(h-text_h)/2", fontsize=64) for i, s in enumerate(input_streams)]


layout = build_ffmpeg_layout(rows, cols, len(inputs))
output_stream = ffmpeg \
    .filter(input_streams, 'xstack', inputs=F"{len(input_streams)}", layout=layout) \
    .output(output) \

if args.overwrite:
    output_stream = ffmpeg.overwrite_output(output_stream)

if args.dry:
    print(output_stream.compile())
    exit()

# Finished building the command --> run ffmpeg
output_stream.run()
