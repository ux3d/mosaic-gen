# Mosaic Generator based on FFMPEG

This is a convenience wrapper for FFMPEG to generate multiview mosaic videos

## Installation

1. Clone the Git Repository to a local directory

2. Ensure you have Python 3.11+ installed

3. Setup a virtual environment

```sh
python3 -m venv venv
```

4. Activate the environment

```sh
source venv/bin/activate
```

5. Install the dependencies

```sh
pip install argparse ffmpeg-python
```

## Run the Script

Usage:

```
usage: mosaicgen.py [-h] -i INPUTS [INPUTS ...] -o OUTPUT [--debug-text] [-y] [--dry]

Combine input video / images to a mosaic for use on a 3D Global multiview monitor

options:
  -h, --help            show this help message and exit
  -i INPUTS [INPUTS ...], --inputs INPUTS [INPUTS ...]
                        List of files to combine to a mosaic
  -o OUTPUT, --output OUTPUT
                        Name or path to the output file. If the file name doesn't contain a mosaic pattern, it will be added to the file before the last dot character
                        (e.g. out.mosaic.3x3.mp4). If it contains a mosaic pattern it will be used to determine the ROWS and COLUMNS of the mosaic. If the number of input files exceeds ROWS * COLUMNS, some input files will not be
                        considered in the final output.
  --debug-text          Display a text overlay numbering the views
  -y, --overwrite       Overwrite output files
  --dry                 Print the ffmpeg command instead of running it
```

For example to generate a 4x4 grid on input files from some directory (which can also be more or less than 16 files), run a command similar to the following:

```sh
python mosaicgen.py -i /Path/To/Input.MV.*.mp4  -o out.mosaic.4x4.mp4 -y
```

> :warning: **Don't use quotes when specifying the input with a glob (aka wildcard) pattern, this will break the wildcard resolution:** `python mosaicgen.py -i "/Path/To/Input.MV.*.mp4"  -o out.mosaic.4x4.mp4 -y`

## IMPORTANT NOTE

As of right now (23.04.2025) the script seams to be broken on Windows and Linux (tested with WSL Ubuntu). It is not working properly with wildcards in the input property. This:

```sh
python mosaicgen.py -i /Path/To/Input.MV.*.mp4  -o out.mosaic.4x4.mp4 -y
```

does not work right now. To fix it you have to go into "mosaicgen.py" and add something like this (after line 19):

```python
inputs = [
"./input/0000-0388MV.01.mp4",
"./input/0000-0388MV.02.mp4",
"./input/0000-0388MV.03.mp4",
"./input/0000-0388MV.04.mp4",
"./input/0000-0388MV.05.mp4",
"./input/0000-0388MV.06.mp4",
"./input/0000-0388MV.07.mp4",
"./input/0000-0388MV.08.mp4",
"./input/0000-0388MV.09.mp4",
"./input/0000-0388MV.10.mp4",
"./input/0000-0388MV.11.mp4",
"./input/0000-0388MV.12.mp4",
"./input/0000-0388MV.13.mp4",
"./input/0000-0388MV.14.mp4",
"./input/0000-0388MV.15.mp4",
"./input/0000-0388MV.16.mp4",
]
```

Afterwards you can run the command from above without any issues. (The input property from the command is now completely ignored though).
