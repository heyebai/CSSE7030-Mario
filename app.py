"""
Simple 2d world where the player can interact with the items in the world.
"""

__author__ = ""
__date__ = ""
__version__ = "1.1.0"
__copyright__ = "The University of Queensland, 2019"

import math
import tkinter as tk

from typing import Tuple, List

import pymunk

from game.block import Block, MysteryBlock
from game.entity import Entity, BoundaryWall
from game.mob import Mob, CloudMob, Fireball
from game.item import DroppedItem, Coin
from game.view import GameView, ViewRenderer
from game.world import World
from tkinter import messagebox
from tkinter import filedialog
from game.util import get_collision_direction
import time
from PIL import Image
from PIL import ImageTk

from level import load_world, WorldBuilder
from player import Player

BLOCK_SIZE = 2 ** 4
MAX_WINDOW_SIZE = (1080, math.inf)

GOAL_SIZES = {
    "flag": (0.2, 9),
    "tunnel": (2, 2)
}

BLOCKS = {
    '#': 'brick',
    '%': 'brick_base',
    '?': 'mystery_empty',
    '$': 'mystery_coin',
    '^': 'cube',
    'b': 'bounce_block',
    'I':'flag',
    '=':'tunnel',
    'S':'switch'
}

ITEMS = {
    'C': 'coin',
    '*': 'star',
    'F': 'flower'
}

MOBS = {
    '&': "cloud",
    '@': 'mushroom'
}

step_count=1
count=0

def create_block(world: World, block_id: str, x: int, y: int, *args):
    """Create a new block instance and add it to the world based on the block_id.

    Parameters:
        world (World): The world where the block should be added to.
        block_id (str): The block identifier of the block to create.
        x (int): The x coordinate of the block.
        y (int): The y coordinate of the block.
    """
    block_id = BLOCKS[block_id]
    if block_id == "mystery_empty":
        block = MysteryBlock()
    elif block_id == "mystery_coin":
        block = MysteryBlock(drop="coin", drop_range=(3, 6))
    elif block_id=='tunnel':
        block=Tunnel()
    elif block_id=='flag':
        block=Flagpole()
    elif block_id=='switch':
        block=Switch(radius=3)
    elif block_id=='bounce_block':
        block=Bounce()
    else:
        block = Block(block_id)

    world.add_block(block, x * BLOCK_SIZE, y * BLOCK_SIZE)



def create_item(world: World, item_id: str, x: int, y: int, *args):
    """Create a new item instance and add it to the world based on the item_id.

    Parameters:
        world (World): The world where the item should be added to.
        item_id (str): The item identifier of the item to create.
        x (int): The x coordinate of the item.
        y (int): The y coordinate of the item.
    """
    item_id = ITEMS[item_id]
    if item_id == "coin":
        item = Coin()
    elif item_id=='star':
        item=Star()
    elif item_id=='flower':
        item=Flower()
    else:
        item = DroppedItem(item_id)

    world.add_item(item, x * BLOCK_SIZE, y * BLOCK_SIZE)


def create_mob(world: World, mob_id: str, x: int, y: int, *args):
    """Create a new mob instance and add it to the world based on the mob_id.

    Parameters:
        world (World): The world where the mob should be added to.
        mob_id (str): The mob identifier of the mob to create.
        x (int): The x coordinate of the mob.
        y (int): The y coordinate of the mob.
    """
    mob_id = MOBS[mob_id]
    if mob_id == "cloud":
        mob = CloudMob()
    elif mob_id == "fireball":
        mob = Fireball()
    elif mob_id =='mushroom':
        mob=Mushroom(world)
    elif mob_id=='fire':
        mob=Fire()
    else:
        mob = Mob(mob_id, size=(1, 1))

    world.add_mob(mob, x * BLOCK_SIZE, y * BLOCK_SIZE)


def create_unknown(world: World, entity_id: str, x: int, y: int, *args):
    """Create an unknown entity."""
    world.add_thing(Entity(), x * BLOCK_SIZE, y * BLOCK_SIZE,
                    size=(BLOCK_SIZE, BLOCK_SIZE))


BLOCK_IMAGES = {
    "brick": "brick",
    "brick_base": "brick_base",
    "cube": "cube",
    'bounce_block': 'bounce_block',
    'flag':'flag',
    'tunnel':'tunnel',
    'switch':'switch'
}

ITEM_IMAGES = {
    
    'star': 'star'
}

MOB_IMAGES = {
    "cloud": "floaty",
    "fireball": "fireball_down",
    'mushroom':'mushroom',
    'fire':'fire'
}

#Block section
class Switch(Block):
    """A switch block explodes and removes the bricks around radius 
    when player hits its upside. After 10s the switch and bricks removed by it
    recover as before.
    """
    _id='switch'

    def __init__(self,radius=1):
        """Construct a new switch block.
           
           Parameters:
               radius (int): The range of bricks removed during exploding. 
        """
        super().__init__() 
        self._active = True
        self._radius=radius 
        self._time_start=0
        self._position={}

    def remove_bricks(self,world):
        """Remove the bricks from world.

           Parameters:
               world (World): The world to remove bricks from.  
        """
        x,y=self.get_position()
        below_brick=world.get_block(x,y+10)
        x,y=below_brick.get_position()
        entity_list=world.get_things_in_range(x,y,self._radius*10)
        for entity in entity_list:
            if entity.get_id()=='brick':
                self._position[entity]=entity.get_position()
                world.remove_block(entity)
    
    def on_hit(self,event,data):
        """Callback collision with player event handler."""
        world, player = data
        # Ensure the above of the block is being hit
        if get_collision_direction(player, self) != "A":
            return
        if self._active:
            self._time_start=time.time()
            self._active = False
            self.remove_bricks(world)

    def is_active(self):
        """(bool): Returns true if the block has not exploded."""
        return self._active
    
    def set_active(self,bool):
        """Parameters:
               bool (bool): Set true if the block has not exploded.
           Returns:
               (bool): Returns true if the block has not exploded. 
        """
        self._active=bool
        return self._active

    def step(self,time_delta,data):
        """Time to recover the exploded bricks.
           Parameters:
                time_delta (float): The amount of time that has passed since the last step, in seconds
                game_data (tuple<World, Player>): Arbitrary data supplied by the app class 
        """
        world, player = data
        if time.time()-self._time_start>=10:
            self.set_active(True)
            for brick,position in self._position.items():
                x,y=position
                world.add_block(brick,x,y)

