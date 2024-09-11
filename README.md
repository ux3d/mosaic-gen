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
