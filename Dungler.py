import os
import arcade
import json

    #Set common variables
SPRITE_SCALING = 0.8
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Dungler"




class Door:
    #Each door object connects to a different room and has coordinates for itself and the connecting door

    def __init__(self, name: str, x: int, y: int, message: str, coords: list, vert: bool):
        self.name = name
        self.x = x
        self.y = y
        self.message = message
        self.coords = coords
        self.vert = vert

        #Rotates the doors hitbox if it is vertically aligned and then checks to see if a click was made
        #inside or around to the door so you don't have to hit it perfectly
    def is_clicked(self, x, y):
        if self.vert:
            height = 36
            width = 104
        else:
            height = 106
            width = 34
        return (self.x - height / 2 <= x <= self.x + height / 2 and
                self.y - width / 2 <= y <= self.y + width / 2)

class Enemy:
    #Enemies have a name and coordinates. Since all same named enemies share the same stats, it is pulled
    #later on if needed

    def __init__(self, name: str, coords: list, message: str):
        self.name = name
        self.coords = coords
        self.message = message

    def is_clicked(self, x, y):
        return (self.coords[0] - 32 <= x <= self.coords[0] + 32 and
                self.coords[1] - 32 <= y <= self.coords[1] + 32)

class Item:
    #Every item like enemies has a name and coords. Additional information is held elsewhere for later usage

    def __init__(self, name: str, coords: list, message: str):
        self.name = name
        self.coords = coords
        self.message = message

    def is_clicked(self, x, y):
        return (self.coords[0] - 32 <= x <= self.coords[0] + 32 and
                self.coords[1] - 32 <= y <= self.coords[1] + 32)