class Bounce(Block):
    """A bounce block propels the player into the air when they walk over 
       or jump on top of the block.
    """
    _id='bounce_block'

    def __init__(self):
        """Construct a new bounce block.
        """
        super().__init__()
        self._active=False
    
    def is_active(self):
        """(bool): Returns false if the block has not yet hit."""
        return self._active

    def set_active(self,bool):
        """Parameters:
               bool (bool): Set true if the block has hit.
           Returns:
               (bool): Returns true if the block has hit. 
        """
        self._active=bool

    def on_hit(self, event, data):
        """ Propel the player into the air.
            Parameters:
                time_delta (float): The amount of time that has passed since the last step, in seconds
                game_data (tuple<World, Player>): Arbitrary data supplied by the app class 
        """
        world, player = data
        if get_collision_direction(player, self) != "A":
            return
        else:
            player.set_velocity((0,-200))
            self.set_active(True)

class Flagpole(Block):
    """When a player collides with this, immediately take the player to the next level. 
       If the player lands on top of the flag pole, their health and max health will be increased by 1.
    """
    _id='flag'
    _cell_size=GOAL_SIZES['flag']

    def __init__(self):
        """Construct a new flag block."""
        super().__init__()

class Tunnel(Block):
    """if the player presses the down key while standing on top of this block, 
       the player will be taken to another level.
    """
    _id='tunnel'
    _cell_size=GOAL_SIZES['tunnel']

    def __init__(self):
        """Construct a new tunnel block."""
        super().__init__()

#Mob section
class Mushroom(Mob):
    """A mushroom mob is a moving entity that collides with a block, player, or other mob
       reversing its direction.When colliding with the player it will damage the player.
    """
    _id='mushroom'

    def __init__(self,world):
        """Construct a new mushroom mob.
           Parameters:
               world (World): The world where the mob should be added to.
        """
        super().__init__(self._id,size=(16, 16),weight=1,tempo=-30)
        self._is_dead=False
        self._world=world

    def on_hit(self, event: pymunk.Arbiter, data):
        """When colliding with the player, player will lose 1 health point and 
           be slightly repelled away from the mob. The mushroom reverses its direction.

           Parameters:
               event (pymunk.Arbiter): Details on the collision event.
               data (tuple<World, Player>): Arbitrary data supplied by the app class.
        """
        world, player = data
        tempo=self.get_tempo()
        vx,vy=player.get_velocity()
        if get_collision_direction(player,self)=='R':
            player.set_velocity((vx-150,0))
            self.set_tempo(-tempo)
            player.change_health(-1)
        elif get_collision_direction(player,self)=='L':
            player.set_velocity((vx+150,0))
            self.set_tempo(-tempo)
            player.change_health(-1)
        elif get_collision_direction(player,self)=='A':
            self.set_dead(True)
    
    def is_dead(self):
        """(bool): return true if the mushroom is dead."""
        return self._is_dead

    def set_dead(self,bool):
        """Parameters:
               bool (bool): set true if the mushroom is dead.
        """
        self._is_dead=bool

    def remove(self):
        """Remove the mushroom from world."""
        self._world.remove_mob(self)

class Fire(Mob):
    """Construct a fireball to eliminate enemies"""
    _id='fire'

    def __init__(self,tempo=500):
        """Construct a new fireball.
           Parameters:
               (int): The speed of fireball. 
        """
        super().__init__(self._id, size=(6, 6), weight=1,tempo=500)

#Item section
class Star(DroppedItem):
    """A item that can be picked up to let players be invincible."""
    _id='star'

    def __init__(self):
        """Construct a new star item."""
        super().__init__(self._id)
    
    def collect(self, player: Player):
        """Parameter:
               player (Player): The player that was involved in the collision.
        """
        pass

class Flower(DroppedItem):
    """A item that can let mario grow up."""
    _id='flower'

    def __init__(self):
        """Construct a new flower."""
        super().__init__(self._id)

    def collect(self, player: Player):
        """Parameter:
               player (Player): The player that was involved in the collision.
        """
        player.set_name('bigger')

