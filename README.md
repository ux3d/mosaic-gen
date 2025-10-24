# Mosaic Generator based on FFMPEG

This is a convenience wrapper for FFMPEG to generate multiview mosaic videos

## Installation

1. Clone the Git Repository to a local directory

2. Ensure you have Python 3.11+ installed

3. Setup a virtual environment

```sh
python3 -m venv venv
```

or

```sh
python -m venv venv
```

4. Activate the environment

Linux / MacOS:

```sh
source venv/bin/activate
```

Windows:

```sh
venv\Scripts\activate
```

5. Install the dependencies

```sh
python -m pip  install -r requirements.txt
```

## For Videos

Usage:

```
usage: mosaicgen_videos.py [-h] -i INPUTS [INPUTS ...] -o OUTPUT [--debug-text] [-y] [--dry]

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
python mosaicgen_videos.py -i /Path/To/Input.MV.*.mp4  -o out.mosaic.4x4.mp4 -y
```

> [!CAUTION] > **Don't use quotes when specifying the input with a glob (aka wildcard) pattern, this will break the wildcard resolution:**
>
> ```diff
> - python mosaicgen_videos.py -i "/Path/To/Input.MV.*.mp4"  -o out.mosaic.4x4.mp4 -y
> + python mosaicgen_videos.py -i /Path/To/Input.MV.*.mp4  -o out.mosaic.4x4.mp4 -y
> ```

> [!TIP]
> If your shell doesn't support wildcard patterns or they don't work for you, you can specify the inputs as a list of files (This seems to be the case on windows.):
>
> `python mosaicgen_videos.py -i ./input/0000-0388MV.01.mp4 ./input/0000-0388MV.02.mp4 ./input/0000-0388MV.03.mp4 ./input/0000-0388MV.04.mp4 -o out.mosaic.2x2.mp4 -y`

## For Images

The output folder has to be created before running the script.

Run:
`python .\main_convert_images.py -i .\input -o .\output`

Command line options:
`--input DIR` : input directory of image files
`--output DIR` : output directory of mosaic image files
