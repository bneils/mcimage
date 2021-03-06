#!/usr/bin/env python3
from colormath.color_diff_matrix import delta_e_cie1976 as delta_e
from colormath.color_objects import LabColor, sRGBColor
from colormath.color_conversions import convert_color

from PIL import Image
from numpy import array, argmin
from argparse import ArgumentParser

NORTH = 1
SOUTH = 2
EAST = 3
WEST = 4
UP = 5
DOWN = 6

# Sketch of omnidirectional scanning
#	~X ~Y ~Z
#	{0}, {1}
#
#	cardinal directions: 									modify {1} -> (rows - {1} - 1)
#		north: +X, +Y	~{0} ~{1} ~	.format(a,b)   ++ N     
#		south: -X, +Y	~{0} ~{1} ~ .format(-a,b)  -+ S
#		east : +Z, +Y   ~ ~{1} ~{0} .format(a,b)   ++ E
#		west : -Z, +Y	~ ~{1} ~{0} .format(-a,b)  -+ W
#	
#	up:
#		north: +X, -Z	~{0} ~ ~{1}	.format(a,-b)  +- N ^	
#		south: -X, +Z	~{0} ~ ~{1} .format(-a,b)  -+ S ^
#		east : +Z, +X	~{1} ~ ~{0} .format(a,b)   ++ E ^
#		west : -Z, -X	~{1} ~ ~{0} .format(-a,-b) -- W ^
#		
#	down:
#		north: +X, +Z	~{0} ~ ~{1} .format(a,b)   ++ N v
#		south: -X, -Z	~{0} ~ ~{1} .format(-a,-b) -- S v
#		east : +Z, -X	~{1} ~ ~{0} .format(a,-b)  +- E v
#		west : -Z, +X	~{1} ~ ~{0} .format(-a,b)  -+ W v
#		
#	N, E			 -> ++
#	E up, N down 	 -> ++
#	S, W 			 -> -+
#	S up, W down 	 -> -+
#	N up, E down	 -> +-
#	W up, S down	 -> --


format_funcs = [
	lambda a, b, rows: (a, rows - b - 1), 
	lambda a, b, rows: (a, b), 
	lambda a, b, rows: (-a, rows - b - 1), 
	lambda a, b, rows: (-a, b), 
	lambda a, b, rows: (a, -b), 
	lambda a, b, rows: (-a, -b)
]

format_strs = [
	'~{0} ~{1} ~',
	'~ ~{1} ~{0}',
	'~{0} ~ ~{1}',
	'~{1} ~ ~{0}'
]

format_map = {
	NORTH: {
		None: (format_funcs[0], format_strs[0]),
		UP:   (format_funcs[4], format_strs[2]),
		DOWN: (format_funcs[1], format_strs[2]),
	},
	
	SOUTH: {
		None: (format_funcs[2], format_strs[0]),
		UP:   (format_funcs[3], format_strs[2]),
		DOWN: (format_funcs[5], format_strs[2]),
	},
	
	EAST: {
		None: (format_funcs[0], format_strs[1]),
		UP:	  (format_funcs[1], format_strs[3]),
		DOWN: (format_funcs[4], format_strs[3]),
	},
	
	WEST: {
		None: (format_funcs[2], format_strs[1]),
		UP:   (format_funcs[5], format_strs[3]),
		DOWN: (format_funcs[3], format_strs[3]),
	},
}