class SpriteSheetLoader():
    """Load one of the smaller images from a sprite sheet based on the smaller images
       location and position within the sheet."""

    def __init__(self):
        """Open the pictures in need."""
        self.characters_im=Image.open('spritesheets/characters.png')
        self.enemies_im=Image.open('spritesheets/enemies.png')
        self.items_im=Image.open('spritesheets/items.png')
        self._images=self.create_image_dict()

    def create_image_dict(self):
        """Create a dictionary to store the images."""
        self.image_dict={}
        self.characters_image_list=[#run need to be symmetric
            (80,34,95,50),(80,34,95,50),(97,34,112,50),(97,34,112,50),
            (114,34,129,50),(114,34,129,50),(131,34,146,50),(131,34,146,50),
            (148,34,163,50),(148,34,163,50),(165,34,180,50),(165,34,180,50),
            #fall
            (182,34,197,50)]
        self.characters_bigger_list=[#run need to be symmetric
            (80,66,96,98),(80,66,96,98),(97,66,113,98),(97,66,113,98),
            (114,66,130,98),(114,66,130,98),(131,66,147,98),(131,66,147,98),
            (148,66,164,98),(148,66,164,98),(165,66,181,98),(165,66,181,98),
            #dunk
            (182,66,198,98)]  
        self.mushroom_image_list=[#walk
            (0,16,16,32),(0,16,16,32),(0,16,16,32),(16,16,32,32),
            (16,16,32,32),(16,16,32,32),
            #squish
            (32,24,48,32),(32,24,48,32),(32,24,48,32),(32,24,48,32),
            (32,24,48,32)]
        self.coin_image_list=[#spin need to be symmetric
            (2,98,14,112),(2,98,14,112),(20,112,28,128),(20,112,28,128),
            (6,112,10,128),(6,112,10,128),(38,112,42,128),(38,112,42,128),
            (55,112,58,128),(55,112,58,128)]
        self.bounce_image_list=[(112,16,128,32),(96,8,112,32),(80,0,96,32),
            (96,8,112,32),(112,16,128,32)]
        self.flower_image_list=[(0,32,16,48),(0,32,16,48),(16,32,32,48),
            (16,32,32,48),(32,32,48,48),(32,32,48,48),(48,32,64,48),
            (48,32,64,48)]
        count=1
        self.image_dict['character_right']={}
        for coordinate in self.characters_image_list:
            self.image_dict['character_right'][count]=self.characters_im.crop(coordinate)
            count+=1
        count=1
        self.image_dict['bigger_right']={}
        for coordinate in self.characters_bigger_list:
            self.image_dict['bigger_right'][count]=self.characters_im.crop(coordinate)
            count+=1
        count=1
        self.image_dict['mushroom']={}
        for coordinate in self.mushroom_image_list:
            self.image_dict['mushroom'][count]=self.enemies_im.crop(coordinate)
            count+=1
        count=1
        self.image_dict['coin']={}
        for coordinate in self.coin_image_list:
            self.image_dict['coin'][count]=self.items_im.crop(coordinate)
            count+=1
        count=1
        self.image_dict['bounce']={}
        for coordinate in self.bounce_image_list:
            self.image_dict['bounce'][count]=self.items_im.crop(coordinate)
            count+=1
        count=1
        self.image_dict['flower']={}
        for coordinate in self.flower_image_list:
            self.image_dict['flower'][count]=self.items_im.crop(coordinate)
            count+=1
        #symmetric
        count=1
        self.image_dict['character_left']={}
        for coordinate in self.characters_image_list:
            self.image_dict['character_left'][count]=self.characters_im.crop(coordinate).transpose(Image.FLIP_LEFT_RIGHT)
            count+=1
        count=1
        self.image_dict['bigger_left']={}
        for coordinate in self.characters_bigger_list:
            self.image_dict['bigger_left'][count]=self.characters_im.crop(coordinate).transpose(Image.FLIP_LEFT_RIGHT)
            count+=1
        count=11
        for coordinate in self.coin_image_list[::-1]:
            self.image_dict['coin'][count]=self.items_im.crop(coordinate).transpose(Image.FLIP_LEFT_RIGHT)
            count+=1
        return self.image_dict

    def right_walking_list(self):
        """(List): A list containing pictures about going right."""
        self.right_walking_list=[]
        for count,img in self._images['character_right'].items():
            if count>=1 and count<=12:
                self.right_walking_list.append(img)
        return self.right_walking_list
    
    def left_walking_list(self):
        """(List): A list containing pictures about going left."""
        self.left_walking_list=[]
        for count,img in self._images['character_left'].items():
            if count>=1 and count<=12:
                self.left_walking_list.append(img)
        return self.left_walking_list

    def bigger_right_walking(self):
        """(List): A list containing pictures about going right."""
        self.bigger_right_walking=[]
        for count,img in self._images['bigger_right'].items():
            if count>=1 and count<=12:
                self.bigger_right_walking.append(img)
        return self.bigger_right_walking

    def bigger_left_walking(self):
        """(List): A list containing pictures about going left."""
        self.bigger_left_walking=[]
        for count,img in self._images['bigger_left'].items():
            if count>=1 and count<=12:
                self.bigger_left_walking.append(img)
        return self.bigger_left_walking

    def coin_spinning_list(self):
        """(List): A list containing pictures about coin spinning."""
        self.spinning_list=[]
        for count,img in self._images['coin'].items():
            self.spinning_list.append(img)
        return self.spinning_list

    def bounce_list(self):
        """(List): A list containing pictures about bounce block."""
        self.bounce_list=[]
        for count,img in self._images['bounce'].items():
            self.bounce_list.append(img)
        return self.bounce_list

    def mushroom_walking_list(self):
        """(List): A list containing pictures about mushroom walking."""
        self.mushroom_walking_list=[]
        for count,img in self._images['mushroom'].items():
            if count>=1 and count<=6:
                self.mushroom_walking_list.append(img)
        return self.mushroom_walking_list

    def mushroom_squishing_list(self):
        """(List): A list containing pictures about mushroom squishing."""
        self.mushroom_squishing_list=[]
        for count,img in self._images['mushroom'].items():
            if count>6:
                self.mushroom_squishing_list.append(img)
        return self.mushroom_squishing_list

    def flower_list(self):
        self.flower_list=[]
        for count,img in self._images['flower'].items():
            self.flower_list.append(img)
        return self.flower_list

