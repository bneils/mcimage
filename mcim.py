from PIL import Image

from colormath.color_diff_matrix import delta_e_cie1976 as delta_e
from colormath.color_objects import LabColor, sRGBColor
from colormath.color_conversions import convert_color

import numpy as np
from json import load
import argparse


def nearest_lab_color(color, colors):
    """Returns the index of the color in an array that is closest to a given color.
        Colors must be in raw LAB"""
    
    return np.argmin(delta_e(color, colors))



def pil2mcfunction(image):
    """Returns the Minecraft representation of an image as *.mcfunction.
       Output is executable within a datapack in-game. """

    if image.mode != "P":
        raise ValueError("mode of image isn't 'P', but instead '%s'" % image.mode)

    # Load and convert color palette of blocks to raw LAB
    with open('palette.json') as f:
        block_color_palette = load(f)
        
    for k, v in block_color_palette.items():
        lab = convert_color(sRGBColor(*v), LabColor)
        block_color_palette[k] = lab.lab_l, lab.lab_a, lab.lab_b
        
    # Load image's palette
    image_palette = np.array(image.getpalette()).reshape(256, 3)
    impal2colpal = np.zeros(256, dtype=np.uint8)

    # Find closest color in color_palette for each color in image_palette
    blocks, colors = zip(*block_color_palette.items())
    for i in range(256):
        color = convert_color(sRGBColor(*image_palette[i]), LabColor)
        impal2colpal[i] = nearest_lab_color(np.array([color.lab_l, color.lab_a, color.lab_b]), np.tile(colors, (1,1)))

    # Generate *.mcfunction file by using the palette
    ## Format indices as a matrix
    indices = list(image.getdata())
    mcfunc = 'gamerule maxCommandChainLength %d\n' % (len(indices) + 2)
    indices = [indices[i * image.width:(i + 1) * image.width] for i in range(image.height)]
    
    for r in range(image.height):
        for c in range(image.width):
            mcfunc += 'setblock ~%d ~%d ~ %s\n' % (-c, image.height - r - 1, blocks[impal2colpal[indices[r][c]]])
    
    return mcfunc + 'gamerule maxCommandChainLength 65536'
    
# Driver
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('fp', metavar='file-path', help='the file path of the image.')
    parser.add_argument('--dest', metavar='file-path', nargs='?', default='result.mcfunction')
    parser.add_argument('--scale', metavar='N', default=1, type=float)

    args = parser.parse_args()
    
    im = Image.open(args.fp).convert("P")  # convert to an indexed image
    im = im.resize((int(im.width * args.scale), int(im.height * args.scale)))

    if (im.width > 1500 or im.height > 300) and input("warning: the size of this image is big. It may take long to complete, do you want to proceed? (y/N) ") != 'y':
            quit()
    
    mcfunc = pil2mcfunction(im)
    with open(args.dest,'w') as f:
        f.write(mcfunc)
