#=Imports==========================================================================================================

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import os
import sys

app = Ursina(title='mClone', icon=os.path.join('textures', 'mcicon.ico'))

#=Global=Vars======================================================================================================

global player, current_block, flying, escaped, gms, hotbar_data, grid, current_world, boxes, block_tags

flying = False
escaped = False
gms = False
hotbar_data = {}
grid = []
boxes = []

current_world = '.default'

block_tags = {
	'transparent': [7, 8],
	'unbreakable': [0],
	'gravity': [9]
}

#=Various=functions================================================================================================

def list_items_equal(main_list):
	first_item = main_list[0]
	for sublist in main_list[1:]:
		if sublist != first_item:
			return False
	return True

def check_if_surrounded(y, x, z):
	surr_blocks = []

	surr_blocks.append(grid[y + 1][x][z] if y < 14 else 1)
	surr_blocks.append(grid[y - 1][x][z] if y > 0 else 1)
	surr_blocks.append(grid[y][x + 1][z] if x < 14 else 1)
	surr_blocks.append(grid[y][x - 1][z] if x > 0 else 1)
	surr_blocks.append(grid[y][x][z + 1] if z < 14 else 1)
	surr_blocks.append(grid[y][x][z - 1] if z > 0 else 1)

	for b in surr_blocks:
		if b in block_tags['transparent']:
			return False

	return '_' not in surr_blocks

def escape():
	global escaped, mouse, player

	escaped = not escaped
	mouse.locked = not escaped
	mouse.visible = escaped
	player.enabled = not escaped
	enable_UI(escaped)

#=World=loading====================================================================================================

def load_world(world):
	world_data = []
	player_coords = [[0, 0, 0], [0, 0]]

	try:
		world_file = open(os.path.join('worlds', world, 'world.txt'), 'r')
		player_file = open(os.path.join('worlds', world, 'player.txt'), 'r')

	except FileNotFoundError:
		return 'error'

	for ln in world_file:
		line = ln.strip()

		if line == '>':
			world_data.append([])

		else:
			if line[0] == '*':
				if line[1] == '*':
					lines = []
					for x in range(15):
						lines.append(line[2] * 15)
					line = lines
				else:
					line = line[1] * 15

			if isinstance(line, str):
				world_data[-1].append(line)
			else:
				world_data[-1].extend(line)

	for ln in player_file:
		line = ln.strip()
		if line[0] == '@':
			player_coords[0] = [float(coord) for coord in line[1:].split(' ')]
			if player_coords[0][0] < -60:
				player_coords = [[0, 7, 7], [0, 0]]
		if line[0] == '^':
			player_coords[1] = [float(dir) for dir in line[1:].split(' ')]

	return (world_data, player_coords)

#=World=saving=====================================================================================================

def save_world(world):
	try:
		os.mkdir(os.path.join('worlds', world))
	except FileExistsError:
		pass

	world_file = open(os.path.join('worlds', world, 'world.txt'), 'w')
	player_file = open(os.path.join('worlds', world, 'player.txt'), 'w')

	data = ''
	for y in grid:
		data += '>\n'
		if list_items_equal(y):
			data += f'**{y[0][0]}\n'
		else:
			for x in y:
				if list_items_equal(x):
					data += f'*{x[0]}\n'
				else:
					for z in x:
						data += str(z)
					data += '\n'

	pdata = f'@{player.y} {player.x} {player.z}\n'
	pdata += f'^{camera.rotation_x} {camera.rotation_y}'

	world_file.write(data)
	player_file.write(pdata)

#=TCButton=class===================================================================================================

class TCButton(Button):
	def __init__(self, model, block_data, position=(0, 0, 0), **kwargs):
		super().__init__(model=model, collider='box', position=position, **kwargs)
		self.single_t = False

		self.block_id = block_data[0]
		self.block_name = block_data[1]

		self.broken = 0
		self.moh = block_data[2]

		if self.block_id  not in block_tags['transparent']:
			self.model = f'textures/{self.block_name}_block.glb'
		else:
			self.texture = self.block_name

	def get_data(self):
		return [self.block_id, self.block_name, self.moh]

#=First=Objects====================================================================================================

Sky(texture='mclone_sky')

def load_player():
	global current_world

	c = load_world(current_world)[1][0]
	d = load_world(current_world)[1][1]

	player = FirstPersonController(y=c[0], x=c[1], z=c[2], scale=(0.8, 0.8, 0.8))
	player.jump_height = 1.255
	player.cursor.color = color.black
	player.cursor.model = 'circle'
	#player.collider = BoxCollider(player, Vec3(0, 1, 0), Vec3(1, 2, 1))

	return player

#=Block=definitions================================================================================================

txz = ['brick', 'grass', 'dirt', 'wood', 'glass', 'stone', 'plank', 'grass-side', 'wood-top', 'bedrock', 'leaves', 'sand']

blocks = [
	# block id, name, hardness
	[0, 'bedrock', 1],
	[1, 'grass', 2],
	[2, 'dirt', 2],
	[3, 'stone', 5],
	[4, 'brick', 4],
	[5, 'plank', 3],
	[6, 'wood', 3], 
	[7, 'leaves', 1],
	[8, 'glass', 1],
	[9, 'sand', 2]
]
current_block = blocks[1]

#=UI=classes=======================================================================================================

class Prompt(InputField):
	def __init__(self, prompt, **kwargs):
		super().__init__(default_value=prompt, parent=camera.ui, 
				scale_y=0.05, scale_x=0.25, y=-0.4,
				limit_content_to='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_ ', **kwargs)