#Create lazy lists used in animation.
spritesheetloader=SpriteSheetLoader()
images=spritesheetloader.create_image_dict()
right_walking=spritesheetloader.right_walking_list()
right=iter(right_walking)
left_walking=spritesheetloader.left_walking_list()
left=iter(left_walking)
bigger_right_walking=spritesheetloader.bigger_right_walking()
bigger_right=iter(bigger_right_walking)
bigger_left_walking=spritesheetloader.bigger_left_walking()
bigger_left=iter(bigger_left_walking)
spinning=spritesheetloader.coin_spinning_list()
spin=iter(spinning)
bounce=spritesheetloader.bounce_list()
bounce_i=iter(bounce)
mushroom_walking=spritesheetloader.mushroom_walking_list()
m_walking=iter(mushroom_walking)
mushroom_squishing=spritesheetloader.mushroom_squishing_list()
m_squishing=iter(mushroom_squishing)
flower_color=spritesheetloader.flower_list()
flower_c=iter(flower_color)

class MarioViewRenderer(ViewRenderer):
    """A customised view renderer for a game of mario."""

    @ViewRenderer.draw.register(Player)
    def _draw_player(self, instance: Player, shape: pymunk.Shape,
                     view: tk.Canvas, offset: Tuple[int, int]) -> List[int]:
        """Method to draw the canvas element for Player animation."""
        global right,left,step_count,image
        step_count+=1  
        if instance.get_name()=='luigi':
            if shape.body.velocity.x >= 0:
                image = self.load_image("luigi_right")
            else:
                image = self.load_image("luigi_left")
        elif instance.get_name()=='mario':
            if shape.body.velocity.x > 0:
                if step_count % 12==0:
                    right=iter(right_walking)
                try:
                    image = ImageTk.PhotoImage(next(right))
                    self._images['right']=image
                except:
                    image = self.load_image("mario_right")
            elif shape.body.velocity.x < 0:
                if step_count % 12==0:
                    left=iter(left_walking)
                try:
                    image = ImageTk.PhotoImage(next(left))
                    self._images['left']=image
                except:
                    image = self.load_image("mario_left")
            elif shape.body.velocity.x == 0 and shape.body.velocity.y != 0:
                image=ImageTk.PhotoImage(images['character_right'][13])
                self._images['jump_dunk']=image
        elif instance.get_name()=='bigger':
            if shape.body.velocity.x > 0:
                if step_count % 12==0:
                    bigger_right=iter(bigger_right_walking)
                try:
                    image = ImageTk.PhotoImage(next(bigger_right))
                    self._images['bigger_right']=image
                except:
                    image=ImageTk.PhotoImage(images['bigger_right'][1])
                    self._images['bigger_right1']=image
            elif shape.body.velocity.x < 0:
                if step_count % 12==0:
                    bigger_left=iter(bigger_left_walking)
                try:
                    image = ImageTk.PhotoImage(next(bigger_left))
                    self._images['bigger_left']=image
                except:
                    image=ImageTk.PhotoImage(images['bigger_left'][1])
                    self._images['bigger_left1']=image
            elif shape.body.velocity.x == 0 and shape.body.velocity.y != 0:
                image=ImageTk.PhotoImage(images['bigger_right'][13])
                self._images['jump_dunk']=image

        return [view.create_image(shape.bb.center().x + offset[0], shape.bb.center().y,
                                  image=image, tags="player")]

    @ViewRenderer.draw.register(MysteryBlock)
    def _draw_mystery_block(self, instance: MysteryBlock, shape: pymunk.Shape,
                            view: tk.Canvas, offset: Tuple[int, int]) -> List[int]:
        if instance.is_active():
            image = self.load_image("coin")
        else:
            image = self.load_image("coin_used")

        return [view.create_image(shape.bb.center().x + offset[0], shape.bb.center().y,
                                  image=image, tags="block")]

    @ViewRenderer.draw.register(Switch)
    def _draw_switch_block(self, instance: Switch, shape: pymunk.Shape,
                            view: tk.Canvas, offset: Tuple[int, int]):
        """Method to draw the canvas element for Switch animation."""
        if instance.is_active():
            image=self.load_image('switch')
        else:
            image=self.load_image('switch_pressed')

        return [view.create_image(shape.bb.center().x + offset[0], shape.bb.center().y,
                                  image=image, tags="block")]

    @ViewRenderer.draw.register(Coin)
    def _draw_coin_item(self, instance: Coin, shape: pymunk.Shape,
                            view: tk.Canvas, offset: Tuple[int, int]):
        """Method to draw the canvas element for Coin animation."""
        global spin,step_count 
        if step_count % 10==0:
            spin=iter(spinning)
        try:
            image = ImageTk.PhotoImage(next(spin))
            self._images['spin']=image
        except:
            image = self.load_image("coin_item")  

        return [view.create_image(shape.bb.center().x + offset[0], shape.bb.center().y,
                                  image=image, tags="item")]
    
    @ViewRenderer.draw.register(Bounce)
    def _draw_bounce_block(self, instance: Bounce, shape: pymunk.Shape,
                            view: tk.Canvas, offset: Tuple[int, int]):
        """Method to draw the canvas element for Bounce animation."""
        global bounce_i,count
        if instance.is_active():
            count+=1
            try:
                image = ImageTk.PhotoImage(next(bounce_i))
                self._images['bounce_i']=image
            except:
                image = self.load_image("bounce_block")
            if count % 6==0:
                instance.set_active(False)
                bounce_i=iter(bounce)
        else:
            image = self.load_image("bounce_block")

        return [view.create_image(shape.bb.center().x + offset[0], shape.bb.center().y,
                                  image=image, tags="block")]
    
    @ViewRenderer.draw.register(Mushroom)
    def _draw_mushroom_mob(self, instance: Mushroom, shape: pymunk.Shape,
                            view: tk.Canvas, offset: Tuple[int, int]):
        """Method to draw the canvas element for Mushroom animation."""
        global m_walking,m_squishing,step_count,count
        if instance.is_dead():
            count+=1
            try:
                image = ImageTk.PhotoImage(next(m_squishing))
                self._images[1]=image
            except:
                image = ImageTk.PhotoImage(images['mushroom'][7])
                self._images['squish']=image
            if count % 5==0:
                m_squishing=iter(mushroom_squishing)
                instance.set_dead(False)
                instance.remove()
        elif instance.get_tempo()>=0 or instance.get_tempo()<0:
            try:
                image = ImageTk.PhotoImage(next(m_walking))
                self._images['m_walk']=image
            except:
                image = self.load_image("mushroom")
            if step_count % 6 == 0:
                m_walking=iter(mushroom_walking)

        return [view.create_image(shape.bb.center().x + offset[0], shape.bb.center().y,
                                  image=image, tags="mob")]

    @ViewRenderer.draw.register(Flower)
    def _draw_flower_item(self, instance: Flower, shape: pymunk.Shape,
                            view: tk.Canvas, offset: Tuple[int, int]):
        """Method to draw the canvas element for Switch animation."""
        global flower_c,step_count 
        if step_count % 8==0:
            flower_c=iter(flower_color)
        try:
            image = ImageTk.PhotoImage(next(flower_c))
            self._images['flower']=image
        except:
            image=ImageTk.PhotoImage(images['flower'][1])
            self._images['flower']=image

        return [view.create_image(shape.bb.center().x + offset[0], shape.bb.center().y,
                                  image=image, tags="item")]

