import os
import arcade
import json


SPRITE_SCALING = 0.8
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Dungler"




class Door:
    def __init__(self, name: str, x: int, y: int, message: str, coords: list, vert: bool):
        self.name = name
        self.x = x
        self.y = y
        self.message = message
        self.coords = coords
        self.vert = vert

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
    def __init__(self, name: str, coords: list, message: str):
        self.name = name
        self.coords = coords
        self.message = message

    def is_clicked(self, x, y):
        return (self.coords[0] - 32 <= x <= self.coords[0] + 32 and
                self.coords[1] - 32 <= y <= self.coords[1] + 32)

class Item:
    def __init__(self, name: str, coords: list, message: str):
        self.name = name
        self.coords = coords
        self.message = message

    def is_clicked(self, x, y):
        return (self.coords[0] - 32 <= x <= self.coords[0] + 32 and
                self.coords[1] - 32 <= y <= self.coords[1] + 32)

class GameView(arcade.View):

    def __init__(self):
        super().__init__()

        self.enemy = None
        self.selected = None
        self.is_selected = False
        self.confirm = ""
        self.info = ""
        self.selected_info = ""
        self.enemy_sprite = None
        self.player_list = None
        self.interactables_list = []
        self.interactables_list_removed = []
        self.interactables_list_sprite = None
        self.enemies_list = None
        self.inventory = [5,2,10,0]

        self.data = load_game_data("Level1.json")
        self.type = "rooms"
        self.room = "room_1_1"
        self.door_sprite = None
        self.doors_list_sprite = None
        self.enemies_list_sprite = None
        self.doors_list = None

        self.player_sprite = None
        self.room_sprite = None
        self.score = 0
        self.score_text = None
        self.background_color = arcade.color.EERIE_BLACK

    def setup(self):


        self.player_list = arcade.SpriteList()
        self.interactables_list_sprite = arcade.SpriteList()
        self.enemies_list_sprite = arcade.SpriteList()
        self.doors_list_sprite = arcade.SpriteList()
        self.score = 0

        image_path = os.path.join(os.path.dirname(__file__), "assets/player1.png")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Custom sprite image not found: {image_path}")
        else:
            self.player_sprite = arcade.Sprite(image_path,
                                               scale=SPRITE_SCALING,
                                               )
            self.player_list.append(self.player_sprite)


        self.setup_room("room_1_1.png", "start", [WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2])
        self.background_color = arcade.color.EERIE_BLACK

    def on_draw(self):

        self.clear()

        self.interactables_list_sprite.draw()
        arcade.draw_sprite(self.room_sprite)
        self.player_list.draw()

        player_info = f"Attack: {self.inventory[0]}  Defense: {self.inventory[1]}  Health: {self.inventory[2]}  Coins: {self.inventory[3]}"
        arcade.draw_text(player_info, 100, 700, arcade.color.WHITE, 14)
        arcade.draw_text(self.selected_info, 100, 650, arcade.color.WHITE, 14)
        arcade.draw_text(self.info, 100, 600, arcade.color.WHITE, 14)
        arcade.draw_text(self.confirm, 100, 550, arcade.color.WHITE, 14)

    def on_mouse_press(self, x, y, button, modifiers):

        self.score = f'x: {x}, y: {y}'

        self.selected_info = "Nothing selected"
        self.info = ""
        self.confirm = "Return"
        if self.is_selected and 90 <= x <= 160 and 540 <= y <= 570:
            if isinstance(self.selected, Item):
                if self.selected.name == "coin":
                    self.inventory[3] += 1
                enhancements = self.data["items"][self.selected.name]["properties"]
                if "atk" in enhancements:
                    self.inventory[0] += enhancements["atk"]
                if "def" in enhancements:
                    self.inventory[1] += enhancements["def"]
                if "hp" in enhancements:
                    self.inventory[2] += enhancements["hp"]

            if isinstance(self.selected, Enemy):
                enemy_hp = self.enemy["hp"]
                player_hp = self.inventory[2]
                enemy_hp -= max(self.inventory[0] - self.enemy["def"], 0)
                while not (enemy_hp <= 0 or player_hp <= 0):
                    player_hp -= max(self.enemy["atk"] - self.inventory[1] ,0)
                    enemy_hp -= max(self.inventory[0] - self.enemy["def"], 0)
                if player_hp <= 0:
                    self.window.show_view(EndView(self.inventory[3], False))
                self.inventory[3] += self.enemy["gold"]
                if self.selected.name == "goblin_king" and player_hp > 0:
                    self.window.show_view(EndView(self.inventory[3], True))

            for sprite in self.interactables_list_sprite:
                if sprite.position == tuple(self.selected.coords):
                    self.interactables_list_sprite.remove(sprite)
                    self.interactables_list.remove(self.selected)
            self.interactables_list_removed.append(self.selected.coords)
            self.selected = None
            self.is_selected = False
            self.on_draw()
            return
        self.is_selected = False


        if 90 <= x <= 160 and 540 <= y <= 570:
            x = self.player_sprite.center_x
            y = self.player_sprite.center_y
        for interactable in self.interactables_list:
            if interactable.is_clicked(x, y):
                if isinstance(interactable, Door):
                    if interactable.name == "maze":
                        return
                    room = f'{interactable.name}.png'
                    old_room = self.room
                    self.room = interactable.name
                    door_coords = interactable.coords
                    if self.room.startswith("hallway") or self.room.startswith("4-way"):
                        self.type = "hallways"
                    elif self.room.startswith("room"):
                        self.type = "rooms"
                    self.setup_room(room, old_room, door_coords)
                    return

                if isinstance(interactable, Enemy):
                    self.enemy = self.data["enemies"][interactable.name]
                    if interactable.message == "":
                        interactable.message = self.enemy["message"]
                    self.selected_info = f'Attack: {self.enemy["atk"]}  Defense: {self.enemy["def"]}  Health: {self.enemy["hp"]}'
                    self.info = f'{interactable.name}    {interactable.message}'
                    self.confirm = "Attack.               Leave."
                    self.is_selected = True
                    self.selected = interactable

                if isinstance(interactable, Item):
                    item = self.data["items"][interactable.name]
                    attack = 0
                    defense = 0
                    health = 0
                    for i in item["properties"]:
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
                self.interactables_list.append(door)
                ##Find the door we came through
                if door.name == old_room:
                    room_found = True
                    if door_coords == [0, 0]:
                        self.player_sprite.center_x = door.x
                        self.player_sprite.center_y = door.y
                    else:
                        self.player_sprite.center_x = door_coords[0]
                        self.player_sprite.center_y = door_coords[1]
                self.interactables_list_sprite.append(self.door_sprite)

        if not room_found:
            self.player_sprite.center_x = door_coords[0]
            self.player_sprite.center_y = door_coords[1]
        in_door = arcade.check_for_collision_with_list(self.player_sprite, self.interactables_list_sprite)
        if len(in_door) > 0:
            in_door[0].remove_from_sprite_lists()

        for enemy in self.enemies_list:
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
                type = self.data["items"][item.name]["properties"]["type"]
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

        image_path = os.path.join(os.path.dirname(__file__), "assets/Rooms_Level1/", room)
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
    def __init__(self, final_score, win: bool):
        super().__init__()
        self.final_score = final_score
        self.win = win

    def on_show_view(self):
        if self.win:
            arcade.set_background_color(arcade.color.WHITE)
        else:
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
    return Enemy(
        name=data.get("name", "Enemy"),
        coords=data.get("coords", [0,0]),
        message=(data.get("message_alt", ""))
    )

def item_from_json(data: dict, ) -> Item:
    return Item(
        name=data.get("name", "Item"),
        coords=data.get("coords", [0,0]),
        message=(data.get("message_alt", ""))
    )

def load_game_data(file_path: str):
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

    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)

    game = GameView()
    game.setup()

    window.show_view(game)

    arcade.run()


if __name__ == "__main__":
    main()