# Parallel arrays holding corresponding block to LAB colors
colors = array(((4299.93, 80.91, 581.41), (4824.02, 2494.01, 3167.29), (5644.15, -0.02, -0.42), (3905.26, 610.6, 1937.03), (3871.01, -0.02, -0.29), (8143.55, -46.86, 219.5), (7050.42, -142.48, 2078.19), (6932.94, -139.05, 2556.93), (695.33, 97.13, -403.81), (1501.96, 88.34, -330.78), (2202.89, 1582.27, 684.56), (1491.15, 640.26, 701.77), (1262.05, 65.46, -279.27), (4656.42, -0.02, -0.34), (4656.42, -0.02, -0.34), (2983.06, 2862.87, -4568.25), (3857.38, 2394.74, -4332.7), (3348.22, 1753.06, -3756.4), (6653.04, 676.13, -4072.25), (3140.44, 1210.91, -1447.3), (3363.75, 2787.12, -4677.85), (8439.13, -144.3, 790.84), (4330.43, 409.54, 2032.29), (4781.75, 1722.49, 1473.21), (3242.49, 1208.53, 2079.96), (4176.44, 1198.15, 2160.6), (4679.99, 144.38, 1181.38), (5068.49, 975.58, 1947.2), (2815.31, 872.98, 1319.31), (3745.62, 1354.21, 2262.39), (4460.33, 2039.27, 3836.8), (8495.75, 26.45, 383.12), (5115.34, 2691.61, 4291.16), (7758.75, -187.6, 2156.51), (5046.49, 49.99, -36.06), (6614.19, 44.19, -634.83), (968.12, 49.83, 17.88), (4968.1, -0.02, -0.37), (4139.51, 954.84, 1800.03), (5342.58, -0.02, -0.4), (3691.12, 1284.76, 2601.38), (5012.24, 50.08, -36.12), (4721.89, 416.4, 2005.06), (5283.4, 2684.34, 4351.53), (7859.85, -287.34, 2115.75), (4741.28, -1565.2, -1399.87), (5591.81, -2111.63, -1155.59), (4728.31, -1535.33, -851.66), (4051.65, -170.12, -59.16), (5269.83, -2101.38, -1049.87), (2466.52, 333.16, 1346.99), (2406.66, 720.33, 1556.52), (2457.68, 748.0, 1666.78), (3816.09, -1562.56, 436.18), (5047.93, 182.47, 224.98), (5257.54, 198.01, 281.71), (5257.54, 198.01, 281.71), (5351.2, 163.57, 268.23), (5249.83, 164.52, 269.6), (8198.92, -3299.66, -565.84), (5728.94, -539.57, -131.44), (7317.04, -0.03, -0.54), (4560.44, 1040.06, 1960.39), (5146.44, 32.52, 11.12), (2323.44, -748.96, 957.75), (5146.44, 32.52, 11.12), (7003.13, -5266.44, 3934.74), (5491.41, -803.76, 356.71), (8226.16, -928.14, 2652.84), (8269.99, -1002.29, 2535.82), (6318.73, 16.61, 2184.75), (4088.87, -0.02, -0.3), (5105.06, -0.02, -0.38), (5727.43, 843.74, 2678.61), (8031.55, -20.05, 6105.91), (5765.11, -138.42, 721.75), (4900.23, 1408.47, 1527.54), (5369.35, 112.83, 92.28), (2795.78, -25.11, -256.71), (3694.47, -113.44, -212.82), (4009.4, -177.57, -231.23), (2337.88, 526.1, 654.64), (3198.25, -150.5, -231.6), (3869.84, -1402.78, 2463.71), (4806.51, -1701.92, 3180.07), (5557.22, -1812.42, 3123.19), (3668.02, -848.07, 1977.98), (4443.3, -1837.01, 3346.82), (5758.08, 182.49, 4454.06), (6631.81, 1982.72, 5592.55), (8299.36, -0.03, -0.61), (5480.4, 145.24, 208.14), (6565.39, 1297.06, 4942.84), (2762.82, 543.3, -416.59), (3405.26, 626.17, -472.8), (3127.51, 987.11, 1459.86), (3299.64, 270.93, 2356.17), (5009.59, 986.33, 2404.9), (5265.7, 1180.39, 2269.37), (3369.32, 1444.24, -3777.77), (4748.28, 104.0, -1161.05), (5476.6, -409.72, -3339.67), (6688.93, -1640.8, -2161.23), (6328.53, -756.93, -2477.0), (4813.5, 719.56, -1309.39), (6546.42, -1472.4, -2571.28), (5251.81, -164.83, 468.67), (6221.97, -96.92, 268.98), (6485.85, -633.01, -264.46), (4847.37, 879.86, 820.78), (5824.6, -130.16, 365.0), (6123.4, -3753.74, 4852.51), (6808.56, -3535.73, 5198.81), (7199.42, -2583.17, 5293.04), (4796.95, -1331.08, 2866.55), (6646.61, -3821.04, 5297.04), (5217.89, 600.89, 2088.26), (4794.76, 1247.43, 2032.52), (4541.33, 5057.93, -2817.26), (5354.55, 4776.73, -2778.02), (5817.01, 4597.84, -2386.75), (4643.73, 2390.11, -22.91), (5111.74, 5151.73, -2913.08), (3976.2, 2734.67, 3017.21), (5623.42, -2287.8, 4373.9), (4927.74, -655.2, 1054.07), (5060.21, -463.14, 689.74), (7589.08, 45.45, 544.59), (2862.6, 2309.3, 1273.07), (1609.57, 1111.53, 200.69), (3690.94, 1927.39, 1053.25), (2918.44, 3392.13, 2845.4), (3127.51, 987.11, 1459.86), (4022.49, 482.11, 2082.24), (5303.02, 493.65, 2624.93), (5614.5, 510.95, 2795.87), (4516.22, -0.02, -0.33), (3252.46, 73.28, 25.84), (3290.58, 73.06, 25.75), (4339.44, -0.02, -0.32), (850.33, 673.12, -855.28), (5685.35, 3983.33, 5190.44), (6289.73, 2675.83, 5301.93), (5958.33, -486.94, 2613.21), (4595.27, 2523.35, 3442.25), (6224.47, 3657.38, 5516.84), (7048.16, 434.11, -3305.35), (5744.78, 4102.73, -61.12), (6902.99, 2727.3, -240.96), (6990.55, 2892.08, -104.41), (4553.84, 2947.52, 1453.04), (6756.19, 3422.47, -16.52), (5560.99, -80.62, 23.42), (7468.27, -13.74, -53.78), (5023.93, 1479.35, 1500.34), (5975.3, -1678.16, -272.61), (6377.98, -2176.07, -18.26), (5595.22, 2299.31, 4763.0), (3414.65, 4344.94, -4526.42), (4194.89, 4467.63, -4320.82), (3678.81, 3868.28, -3881.43), (3858.35, 1973.76, -34.0), (3896.16, 4631.58, -4556.91), (5762.12, 2109.97, -1426.32), (5868.04, 2008.17, -1361.8), (8594.4, 69.99, 350.88), (8619.87, 55.16, 298.77), (4156.49, 4667.99, 4015.65), (4873.11, 891.15, 340.74), (3598.33, 3770.73, 2629.75), (4281.35, 3922.24, 2587.43), (4553.64, 4134.69, 2798.24), (4743.75, 4939.76, 3468.43), (1958.69, 2249.69, 1748.77), (5314.81, 2678.06, 4327.82), (5208.4, 2665.55, 4328.79), (3971.94, 2902.54, 2332.88), (3982.07, 4077.79, 3007.59), (7902.11, -221.4, 1996.93), (7780.71, -231.84, 2186.13), (7473.84, -925.57, 123.85), (2202.83, 823.09, 279.84), (3565.49, 182.29, 1098.4), (4143.1, 148.07, 941.84), (6365.2, -0.03, -0.47), (6654.27, -0.03, -0.49), (9281.3, -139.59, -49.54), (3159.49, 570.28, 930.89), (7297.61, -1124.15, 4888.46), (2193.68, 714.0, 1557.34), (3887.32, 675.32, 2115.43), (4048.68, 724.65, 2222.75), (5274.99, -0.02, -0.39), (5148.9, 49.74, -35.89), (4946.26, 2650.02, 2918.8), (4817.43, 2381.19, 3108.9), (6982.04, -73.2, 2760.74), (6828.77, -39.09, 2645.89), (3667.21, 415.21, 1670.76), (2471.41, 654.68, 1578.8), (5749.4, 795.73, 2705.56), (5469.05, 1032.96, 2486.4), (6072.19, 461.22, 3020.14), (5572.51, 476.4, 2786.33), (4182.15, 532.93, 2189.44), (3855.35, 551.45, 2070.03), (4719.87, 1816.73, 2202.75), (6872.88, -1536.95, 4537.04), (8051.05, -157.33, -103.04), (8497.59, -57.24, -20.73), (7888.58, -847.07, 189.96), (7195.74, 735.23, 1098.73), (8760.73, -85.12, -30.5), (7279.3, 1156.98, 6195.82), (7723.2, -153.16, 5965.99), (7607.15, 353.36, 4809.05), (5881.92, 1092.41, 4709.4), (7809.01, 488.68, 6391.93)))
blocks = ('acacia_log', 'acacia_planks', 'andesite', 'barrel', 'bedrock', 'birch_log', 'birch_log[axis=z]', 'birch_planks', 'black_concrete', 'black_concrete_powder', 'black_glazed_terracotta', 'black_terracotta', 'black_wool', 'blast_furnace', 'blast_furnace[facing=east]', 'blue_concrete', 'blue_concrete_powder', 'blue_glazed_terracotta', 'blue_ice', 'blue_terracotta', 'blue_wool', 'bone_block', 'bookshelf', 'bricks', 'brown_concrete', 'brown_concrete_powder', 'brown_glazed_terracotta', 'brown_mushroom_block', 'brown_terracotta', 'brown_wool', 'carved_pumpkin', 'chiseled_quartz_block', 'chiseled_red_sandstone', 'chiseled_sandstone', 'chiseled_stone_bricks', 'clay', 'coal_block', 'coal_ore', 'coarse_dirt', 'cobblestone', 'composter', 'cracked_stone_bricks', 'crafting_table', 'cut_red_sandstone', 'cut_sandstone', 'cyan_concrete', 'cyan_concrete_powder', 'cyan_glazed_terracotta', 'cyan_terracotta', 'cyan_wool', 'dark_oak_log', 'dark_oak_log[axis=z]', 'dark_oak_planks', 'dark_prismarine', 'dead_brain_coral_block', 'dead_bubble_coral_block', 'dead_fire_coral_block', 'dead_horn_coral_block', 'dead_tube_coral_block', 'diamond_block', 'diamond_ore', 'diorite', 'dirt', 'dispenser', 'dried_kelp_block', 'dropper', 'emerald_block', 'emerald_ore', 'end_stone', 'end_stone_bricks', 'fletching_table', 'furnace', 'furnace[facing=south]', 'glowstone', 'gold_block', 'gold_ore', 'granite', 'gravel', 'gray_concrete', 'gray_concrete_powder', 'gray_glazed_terracotta', 'gray_terracotta', 'gray_wool', 'green_concrete', 'green_concrete_powder', 'green_glazed_terracotta', 'green_terracotta', 'green_wool', 'hay_block', 'honeycomb_block', 'iron_block', 'iron_ore', 'jack_o_lantern', 'jigsaw', 'jigsaw[facing=north]', 'jukebox', 'jungle_log', 'jungle_log[axis=z]', 'jungle_planks', 'lapis_block', 'lapis_ore', 'light_blue_concrete', 'light_blue_concrete_powder', 'light_blue_glazed_terracotta', 'light_blue_terracotta', 'light_blue_wool', 'light_gray_concrete', 'light_gray_concrete_powder', 'light_gray_glazed_terracotta', 'light_gray_terracotta', 'light_gray_wool', 'lime_concrete', 'lime_concrete_powder', 'lime_glazed_terracotta', 'lime_terracotta', 'lime_wool', 'loom', 'loom[facing=south]', 'magenta_concrete', 'magenta_concrete_powder', 'magenta_glazed_terracotta', 'magenta_terracotta', 'magenta_wool', 'magma_block', 'melon', 'mossy_cobblestone', 'mossy_stone_bricks', 'mushroom_stem', 'netherrack', 'nether_bricks', 'nether_quartz_ore', 'nether_wart_block', 'note_block', 'oak_log', 'oak_log[axis=z]', 'oak_planks', 'observer', 'observer[facing=east]', 'observer[facing=south]', 'observer[facing=up]', 'obsidian', 'orange_concrete', 'orange_concrete_powder', 'orange_glazed_terracotta', 'orange_terracotta', 'orange_wool', 'packed_ice', 'pink_concrete', 'pink_concrete_powder', 'pink_glazed_terracotta', 'pink_terracotta', 'pink_wool', 'polished_andesite', 'polished_diorite', 'polished_granite', 'prismarine', 'prismarine_bricks', 'pumpkin', 'purple_concrete', 'purple_concrete_powder', 'purple_glazed_terracotta', 'purple_terracotta', 'purple_wool', 'purpur_block', 'purpur_pillar', 'quartz_block', 'quartz_pillar', 'redstone_block', 'redstone_ore', 'red_concrete', 'red_concrete_powder', 'red_glazed_terracotta', 'red_mushroom_block', 'red_nether_bricks', 'red_sand', 'red_sandstone', 'red_terracotta', 'red_wool', 'sand', 'sandstone', 'sea_lantern', 'smithing_table', 'smoker', 'smoker[facing=east]', 'smooth_stone', 'smooth_stone_slab[type=double]', 'snow_block', 'soul_sand', 'sponge', 'spruce_log', 'spruce_log[axis=z]', 'spruce_planks', 'stone', 'stone_bricks', 'stripped_acacia_log', 'stripped_acacia_log[axis=z]', 'stripped_birch_log', 'stripped_birch_log[axis=z]', 'stripped_dark_oak_log', 'stripped_dark_oak_log[axis=z]', 'stripped_jungle_log', 'stripped_jungle_log[axis=z]', 'stripped_oak_log', 'stripped_oak_log[axis=z]', 'stripped_spruce_log', 'stripped_spruce_log[axis=z]', 'terracotta', 'wet_sponge', 'white_concrete', 'white_concrete_powder', 'white_glazed_terracotta', 'white_terracotta', 'white_wool', 'yellow_concrete', 'yellow_concrete_powder', 'yellow_glazed_terracotta', 'yellow_terracotta', 'yellow_wool')