class Records():
    """ A custom tkinter widget which displays the score and health of the
        player
    """

    def __init__(self,parent=None):
        """Construct a new widget to record player's score and health.
           Parameters:
               parent (tk.Tk): tkinter root widget.  
        """
        self.records=tk.Frame(parent).pack(side=tk.TOP,fill=tk.X)
        self.frame_health = tk.Frame(self.records,bg='black')
        self.frame_health.pack(side=tk.TOP,expand=1,pady=5,fill=tk.X)
        self.label_health = tk.Label(self.frame_health,bg= 'green',width=154)
        self.label_health.pack(side=tk.TOP,anchor=tk.W)
        self.label_score = tk.Label(self.records,text='Score: 0')
        self.label_score.pack(side=tk.TOP)
        

    def change_health(self,player):  
        """The health bar depending on player's health.
           Parameters:
               player (Player): The player in the game.
        """   
        width_percent= float(player.get_health()/player.get_max_health())
        if player.get_health()==player.get_max_health():
            self.label_health.config(bg='green',width=154)
        elif width_percent>=0.5:
            self.label_health.config(width=int(154*width_percent))
        elif width_percent>=0.25:
            self.label_health.config(bg='orange',width=int(154*width_percent))
        else:
            self.label_health.config(bg='red',width=int(154*width_percent))
    
    def change_score(self,player):
        """Changing the score bar if player collects coins.
           Parameters:
               player (Player): The player in the game. 
        """
        score=player.get_score()
        self.label_score.config(text='Score: {}'.format(score))

    def invincible_health(self):
        """Callback if player collects a star."""
        self.label_health.config(bg='yellow')

class HighScore():
    """A tkinter widget to show and store the high scores for each level in a file."""

    def __init__(self,levelname):
        """Construct a new widget to show player's name and score.
           Parameters:
               levelname (str): A string of text file name.
        """
        self._rank_dict1=self.load_rank_file('score_level1.txt')
        self._rank_dict2=self.load_rank_file('score_level2.txt')
        self._rank_dict3=self.load_rank_file('score_level3.txt')
        self._label2_text=self.conver_to_str(levelname)
        top=tk.Toplevel()
        top.title('High Score')
        top.geometry('400x300')
        self.label1=tk.Label(top,text=levelname[0:-4]).pack()
        self.label2=tk.Label(top,text=self._label2_text)
        self.label2.pack()

    def get_name(self,levelname,player):
        """Construct a new tkinter root widget to collect player's name.
           Parameters:
               levelname (str): A string of text file name.
               player (Player): The player in the game. 
        """
        root_1 = tk.Tk()
        root_1.title('Congratulations')
        root_1.geometry('250x150')
        label = tk.Label(root_1,text='Please enter your name:')
        label.pack(side = tk.TOP,pady=10)
        entry = tk.Entry(root_1,width=20)
        entry.pack(side=tk.TOP,expand=1)

        def update_rank_file():
            """A method to store player's name and score in the text file.
            """
            if levelname=='level1.txt':
                with open('score_level1.txt','a') as file:
                    file.write(entry.get()+' : '+str(player.get_score())+'\n')
                self._rank_dict1=self.load_rank_file('score_level1.txt')
                self._label2_text=self.conver_to_str(levelname)
                self.change_label2(self._label2_text)
                root_1.destroy()
            elif levelname=='level2.txt':
                with open('score_level2.txt','a') as file:
                    file.write(entry.get()+' : '+str(player.get_score())+'\n')
                self._rank_dict2=self.load_rank_file('score_level2.txt')
                self._label2_text=self.conver_to_str(levelname)
                self.change_label2(self._label2_text)
                root_1.destroy()
            elif levelname=='level3.txt':
                with open('score_level3.txt','a') as file:
                    file.write(entry.get()+' : '+str(player.get_score())+'\n')
                self._rank_dict3=self.load_rank_file('score_level3.txt')
                self._label2_text=self.conver_to_str(levelname)
                self.change_label2(self._label2_text)
                root_1.destroy()

        button = tk.Button(root_1,text='OK',command=update_rank_file)
        button.pack(side=tk.TOP,pady=5)
        
    def change_label2(self,text):
        """A method to update information with given text.
           Parameters:
               text (str): A string of player's name and score.
        """
        self.label2.config(text=text)

    def load_rank_file(self,rank_file):
        """A method to convert text file content to a dictionary.
           Parameters:
               rank_file (str): A string of text file name.
           Returns:
               rank_dict (dict): A dictionary contains level name, player's name and score. 
        """
        rank_dict={}
        with open(rank_file) as file:
            for line in file:
                line=line.strip()
                if line.startswith('==') and line.endswith('=='):
                    dict_key=line[2:-2]
                    rank_dict[dict_key]={}
                else:
                    inner_key,_,inner_value=line.partition(':')
                    inner_key=inner_key.strip()
                    inner_value=inner_value.strip()
                    rank_dict[dict_key][inner_key]=inner_value
        return rank_dict 

    def conver_to_str(self,levelname):
        """A method to convert dictionary to a decend order string sorted by player's score.
           Parameters:
               levelname (str): A string of text file name.
           Returns:
               (str): A decend order string sorted by player's score.
        """
        if levelname=='level1.txt':
            rank_list=sorted(self._rank_dict1[levelname].items(),key=lambda item: item[1],reverse=True)
            temp_list=[]
            count=1
            for record in rank_list:
                if count<=10:
                    name,score=record
                    record=(name,str(score))
                    temp_list.append(' : '.join(record))
                    count+=1
            return '\n'.join(temp_list)
        elif levelname=='level2.txt':
            rank_list=sorted(self._rank_dict2[levelname].items(),key=lambda item: item[1],reverse=True)
            temp_list=[]
            count=1
            for record in rank_list:
                if count<=10:
                    name,score=record
                    record=(name,str(score))
                    temp_list.append(' : '.join(record))
                    count+=1
            return '\n'.join(temp_list)
        elif levelname=='level3.txt':
            rank_list=sorted(self._rank_dict3[levelname].items(),key=lambda item: item[1],reverse=True)
            temp_list=[]
            count=1
            for record in rank_list:
                if count<=10:
                    name,score=record
                    record=(name,str(score))
                    temp_list.append(' : '.join(record))
                    count+=1
            return '\n'.join(temp_list)    

