import argparse
import ffmpeg
import json
import re

import os
from util import find_closest_factors, build_ffmpeg_layout, sort_input_files, extract_tiles_from_mosaic, apply_aspect_ratio_padding

def can_use_image_sequence(input_files):
    """
    Check if input files can be treated as an image sequence for FFmpeg.
    Returns (can_use, pattern, start_number) or (False, None, None)
    """
    if len(input_files) < 2:
        return False, None, None
    
    # Check if all files are images with same extension
    extensions = set(os.path.splitext(f)[1].lower() for f in input_files)
    if len(extensions) != 1 or extensions.pop() not in ['.png', '.jpg', '.jpeg']:
        return False, None, None
    
    # Check if files follow a sequential pattern
    basenames = [os.path.splitext(os.path.basename(f))[0] for f in input_files]
    
    # Try to find a common pattern with numbers
    for i, basename in enumerate(basenames):
        # Find numbers in the basename
        numbers = re.findall(r'\d+', basename)
        if not numbers:
            return False, None, None
        
        # Use the last number as the sequence number
        seq_num = int(numbers[-1])
        if i == 0:
            start_num = seq_num
            # Create pattern by replacing the last number with %d
            pattern_base = re.sub(r'\d+(?=\D*$)', '%d', basename)
            pattern = os.path.join(os.path.dirname(input_files[0]), pattern_base + os.path.splitext(input_files[0])[1])
        else:
            expected_num = start_num + i
            if seq_num != expected_num:
                return False, None, None
    
    return True, pattern, start_num

def is_ffmpeg_pattern(file_path):
    """
    Check if a file path contains FFmpeg pattern like %04d
    """
    return '%' in file_path and 'd' in file_path

parser = argparse.ArgumentParser(description='Combine input video / images to a mosaic for use on a 3D Global multiview monitor')
parser.add_argument( "-i", "--inputs", nargs='+', help="List of files to combine to a mosaic", required=True)
parser.add_argument("-o", "--output", help="Name or path to the output file. If the file doesn't contain a pattern, it will be added automatically. Supported patterns: mosaic (e.g., out.mosaic.3x3.mp4), Looking Glass (e.g., out_8x6a0.75.mp4), or SBS (e.g., out.sbs.mp4 for side-by-side). SBS format requires exactly 2 views. If the number of input files exceeds the target grid size, some input files will not be considered in the final output", required=True)
parser.add_argument("--debug-text", action="store_true", help="Display a text overlay for the views")
parser.add_argument("-f", "--filter-views", type=str, help="Filter specific views to include in the output. Specify as a JSON array of view indices (0-based), e.g., '[16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]' for a 4x4 grid from views 16-31")
parser.add_argument("-a", "--aspect-ratio", type=str, help="Force aspect ratio for individual views by adding black borders. Format: 'width:height' (e.g., '16:9', '4:3', '1:1'). Views will be padded with black borders to match this aspect ratio.")
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

# Check for SBS (Side-by-Side) format first
is_sbs_output = ".sbs." in output_filename
if is_sbs_output:
    # SBS format is always 2x1 (2 views side by side)
    rows = 1
    cols = 2
elif looking_glass_match := re.search(r"(\d+)x(\d+)a[\d.]+", output_filename):
    # Check for Looking Glass mosaic pattern (e.g. 8x6a0.75) in output filename
    cols = int(looking_glass_match.group(1))  # Looking Glass format is COLSxROWS
    rows = int(looking_glass_match.group(2))
elif "mosaic" in output_filename:
    # Extract the row and column from the mosaic file name (e.g. out.mosaic.3x3.mp4)
    output_identifiers = output_filename.split(".")
    try:
        mosaic_index = output_identifiers.index("mosaic")
        match = re.compile(r"(\d+)x(\d+)").match(output_identifiers[mosaic_index + 1])
        if not match:
            raise ValueError("The mosaic pattern must be in the format ROWSxCOLUMNS")
        rows = int(match.group(1))
        cols = int(match.group(2))
    except (ValueError, IndexError):
        # Fallback to default grid dimensions
        if is_mosaic_input:
            rows, cols = source_rows, source_cols
        else:
            rows, cols = find_closest_factors(len(inputs))
else:
    # Use default grid dimensions
    if is_mosaic_input:
        # For mosaic inputs, use the source dimensions as default
        rows, cols = source_rows, source_cols
    else:
        rows, cols = find_closest_factors(len(inputs))

# Always ensure output filename has the appropriate pattern
if not is_sbs_output and "mosaic" not in output_filename and not re.search(r"\d+x\d+a[\d.]+", output_filename):
    output_path = os.path.dirname(output) + "/" if os.path.dirname(output) else ""
    output_identifiers = output_filename.split(".")
    
    # Determine if this should be SBS based on dimensions
    if rows == 1 and cols == 2:
        output = output_path + F'{".".join(output_identifiers[:-1])}.sbs.{output_identifiers[-1]}'
    else:
        output = output_path + F'{".".join(output_identifiers[:-1])}.mosaic.{rows}x{cols}.{output_identifiers[-1]}'



