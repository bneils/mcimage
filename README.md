# mcimage
Converts PIL images into *.mcfunction files that can be executed in-game.

To use this, run mcim.py from the command-line and pass a file path to it.
Optional arguments include '--dest' and '--scale'.

For all high resolution images, it is required to scale the image as each pixel is translated to a block.
Speeds may vary but is generally expected to execute within a second.