class GameView(arcade.View):
    #Game view holds everything related to the game. If it is in the game it happens here.

    def __init__(self):
        super().__init__()


            #preinitialized variables for use of all functions in GameView
        self.enemy = None
        self.selected = None
        self.enemy_sprite = None
        self.player_list = None
        self.interactables_list_sprite = None
        self.enemies_list = None
        self.door_sprite = None
        self.doors_list_sprite = None
        self.enemies_list_sprite = None
        self.doors_list = None
        self.player_sprite = None
        self.room_sprite = None
        self.score = 0
        self.score_text = None
        self.music_player = None

        self.confirm = ""
        self.info = ""
        self.selected_info = ""
        self.type = "rooms"
        self.room = "room_1_1"

        self.interactables_list = []
        self.interactables_list_removed = []
        self.inventory = [5,2,10,0]

        self.is_selected = False

        self.data = load_game_data("Level1.json")

        self.background_color = arcade.color.EERIE_BLACK

        self.coin_sound = arcade.sound.load_sound(":resources:sounds/coin4.wav")
        self.hit_sound = arcade.sound.load_sound(":resources:sounds/hit1.wav")
        self.upgrade_sound = arcade.sound.load_sound(":resources:sounds/upgrade4.wav")
        self.background_music = arcade.Sound(":resources:music/1918.mp3", streaming=True)

    def setup(self):
        #Set up is where the first part of the game is, well, set up. Variables are defined and sprites gathered

        self.music_player = self.background_music.play(loop=True)
        self.player_list = arcade.SpriteList()
        self.interactables_list_sprite = arcade.SpriteList()
        self.enemies_list_sprite = arcade.SpriteList()
        self.doors_list_sprite = arcade.SpriteList()
        self.score = 0

            #Using json we gather the information for the sprite and add it to the sprite list
        image_path = os.path.join(os.path.dirname(__file__), "assets/player1.png")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Custom sprite image not found: {image_path}")
        else:
            self.player_sprite = arcade.Sprite(image_path,
                                               scale=SPRITE_SCALING,
                                               )
            self.player_list.append(self.player_sprite)

            #setup_room is what will set up each room from now one. Instead of calling the built-in function "setup", we will
            #define our own parameters. Namely, the name of the room we are setting up, the room we are moving into, and the
            #coordinates for the door we came through, so we can place our character
        self.setup_room("room_1_1.png", "start", [WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2])
        self.background_color = arcade.color.EERIE_BLACK

    def on_draw(self):
        #The singular draw function in our game. Anything drawn to the screen gets sent here and the drawn

        self.clear()

            #Draws all the interactables in the room (doors, enemies, etc.), the room itself, and the player
        self.interactables_list_sprite.draw()
        arcade.draw_sprite(self.room_sprite)
        self.player_list.draw()

            #These display all the information to the screen
        player_info = f"Attack: {self.inventory[0]}  Defense: {self.inventory[1]}  Health: {self.inventory[2]}  Coins: {self.inventory[3]}"
        arcade.draw_text(player_info, 100, 700, arcade.color.WHITE, 14)  #Player stats
        arcade.draw_text(self.selected_info, 100, 650, arcade.color.WHITE, 14)  #Stats for selected item
        arcade.draw_text(self.info, 100, 600, arcade.color.WHITE, 14)  #A message about the selected item
        arcade.draw_text(self.confirm, 100, 550, arcade.color.WHITE, 14)  #The button for interacting

    def on_mouse_press(self, x, y, button, modifiers):
        #Defines what happens when the mouse is clicked

        self.selected_info = "Nothing selected"
        self.info = ""
        self.confirm = "Return"

            #If an item has already been selected, then the player can choose to interact with the item by pressing the confirm button
        if self.is_selected and 90 <= x <= 160 and 540 <= y <= 570:
            if isinstance(self.selected, Item):
                if self.selected.name == "coin":   #Coins are just added to the players inventory
                    self.coin_sound.play()
                    self.inventory[3] += 1
                enhancements = self.data["items"][self.selected.name]["properties"]  #Items add their values to the players values
                if "atk" in enhancements:
                    self.inventory[0] += enhancements["atk"]
                if "def" in enhancements:
                    self.inventory[1] += enhancements["def"]
                if "hp" in enhancements:
                    self.inventory[2] += enhancements["hp"]
                self.upgrade_sound.play()

            if isinstance(self.selected, Enemy):  #Enemies initiate a "battle", and as long as the player wins the enemy is defeated
                enemy_hp = self.enemy["hp"]
                player_hp = self.inventory[2]
                enemy_hp -= max(self.inventory[0] - self.enemy["def"], 0)  #Player always attacks first, and if an attack would be negative damage, zero is used instead

                while not (enemy_hp <= 0 or player_hp <= 0):
                    player_hp -= max(self.enemy["atk"] - self.inventory[1] ,0)
                    enemy_hp -= max(self.inventory[0] - self.enemy["def"], 0)

                if player_hp <= 0:
                    self.music_player.pause()
                    self.window.show_view(EndView(self.inventory[3], False))

                self.hit_sound.play()
                self.inventory[3] += self.enemy["gold"]

                if self.selected.name == "goblin_king" and player_hp > 0:  #If the player kills the boss the victory screen is shown
                    self.window.show_view(EndView(self.inventory[3], True))

            for sprite in self.interactables_list_sprite:  #Once interacted with the interacted object is removed from the game
                if sprite.position == tuple(self.selected.coords):
                    self.interactables_list_sprite.remove(sprite)
                    self.interactables_list.remove(self.selected)

            self.interactables_list_removed.append(self.selected.coords)
            self.selected = None
            self.is_selected = False
            self.on_draw()

            return

        self.is_selected = False  #Nothing is now selected

            #When an interactable object is not selected the player had the option of returning to the previous room, by pressing the same button
            #used to interact with items
        if 90 <= x <= 160 and 540 <= y <= 570:
            x = self.player_sprite.center_x
            y = self.player_sprite.center_y

        for interactable in self.interactables_list:
            if interactable.is_clicked(x, y):  #Checks to see which interactable has been clicked
                if isinstance(interactable, Door):
                    if interactable.name == "maze":  #Maze has not been implimented
                        return

                    room = f'{interactable.name}.png'
                    old_room = self.room
                    self.room = interactable.name
                    door_coords = interactable.coords

                        #Determines if it needs to use the hallways, or rooms in the json file
                    if self.room.startswith("hallway") or self.room.startswith("4-way"):
                        self.type = "hallways"

                    elif self.room.startswith("room"):
                        self.type = "rooms"

                    self.setup_room(room, old_room, door_coords)

                    return  #If a door is selected then we can just leave after we gather all the data, no need to check the others

                    #If it is an enemy we need to gather the data form the json, and display it to the screen
                if isinstance(interactable, Enemy):
                    self.enemy = self.data["enemies"][interactable.name]

                    if interactable.message == "":
                        interactable.message = self.enemy["message"]

                    self.selected_info = f'Attack: {self.enemy["atk"]}  Defense: {self.enemy["def"]}  Health: {self.enemy["hp"]}'
                    self.info = f'{interactable.name}    {interactable.message}'
                    self.confirm = "Attack.               Leave."
                    self.is_selected = True
                    self.selected = interactable

                    #If it is an item we need to gather the data form the json, and display it to the screen
                if isinstance(interactable, Item):
                    item = self.data["items"][interactable.name]
                    attack = 0
                    defense = 0
                    health = 0

                    for i in item["properties"]:  #Not all items have the same properties, so we need to add only those that do

                        if i == "atk":
                            attack = item["properties"][i]
                        if i == "def":
                            defense = item["properties"][i]
                        if i == "hp":
                            health = item["properties"][i]

                    self.selected_info = f'Attack: +{attack}  Defense: +{defense}  Health: +{health}'
                    if interactable.message == "":
                        interactable.message = item["message"]
                    self.info = f'{interactable.name}   {interactable.message}'
                    self.confirm = "Pick up.             Leave."
                    self.is_selected = True
                    self.selected = interactable


    def setup_room(self, room: str, old_room: str, door_coords: list):
        #This will gather all the data for the room, the doors, and objects in the room
        #We will then send them all to be drawn

        doors_data = self.data[self.type][self.room]["doors"]
        self.doors_list: List[Door] = [door_from_json(e) for e in doors_data]

        enemies_data = self.data[self.type][self.room]["enemies"]
        self.enemies_list: List[Enemy] = [enemy_from_json(e) for e in enemies_data]

        items_data = self.data[self.type][self.room]["items"]
        items_list: List[Item] = [item_from_json(e) for e in items_data]

        self.interactables_list_sprite.clear()
        self.interactables_list.clear()
        self.score = ""
        room_found = False

        for door in self.doors_list:

            image_path = os.path.join(os.path.dirname(__file__), "assets/door.png")
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Custom sprite image not found: {image_path}")
            else:
                self.door_sprite = arcade.Sprite(image_path,
                                                 scale=SPRITE_SCALING,
                                                 )

                self.door_sprite.center_x = door.x
                self.door_sprite.center_y = door.y

                if door.vert:
                    self.door_sprite.angle = 90

                self.interactables_list.append(door)  #We need to add the door to the interactables, but then check and see if it is "open". In which case we won't draw it

                #Find the door we came through
                if door.name == old_room:
                    room_found = True

                        #Doors have two coordinates, their  own, and the coordinates to the joining door. If they don't have those coordinates
                        #to the next door, we will find it by going through the doors and finding which one leads back, and that is the door
                    if door_coords == [0, 0]:
                        self.player_sprite.center_x = door.x
                        self.player_sprite.center_y = door.y
                    else:
                        self.player_sprite.center_x = door_coords[0]
                        self.player_sprite.center_y = door_coords[1]

                self.interactables_list_sprite.append(self.door_sprite)

        if not room_found:  #If the room doesn't connect back, we need to use the predefined coords to find our starting spot
            self.player_sprite.center_x = door_coords[0]
            self.player_sprite.center_y = door_coords[1]

        in_door = arcade.check_for_collision_with_list(self.player_sprite, self.interactables_list_sprite)
        if len(in_door) > 0:  #If the door is "open" (the one we came through), don't draw it
            in_door[0].remove_from_sprite_lists()

        for enemy in self.enemies_list:  #Each enemy has a specific image, and position
            if enemy.coords not in self.interactables_list_removed:
                enemy_sprite_path = f'{enemy.name}.png'

                image_path = os.path.join(os.path.dirname(__file__), "assets/enemies", enemy_sprite_path)
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Custom sprite image not found: {image_path}")
                else:
                    self.enemy_sprite = arcade.Sprite(image_path,
                                                     scale=SPRITE_SCALING,
                                                     )

                    self.enemy_sprite.center_x = enemy.coords[0]
                    self.enemy_sprite.center_y = enemy.coords[1]

                self.interactables_list.append(enemy)
                self.interactables_list_sprite.append(self.enemy_sprite)

        for item in items_list:
            if item.coords not in self.interactables_list_removed:
                type = self.data["items"][item.name]["properties"]["type"]  #Items have a longer image path
                item_sprite_path = f'{type}.png'

                image_path = os.path.join(os.path.dirname(__file__), "assets/items", item_sprite_path)
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Custom sprite image not found: {image_path}")
                else:
                    item_sprite = arcade.Sprite(image_path,
                                                      scale=SPRITE_SCALING,
                                                      )
                    item_sprite.center_x = item.coords[0]
                    item_sprite.center_y = item.coords[1]

                self.interactables_list.append(item)
                self.interactables_list_sprite.append(item_sprite)

        image_path = os.path.join(os.path.dirname(__file__), "assets/Rooms_Level1/", room)  #Finally, the room
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Custom sprite image not found: {image_path}")
        else:
            self.room_sprite = arcade.Sprite(image_path,
                                             scale=SPRITE_SCALING,
                                             )

            self.room_sprite.center_x = WINDOW_WIDTH / 2
            self.room_sprite.center_y = WINDOW_HEIGHT / 2

        return