def pil2mcfunction(image, directions=NORTH, fill_compression=False):
	"""Returns the Minecraft representation of an image as a *.mcfunction.
	   Output is executable within a data-pack in-game. """
	
	assert image.mode == "P", "error: mode of image isn't 'P', but instead '%s'" % image.mode	
	
	if type(directions) == int:
		directions = (directions,)
	else:
		assert len(directions) <= 2, "Too many directions specified"
		
	directions = list(sorted(directions))
	format_func, format_str = format_map[directions[0]][directions[1] if len(directions) == 2 else None]
	
	# Find the closest color to colors in the image's palette to block colors
	impal2colpal = [argmin(delta_e(array(convert_color(sRGBColor(*rgb), LabColor).get_value_tuple()),
					colors))
			for rgb in array(image.getpalette()).reshape(256, 3)]
	
	# Generate *.mcfunction file by using the palette
	pixel_indices = list(image.getdata())

	# Use run-length encoding
	if fill_compression:
		## Sacrifices a little speed for space
		func_body = []
		for r in range(image.height):
			streak_block = last_pos = None
			streak = False
			for c in range(image.width):
				# Retrieve the current color index, and find what block its color is closest to
				block = blocks[impal2colpal[pixel_indices[r * image.width + c]]]
				
				# Retrieve where to place the block
				pos = format_str.format(*format_func(c, r, image.height))
				
				# See if the streak continues or breaks
				if streak_block != block:
					# Determine how to place the block
					if streak:
						func_body.append(f'fill {block_pos} {last_pos} {streak_block}')
					elif last_pos:
						func_body.append(f'setblock {last_pos} {streak_block}')
					else:
						# First element in sequence
						func_body.append(f'setblock {pos} {block}')
		
					# Reset streak and blocks
					streak = False
					block_pos = last_pos = pos
					streak_block = block
				else:
					streak = True
					last_pos = pos
			
			# If a streak persists past the loop
			if streak:
				func_body.append(f'fill {block_pos} {pos} {block}')
			# If there wasn't a streak, but just a block waiting for a streak to occur
			elif last_pos == block_pos:
				func_body.append(f'setblock {last_pos} {block}')
		
		return f'gamerule maxCommandChainLength {len(func_body) + 10}\n' + \
				'tellraw @a "Pending extreme lag..."\n' + '\n'.join(func_body) + '\ngamerule maxCommandChainLength 65536'
	
	else:
		format_str = "setblock " + format_str + " {2}\n"
		
		# If the programmer doesn't want compression due to the fill command messing up the build (default)
		return f'gamerule maxCommandChainLength {len(pixel_indices) + 10}\ntellraw @a "Pending extreme lag..."\n' + \
			''.join([format_str.format(*format_func(c, r, image.height), blocks[impal2colpal[pixel_indices[r * image.width + c]]])
			for c in range(image.width) for r in range(image.height)]) + 'gamerule maxCommandChainLength 65536'
	
