# mcimage
A robust Minecraft image converter that generates *.mcfunction files that are executed in-game (within data-packs).
Images are limited to 256 colors and are dithered, as indexed images provide major speed boosts.

For all high resolution images due to in-game restrictions, it's required to scale the image, as each pixel is translated to a block in-game.

To use this, run 'py mcim.py' from the command-line and pass a file path to it.
Optional arguments include --dest, --scale, and --suppress.