class EndView(arcade.View):
    #When the game is over we switch to a new view for the game with either a game over, or victory screen

    def __init__(self, final_score, win: bool):
        super().__init__()
        self.final_score = final_score
        self.win = win
        self.game_over_sound = arcade.sound.load_sound(":resources:sounds/gameover5.wav")
        self.victory_sound = arcade.sound.load_sound(":resources:sounds/secret4.wav")

    def on_show_view(self):
        if self.win:
            self.victory_sound.play()
            arcade.set_background_color(arcade.color.WHITE)
        else:
            self.game_over_sound.play()
            arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        if self.win:
            arcade.draw_text("Victory!", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, arcade.color.BLACK, 50, anchor_x="center")
            arcade.draw_text(f"Final Score: {self.final_score}", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50,arcade.color.BLACK, 24, anchor_x="center")
            arcade.draw_text("Click to restart", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100, arcade.color.BLACK, 18,anchor_x="center")
        else:
            arcade.draw_text("GAME OVER!", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, arcade.color.WHITE, 50, anchor_x="center")
            arcade.draw_text(f"Final Score: {self.final_score}", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50, arcade.color.WHITE, 24, anchor_x="center")
            arcade.draw_text("Click to restart", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100, arcade.color.WHITE, 18, anchor_x="center")

    def on_mouse_press(self, x, y, button, modifiers):
        game = GameView()
        game.setup()
        self.window.show_view(game)



def door_from_json(data: dict) -> Door:

    return Door(
        name=data.get("name", "room_4_3.png"),
        x=int(data.get("x", 0)),
        y=int(data.get("y", 0)),
        message=(data.get("message", "")),
        coords=(data.get("coords", [0, 0])),
        vert=(data.get("vertical", False))
    )


def enemy_from_json(data: dict, ) -> Enemy:
    #Gathers enemy data and applies it to an enemy object

    return Enemy(
        name=data.get("name", "Enemy"),
        coords=data.get("coords", [0,0]),
        message=(data.get("message_alt", ""))
    )

def item_from_json(data: dict, ) -> Item:
    #Gathers item data and applies it to an item object

    return Item(
        name=data.get("name", "Item"),
        coords=data.get("coords", [0,0]),
        message=(data.get("message_alt", ""))
    )

def load_game_data(file_path: str):
    #Loads all the data from our json into one data object

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return {}


def main():
    #Program starts here

        #Sets up our window with the defined values
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)

        #makes our game view object and sets it up for the frist time
    game = GameView()
    game.setup()

        #Sends the game view object to the window to be displayed
    window.show_view(game)

        #The arcade library starts and handles everything (loops) with this function call
    arcade.run()


if __name__ == "__main__":
    main()