class MarioApp:
    """High-level app class for Mario, a 2d platformer"""

    _world: World

    def __init__(self, master: tk.Tk):
        """Construct a new game of a MarioApp game.

        Parameters:
            master (tk.Tk): tkinter root widget
        """
        
        self._master = master
        self._master.update_idletasks()
        #Load configuration file
        self._config_file=filedialog.askopenfilename()
        try:
            self._config_dict=self.load_configuration(self._config_file)
            self.get_config_values(self._config_dict)
        except:
            messagebox.showinfo('Sorry!','The file cannot be parsed.')

        world_builder = WorldBuilder(BLOCK_SIZE, gravity=(0, self._gravity), fallback=create_unknown)
        world_builder.register_builders(BLOCKS.keys(), create_block)
        world_builder.register_builders(ITEMS.keys(), create_item)
        world_builder.register_builders(MOBS.keys(), create_mob)
 
        self._builder = world_builder
        self._player = Player(name=self._character,max_health=self._health)
        self.reset_world(self._start)
        self._renderer = MarioViewRenderer(BLOCK_IMAGES, ITEM_IMAGES, MOB_IMAGES)
        size = tuple(map(min, zip(MAX_WINDOW_SIZE, self._world.get_pixel_size())))
        self._view = GameView(master, size, self._renderer)
        self._view.pack()
        self.vx,self.vy=self._player.get_velocity()
        self.bind()

        self._filename = self._start 
        
        self._invincible=False
        self._time_start=None
        self._time_end=None
        self._switch_pressed=False
        self._tunnel=False
        self._tunnel_dict=self.get_tunnel_dict()
        self._list_tunnel=self.get_list_level(self._tunnel_dict)
        self._level_dict=self.get_next_level_dict()
        self._list_level=self.get_list_level(self._level_dict)
        self._last_fire=time.time()

        #file menu
        menubar = tk.Menu(self._master)
        self._master.config(menu=menubar)
        filemenu = tk.Menu(menubar)
        menubar.add_cascade(label='File', menu=filemenu)
        filemenu.add_command(label='Load Level', command=self.load_level)
        filemenu.add_command(label='Reset Level', command=self.reset_level)
        filemenu.add_command(label='High Score', command=self.high_score)
        filemenu.add_command(label='Exit', command=self.exit)
        
        # Wait for window to update before continuing
        master.update_idletasks()
        self.step()

        #Player's health and score       
        self._records=Records(self._master)

    def load_configuration(self,config_file):
        """Convert a text file into a dictionary.
           Parameters:
               config_file (str): A string of text file name.
           Returns:
               config_dict (dict): A dictionary contains information from text file. 
        """
        config_dict={}
        with open(config_file) as file:
            for line in file:
                line=line.strip()
                if line.startswith('==') and line.endswith('=='):
                    dict_key=line[2:-2]
                    config_dict[dict_key]={}
                else:
                    inner_key,_,inner_value=line.partition(':')
                    inner_key=inner_key.strip()
                    inner_value=inner_value.strip()
                    config_dict[dict_key][inner_key]=inner_value
        return config_dict 

    def get_config_values(self,config_dict):
        """Get the information from configuration file.
           Parameters:
               config_dict (dict): A dictionary contains information from text file. 
        """
        #world values
        self._gravity=float(config_dict['World']['gravity'])
        self._start=config_dict['World']['start']

        #player values
        self._character=config_dict['Player']['character']
        self._x=float(config_dict['Player']['x'])
        self._y=float(config_dict['Player']['y'])
        self._mass=float(config_dict['Player']['mass'])
        self._health=float(config_dict['Player']['health'])
        self._max_velocity=float(config_dict['Player']['max_velocity'])

        #other values
        try:
            #level1
            self._1_tunnel=config_dict['level1.txt']['tunnel']
            self._1_goal=config_dict['level1.txt']['goal']
            #bonus
            self._bonus_goal=config_dict['bonus.txt']['goal']
            #level2
            self._2_tunnel=config_dict['level2.txt']['tunnel']
            self._2_goal=config_dict['level2.txt']['goal']
            #small room
            self._sr_goal=config_dict['small_room.txt']['goal']
            #level3
            self._3_goal=config_dict['level3.txt']['goal']
        except:
            None

    def get_tunnel_dict(self):
        """(dict): A dictionary contains information about where the players
           go if they enter a tunnel.
        """
        tunnel_dict={}
        try:
            tunnel_dict['level1.txt']=self._1_tunnel
            tunnel_dict['bonus.txt']=self._bonus_goal
            tunnel_dict['level2.txt']=self._2_tunnel
            tunnel_dict['small_room.txt']=self._sr_goal
        except:
            None
        return tunnel_dict

    def get_next_level_dict(self):
        """(dict): A dictionary contains information about where the players
           go if they collide a flag.
        """
        level_dict={}
        try:
            level_dict['level1.txt']=self._1_goal
            level_dict['level2.txt']=self._2_goal
            level_dict['level3.txt']=self._3_goal
        except:
            None
        return level_dict

    def get_list_level(self,dict):
        """(List): A list of level name"""
        list_level=[]
        for level in dict.keys():
            list_level.append(level)
        return list_level        

    def load_level(self):
        """Load to another level using file menu."""
        self._filename=filedialog.askopenfilename()
        self._filename=self._filename[-10:]
        try:
            self.reset_world(self._filename)
            self._records.change_health(self._player)
            self._records.change_score(self._player)      
        except Exception as e:
            messagebox.showinfo('Sorry!','The file cannot find.')

    def reset_level(self):
        """Reset the level using file menu."""
        self.reset_world(self._filename)
        self._records.change_health(self._player)
        self._records.change_score(self._player) 

    def exit(self):
        """Exit the game."""
        self._master.destroy()

    def high_score(self):
        """Check the other player's score using file menu."""
        self._high_score=HighScore(self._filename)

    def reset_world(self, new_level):
        """A method to reset game to new_level.
           Parameters:
               new_level (str): A string of text file name.
        """
        self._world = load_world(self._builder, new_level)
        self._world.add_player(self._player, self._x, self._y,self._mass)
        self._builder.clear()
        self._player.change_health(self._player.get_max_health())
        self._player.reset_score()
        self._setup_collision_handlers()

    def bind(self):
        """Bind all the keyboard events to their event handlers."""
        if self.vx>=self._max_velocity or self.vx<=-self._max_velocity:
            self._master.bind('<a>',lambda e:self._move(-self._max_velocity,self.vy))
            self._master.bind('<Left>',lambda e:self._move(-self._max_velocity,self.vy))
            self._master.bind('<d>',lambda e:self._move(self._max_velocity,self.vy))
            self._master.bind('<Right>',lambda e:self._move(self._max_velocity,self.vy))
        else:
            self._master.bind('<a>',lambda e:self._move(self.vx-100,self.vy))
            self._master.bind('<Left>',lambda e:self._move(self.vx-100,self.vy))
            self._master.bind('<d>',lambda e:self._move(self.vx+100,self.vy))
            self._master.bind('<Right>',lambda e:self._move(self.vx+100,self.vy))
        self._master.bind('<w>',lambda e:self._jump())
        self._master.bind('<Up>',lambda e:self._jump())
        self._master.bind('<space>',lambda e:self._jump())
        self._master.bind('<s>',lambda e:self._duck())
        self._master.bind('<Down>',lambda e:self._duck())

    def redraw(self):
        """Redraw all the entities in the game canvas."""
        self._view.delete(tk.ALL)
        self._view.draw_entities(self._world.get_all_things())

    def scroll(self):
        """Scroll the view along with the player in the center unless
        they are near the left or right boundaries
        """
        x_position = self._player.get_position()[0]
        half_screen = self._master.winfo_width() / 2
        world_size = self._world.get_pixel_size()[0] - half_screen

        # Left side
        if x_position <= half_screen:
            self._view.set_offset((0, 0))

        # Between left and right sides
        elif half_screen <= x_position <= world_size:
            self._view.set_offset((half_screen - x_position, 0))

        # Right side
        elif x_position >= world_size:
            self._view.set_offset((half_screen - world_size, 0))

    def step(self):
        """Step the world physics and redraw the canvas."""
        data = (self._world, self._player)
        self._world.step(data)
        self.scroll()
        self.redraw()
        self._master.after(10, self.step)
        #Player invincible timing
        if self._invincible == True:
            self._time_end=time.time()
            if self._time_end-self._time_start>=10:
                self._invincible=False
                self._records.change_health(self._player)
        if self._player.get_name()=='bigger':
            if time.time()-self._last_fire>=1:
                x,y=self._player.get_position()
                vx,vy=self._player.get_velocity()
                if vx>=0:
                    fire=Fire()
                    self._world.add_mob(fire,x+30,y)
                elif vx<0:
                    fire=Fire(tempo=-500)
                    self._world.add_mob(fire,x-30,y)
                self._last_fire=time.time()
                
    def _move(self, dx, dy):
        """Set velocity for player.
           Parameters:
               dx (int): Velocity in the x direction
               dy (int): Velocity in the y direction
        """
        self._player.set_velocity((dx,dy))

    def _jump(self):
        """Set velocity for player."""
        self._player.set_velocity((self.vx, self.vy-150))
        
    def _duck(self):
        """Set velocity for player."""
        self._player.set_velocity((self.vx, self.vy+150))
        self._tunnel=True

    def _fire(self):
        pass
    

    def _setup_collision_handlers(self):
        self._world.add_collision_handler("player", "item", on_begin=self._handle_player_collide_item)
        self._world.add_collision_handler("player", "block", on_begin=self._handle_player_collide_block,
                                          on_separate=self._handle_player_separate_block)
        self._world.add_collision_handler("player", "mob", on_begin=self._handle_player_collide_mob)
        self._world.add_collision_handler("mob", "block", on_begin=self._handle_mob_collide_block)
        self._world.add_collision_handler("mob", "mob", on_begin=self._handle_mob_collide_mob)
        self._world.add_collision_handler("mob", "item", on_begin=self._handle_mob_collide_item)

    def _handle_mob_collide_block(self, mob: Mob, block: Block, data,
                                  arbiter: pymunk.Arbiter) -> bool:
        if mob.get_id() == "fireball":
            if block.get_id() == "brick":
                self._world.remove_block(block)
            self._world.remove_mob(mob)

        elif mob.get_id()=='mushroom':
            if get_collision_direction(mob,block)=='L' or get_collision_direction(mob,block)=='R':
                tempo=mob.get_tempo()
                mob.set_tempo(-tempo)
        elif mob.get_id()=='fire':
            self._world.remove_mob(mob)
        return True

    def _handle_mob_collide_item(self, mob: Mob, block: Block, data,
                                 arbiter: pymunk.Arbiter) -> bool:
        return False

    def _handle_mob_collide_mob(self, mob1: Mob, mob2: Mob, data,
                                arbiter: pymunk.Arbiter) -> bool:
        if mob1.get_id() == "fireball" or mob2.get_id() == "fireball":
            self._world.remove_mob(mob1)
            self._world.remove_mob(mob2)
        elif mob1.get_id()=='fire' :
            self._world.remove_mob(mob1)
            self._world.remove_mob(mob2)
        elif mob2.get_id()=='fire':
            self._world.remove_mob(mob1)
            self._world.remove_mob(mob2)
        elif mob1.get_id()=='mushroom' or mob2.get_id()=='mushroom':
            tempo1=mob1.get_tempo()
            mob1.set_tempo(-tempo1)
            tempo2=mob2.get_tempo()
            mob2.set_tempo(-tempo2)
        
        return False

    def _handle_player_collide_item(self, player: Player, dropped_item: DroppedItem,
                                    data, arbiter: pymunk.Arbiter) -> bool:
        """Callback to handle collision between the player and a (dropped) item. If the player has sufficient space in
        their to pick up the item, the item will be removed from the game world.

        Parameters:
            player (Player): The player that was involved in the collision
            dropped_item (DroppedItem): The (dropped) item that the player collided with
            data (dict): data that was added with this collision handler (see data parameter in
                         World.add_collision_handler)
            arbiter (pymunk.Arbiter): Data about a collision
                                      (see http://www.pymunk.org/en/latest/pymunk.html#pymunk.Arbiter)
                                      NOTE: you probably won't need this
        Return:
             bool: False (always ignore this type of collision)
                   (more generally, collision callbacks return True iff the collision should be considered valid; i.e.
                   returning False makes the world ignore the collision)
        """

        dropped_item.collect(self._player)
        self._world.remove_item(dropped_item)
        if dropped_item.get_id()=='coin':
            self._records.change_score(player)
        elif dropped_item.get_id()=='star':
            self._records.invincible_health()
            self._invincible=True 
            self._time_start=time.time()
        return False

    def _handle_player_collide_block(self, player: Player, block: Block, data,
                                     arbiter: pymunk.Arbiter) -> bool:
        if block.get_id()=='flag':
            HighScore(self._filename).get_name(self._filename,player)
            messagebox.showinfo('Congradulations','We will record you!')
            if self._filename in self._list_level:
                self._filename=self._level_dict[self._filename]
                if self._filename=='END':
                    messagebox.showinfo('Congratulations!','You have finished the game.')
                    self.exit()
            else:
                temp=list(self._filename)
                temp[5]=str(int(temp[5])+1)
                self._filename=''.join(temp)  
            self._world = load_world(self._builder, self._filename)
            self._world.add_player(player, BLOCK_SIZE, BLOCK_SIZE)
            self._builder.clear()
            self._setup_collision_handlers()
            if get_collision_direction(player, block) == "A":
                player = Player(player.get_max_health()+1)
                player.change_health(1)

        elif block.get_id()=='tunnel':
            if get_collision_direction(player, block) == "A":
                if self._tunnel==True:
                    if self._filename in self._list_tunnel:
                        self._filename=self._tunnel_dict[self._filename]
                    else:
                        temp=list(self._filename)
                        temp[5]=str(int(temp[5])+1)
                        self._filename=''.join(temp)
                    self._world = load_world(self._builder, self._filename)
                    self._world.add_player(player, BLOCK_SIZE, BLOCK_SIZE)
                    self._builder.clear()
                    self._setup_collision_handlers()
                    self._tunnel=False
           
        elif block.get_id()=='switch':
            block.on_hit(arbiter, (self._world, player))
            if block.is_active()==False:
                self._switch_pressed=True
                return False
        else:
            block.on_hit(arbiter, (self._world, player))    
        return True

    def _handle_player_collide_mob(self, player: Player, mob: Mob, data,
                                   arbiter: pymunk.Arbiter) -> bool:
        if self._invincible==True:
            self._world.remove_mob(mob)
        elif mob.get_id()=='fire':
            return False
        else:
            mob.on_hit(arbiter, (self._world, player))   
            self._records.change_health(player)
            if player.get_name()=='bigger':
                player.set_name('mario')
            
        if player.get_health()==0:
            ans=messagebox.askyesno('GameOver','Would you like to restar?')
            if ans==True:
                self.reset_level()
            else:
                self.exit()      
        return True

    def _handle_player_separate_block(self, player: Player, block: Block, data,
                                      arbiter: pymunk.Arbiter) -> bool:
        return True

def main():
    # create window for game
    root = tk.Tk()
    root.title('Mario')
    app = MarioApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
