# mcimage
Converts PIL images into *.mcfunction files that can be executed in-game.

To use this, run 'py mcim.py' from the command-line and pass a file path to it.
Optional arguments include --dest, --scale, --suppress, and --progress-bar.

For all high resolution images, it is required to scale the image as each pixel is translated to a block in-game and there are in-game restrictions.
Speeds may vary but it's generally expected to execute within a second.

Images are limited to 256 colors and are dithered, as indexed images provide major speed boosts.