# Create input streams
if is_mosaic_input:
    # Extract tiles from the single mosaic input
    input_streams = extract_tiles_from_mosaic(inputs[0], source_rows, source_cols)
else:
    # Check if inputs are FFmpeg patterns (e.g., path_%04d.png)
    if all(is_ffmpeg_pattern(inp) for inp in inputs):
        # Each input is an FFmpeg image sequence pattern
        print(f"Using FFmpeg image sequence patterns for {len(inputs)} cameras")
        input_streams = []
        for i, pattern in enumerate(inputs):
            print(f"Camera {i+1}: {pattern}")
            # Use FFmpeg image sequence input for each camera
            stream = ffmpeg.input(pattern, f='image2', start_number=1)
            input_streams.append(stream)
    else:
        # Check if we can use FFmpeg image sequence format for individual files
        can_use_seq, pattern, start_num = can_use_image_sequence(inputs)
        
        if can_use_seq:
            # Use FFmpeg image sequence input - much more efficient for many PNG files
            print(f"Using image sequence format: {pattern} (starting from {start_num})")
            base_input = ffmpeg.input(pattern, 
                                     f='image2',
                                     start_number=start_num,
                                     vframes=len(inputs))
            
            # Create individual streams by selecting specific frames
            input_streams = []
            for i in range(len(inputs)):
                # Use select filter to pick specific frame
                frame_stream = ffmpeg.filter(base_input, 'select', f'eq(n,{i})')
                input_streams.append(frame_stream)
        else:
            # Use individual input files (fallback for mixed file types or non-sequential)
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
            if rows == 1 and cols == 2:
                # Convert to SBS format
                output = re.sub(r'\.mosaic\.\d+x\d+\.', '.sbs.', output)
            else:
                output = re.sub(r'\.mosaic\.\d+x\d+\.', f'.mosaic.{rows}x{cols}.', output)
        elif ".sbs." in output:
            # Keep SBS format if it's already there and dimensions match
            if rows != 1 or cols != 2:
                # Convert from SBS to mosaic if dimensions don't match
                output = re.sub(r'\.sbs\.', f'.mosaic.{rows}x{cols}.', output)
        elif not re.search(r"\d+x\d+a[\d.]+", os.path.basename(output)):
            # Add appropriate pattern if none exists
            output_path = os.path.dirname(output) + "/" if os.path.dirname(output) else ""
            output_identifiers = os.path.basename(output).split(".")
            if rows == 1 and cols == 2:
                output = output_path + F'{".".join(output_identifiers[:-1])}.sbs.{output_identifiers[-1]}'
            else:
                output = output_path + F'{".".join(output_identifiers[:-1])}.mosaic.{rows}x{cols}.{output_identifiers[-1]}'
            
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Invalid filter views format: {e}. Use JSON array format like '[0, 1, 2, 3]'")

if len(input_streams) > rows * cols:
    input_streams = input_streams[:rows * cols]

# Validate SBS format requirements
if is_sbs_output or ".sbs." in output:
    if len(input_streams) != 2:
        raise ValueError(f"SBS format requires exactly 2 views, but {len(input_streams)} views were provided")
    print(f"Creating SBS output with {len(input_streams)} views")

# Apply aspect ratio padding if specified
if args.aspect_ratio:
    try:
        input_streams = [apply_aspect_ratio_padding(stream, args.aspect_ratio) for stream in input_streams]
        print(f"Applied aspect ratio padding: {args.aspect_ratio}")
    except ValueError as e:
        raise ValueError(f"Aspect ratio error: {e}")

if args.debug_text: 
    input_streams = [ffmpeg.drawtext(s, text=F"{i+1}", fontcolor="white", x="(w-text_w)/2",  y="(h-text_h)/2", fontsize=64) for i, s in enumerate(input_streams)]

# Handle single input vs multiple inputs differently
ffmpeg_output_kwargs = {
    'vcodec': 'libx264',
    'pix_fmt': 'yuv420p',
    'colorspace': 'bt709',
    'color_range': 'tv',
    'color_primaries': 'bt709',
    'color_trc': 'bt709',
    'profile:v': 'high',
    'crf': 18,
    'preset': 'medium',
}
if len(input_streams) == 1:
    # For single input, just output directly (no stacking needed)
    output_stream = ffmpeg.output(input_streams[0], output, **ffmpeg_output_kwargs)
else:
    # For multiple inputs, use xstack
    layout = build_ffmpeg_layout(rows, cols, len(input_streams))
    output_stream = ffmpeg \
        .filter(input_streams, 'xstack', inputs=F"{len(input_streams)}", layout=layout) \
        .output(output, **ffmpeg_output_kwargs)

if args.overwrite:
    output_stream = ffmpeg.overwrite_output(output_stream)

if args.dry:
    print(output_stream.compile())
    exit()

# Finished building the command --> run ffmpeg
output_stream.run()