# Driver
if __name__ == "__main__":
	# Argument parsing
	parser = ArgumentParser()
	parser.add_argument('fp', metavar='file-path', help='the file path of the image')
	parser.add_argument('-d', '--dest', metavar='file-path', default='image.mcfunction', help='what to save the file as')
	parser.add_argument('-s', '--scale', metavar='N', default=1.0, type=float, help='a decimal to appropriately scale an image')
	parser.add_argument('-q', '--suppress', action='store_true', help="won't annoy users about large images")
	parser.add_argument('-o', '--orientation', metavar='D', default='N', help="specify in what direction to make the image (e.g. N+U). Allowed: N, E, S, W, U, D")
	parser.add_argument('-c', '--compress', action='store_true', help="compress the image into fill commands (problematic for large images, due to unloaded chunks)")
	
	args = parser.parse_args()
	
	directions_alias = {'N':NORTH, 'S':SOUTH, 'E':EAST, 'W':WEST, 'U':UP, 'D':DOWN}
	directions = [directions_alias[c] for c in args.orientation.upper()]
	assert len(directions) <= 2, "Too many directions specified."
	
	# Convert to an indexed image (w/ palette)
	im = Image.open(args.fp).convert("P")
	im = im.resize((int(im.width * args.scale), int(im.height * args.scale)))
	
	# For large images, ask them if they'd like to continue
	if not args.suppress and im.width * im.height >= 300_000:
		if input("This image is big (%d >= 300000), it's suggested that you scale it. Do you still want to proceed? (y/N) " % (im.width * im.height)) != 'y':
			print("Aborted.")
			quit()
	
	result = pil2mcfunction(im, directions, args.compress)
	
	# Write the file
	with open(args.dest, 'w') as f:
		f.write(result)