class UIbutton(Button):
	def __init__(self, name, sy, **kwargs):
		super().__init__(color=color.white, model='plane', texture=name, scale_x=0.2, scale_z=0.066, x=0, y=sy, rotation_x=-90,
			 enabled=False, parent=camera.ui, on_click=self.event, **kwargs)
		self.name = name

	def event(self):
		global current_world

		if self.name == 'exit':
			application.quit()

		if self.name == 'save':
			if current_world == '.default':
				nwn_prompt = Prompt('New world')

				def enter():
					global current_world

					current_world = nwn_prompt.text
					destroy(enter_button)
					destroy(nwn_prompt)

					save_world(current_world)

				enter_button = Button(
					color=color.white, model='plane', texture='enter', parent=camera.ui, 
					scale_z=0.05, scale_x=0.15, y=-0.4, x=0.2, rotation_x=-90, 
					on_click=enter
				)

			else:
				save_world(current_world)

		if self.name == 'load':
			load_prompt = Prompt('Load world')

			def enter():
				global current_world, boxes, escaped, player

				current_world = load_prompt.text
				for box in boxes:
					destroy(box)
				destroy(enter_button)
				destroy(load_prompt)
				escape()

				spawn_blocks()
				player = load_player()

			enter_button = Button(
					color=color.white, model='plane', texture='enter', parent=camera.ui, 
					scale_z=0.05, scale_x=0.15, y=-0.4, x=0.2, rotation_x=-90, 
					on_click=enter
			)

#=GUI==============================================================================================================

curr_indicator = Text(text=current_block[1], origin=(0, 0), x=0, y=-0.45, color=color.black)
hotbar = Text(text=str(hotbar_data), origin=(0, 0), x=0, y=-0.4, color=color.black)

if not gms:
	for b in blocks:
		pass

save_button = UIbutton('save', 0.1)
load_button = UIbutton('load', 0)
exit_button = UIbutton('exit', -0.1)

sy = 0.4
world_display = [Text(color=color.blue, text='Worlds:', x=-0.8, y=0.45, visible=False)]
for world in os.listdir('worlds'):
	if world[0] != '.':
		world_display.append(Text(color=color.black, text=world, x=-0.8, y=sy, visible=False))
		sy -= 0.05

def enable_UI(thebool):
	save_button.enabled = thebool
	load_button.enabled = thebool
	exit_button.enabled = thebool

	for name in world_display:
		name.visible = thebool

#=Spawn=Blocks=====================================================================================================

def spawn_blocks():
	global boxes
	wd = load_world(current_world)[0]

	boxes = []
	for i in range(15):
		for j in range(15):
			for k in range(15):
				if wd[i][j][k].isnumeric():
					box = TCButton(color=color.white, model='cube', position=(j,-i,k), block_data=blocks[int(wd[i][j][k])], parent=scene, origin_y=0.5)
					boxes.append(box)

#=Inputs===========================================================================================================

def input(key):
	global current_block
	global flying
	global escaped

	if key == 'escape':
		escape()

	if not escaped:
		for box in boxes:
			if box.hovered:
				if key == 'right mouse down':
					new_block_pos = box.position + mouse.normal
					X = new_block_pos[0]
					Y = new_block_pos[1]
					Z = new_block_pos[2]

					if Y <= 0 and Y > -15 and X >= 0 and X < 15 and Z >= 0 and Z < 15:
						new_box = TCButton(color=color.white, model='cube', position=new_block_pos, block_data=current_block, parent=scene, origin_y=0.5)
						boxes.append(new_box)
	
				if 'left mouse' in key and key != 'left mouse up':
					if box.block_id not in block_tags['unbreakable']:
						if gms:
							box.broken += 1
							if box.broken >= box.moh:
								if gms:
									if len(hotbar_data.keys()) <= 10:
										if box.get_data()[1] not in hotbar_data.keys():
											hotbar_data[box.get_data()[1]] = 1
										else:
											hotbar_data[box.get_data()[1]] += 1

								boxes.remove(box)
								destroy(box)
						else:
							boxes.remove(box)
							destroy(box)
	
				if key == 'middle mouse down':
					current_block = box.get_data()
					curr_indicator.text = current_block[1]				

		if not gms and key == 'f':
			if flying:
				player.gravity = 1
				flying = False
			else:
				player.gravity = 0
				flying = True

		if key.isnumeric() and int(key) <= len(blocks):
			current_block = blocks[int(key)]
			curr_indicator.text = current_block[1]
	
	if key == 'g':
		print(grid)
	
#=Update===========================================================================================================

def update():
	global hotbar_data
	global grid

	if not escaped:

		hotbar.text = str(hotbar_data)
		grid = [[['_' for z in range(15)] for x in range(15)] for y in range(15)]

		for box in boxes:
			grid[int(-box.y)][int(box.x)][int(box.z)] = box.block_id

		for box in boxes:
			i = -int(box.y)
			j = int(box.x)
			k = int(box.z)

			if box.block_id in block_tags['gravity'] and grid[i + 1][j][k] == '_':
					box.y -= 0.25

			box.visible = not check_if_surrounded(i, j, k)

		if flying:
			if held_keys['space']:
				player.y += time.dt * 5

			if held_keys['left shift']:
				player.y -= time.dt * 5

	else:
		for field in [e for e in scene.entities if isinstance(e, InputField)]:
			if len(field.text) > 12:
				field.text = field.text[:12]

#=Run==============================================================================================================

#os.chdir(os.path.dirname(os.path.abspath(sys.argv[0]))

spawn_blocks()
player = load_player()
app.run()

#==================================================================================================================