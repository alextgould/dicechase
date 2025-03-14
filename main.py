# interface
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.properties import NumericProperty, StringProperty

# dice values
from random import randint, random

# music
from kivy.core.audio import SoundLoader

# animations
from kivy.animation import Animation # https://kivy.org/doc/stable/api-kivy.animation.html
from kivy.clock import Clock

# disable multi-touch simulation (red dots when you right click with mouse on a pc)
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# control on screen keyboard behaviour
from kivy.core.window import Window

# new game popup
from kivy.uix.popup import Popup

# save high scores when app is closed and reopened
import os
import json
from operator import itemgetter

# for pyinstaller packaging
import sys
from kivy.resources import resource_add_path
from os import path

# sound effects
play_background_sound = True # TODO: move this to a config file, add config interface
# __file__ is used in the lines below to ensure files are always picked up relative to the script location, even when sys._MEIPASS is in play
sound_click_path = path.abspath(path.join(path.dirname(__file__), 'audio', 'smw_coin.wav'))
sound_background_path = path.abspath(path.join(path.dirname(__file__), 'audio', 'dice_chase.mp3'))
sound_click = SoundLoader.load(sound_click_path)
sound_background = SoundLoader.load(sound_background_path)

# mp3 - good compression but anecdotally may not work on Android (0.4 Mb)
# ogg - good compression but doesn't work on Desktop (0.4 Mb)
# flac - works and has around 75% compression (2.6 Mb)
# wav - works but has 0% compression (9.3 Mb)
# mid - sounds poor, high hat is inaccurate (0.0 Mb)

# game length in seconds - useful to have at the top for testing (e.g. reduce duration from 50 sec to 5 sec)
game_length = 60

class Dice(Button):
    ''' Each dice will have its own properties (e.g. roll style, current value) '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)    

        # parameters to control the dice roll and reroll animations
        self.clickable = True # prevent clicking the dice while reroll animation occurs
        self.roll_anim_duration = 0.5 # duration of the animation in seconds
        self.roll_anim_updates = 10 # number of times to update the value over the duration
        self.roll_anim_step = self.roll_anim_duration / self.roll_anim_updates
        self.roll_anim_count = 0 # keep track of how many times we have updated the dice image
        self.reroll_clock = None

        # parameters to control dice movement animations
        self.move_anim_type = 'bounce' # 'chase on click'
        self.bounce_clock = None

    def init_dice(self):
        ''' run after a new dice is created'''
        self.start_dice_roll_animation() # roll the dice
        self.move_dice()

    def click_dice(self):
        if self.clickable: # not currently in the reroll animation
            App.get_running_app().root.dice_clicked += 1
            sound_click.play() # coin sound
            self.update_score()
            self.cancel_dice_reroll() # cancel scheduled reroll
            self.start_dice_roll_animation() # roll the dice
            self.move_dice()

    def update_score(self):
        App.get_running_app().root.score += self.dice_value

    def roll_dice(self):
        ''' update the image shown on the dice '''
        self.dice_value = randint(1,6)
        img_path = 'img/Alea_' + str(self.dice_value) + '.png'
        self.background_normal=img_path
        self.background_down=img_path

    def move_dice(self):
        ''' move the dice to a new location '''
        self.roll_dice()

        if self.move_anim_type == 'chase on click':
            anim = Animation(target_pos_x = random(), target_pos_y = random())
            anim.start(self)

        elif self.move_anim_type == 'bounce':

            # new random velocity (pixels per incremental update)
            self.velocity_x = randint(1, 4) * (1 if random() < 0.5 else -1)
            self.velocity_y = randint(1, 4) * (1 if random() < 0.5 else -1)
            
            if self.bounce_clock is None:
                self.bounce_clock = Clock.schedule_interval(self.incremental_movement, 1.0/60.0) # 1.0 / 60.0 is 60 frames / sec

    # the "bouncing dice" animation moves the dice based on velocity parameters
    # similar to the pong example, but also checks for collision with other dice
    def incremental_movement(self, dt):
        self.x += self.velocity_x
        self.y += self.velocity_y

        # bounce away from other dice
        App.get_running_app().root.resolve_collisions(self)

        # bounce away from edges, with priority over bouncing away from other dice
        if self.top > self.parent.height: # top
            self.velocity_y = -1 * abs(self.velocity_y) # negative, move down
        elif self.y < 0: # bottom
            self.velocity_y = abs(self.velocity_y) # positive, move up
        elif self.x < 0: # left
            self.velocity_x = abs(self.velocity_x) # positive, move right
        elif self.right > self.parent.width: # right
            self.velocity_x = -1 * abs(self.velocity_x) # negative, move left
            
    # the "dice cycle" animation emulates a roll of the dice by showing various
    # values before stopping on a final value. the dice can't be clicked while
    # the animation is taking place

    def start_dice_roll_animation(self):
        ''' change dice values repeatedly '''
        if self.clickable:
            self.roll_anim_step_decayed = self.roll_anim_step
            Clock.schedule_once(self.update_dice_roll_animation, self.roll_anim_step_decayed)
            self.clickable = False

    def update_dice_roll_animation(self, dt, decay_prop = 0.5, decay_rate = 0.7):
        ''' one iteration of the dice value change animation '''
        self.roll_anim_count += 1

        if self.roll_anim_count == self.roll_anim_updates:
            # done, reset dice to clickable
            self.clickable = True
            self.roll_anim_count = 0
            self.roll_with_reroll()
            return
        elif self.roll_anim_count > self.roll_anim_updates * decay_prop:
            # almost done, slow down the dice value changes
            self.roll_anim_step_decayed /= decay_rate
        self.roll_dice()
        Clock.schedule_once(self.update_dice_roll_animation, self.roll_anim_step_decayed)

    # the "dice reroll" animation randomly changes the dice value when it
    # has not been clicked on for a random period of time. the idea is to
    # try and click the dice when it has a high value (e.g. a 6) before it's 
    # too late, and be patient when it has a low value (e.g. a 1) as it'll change

    def roll_with_reroll(self, *args):
        ''' roll the dice and schedule a reroll after a random delay '''

        self.roll_dice()
        min_delay = 1
        max_delay = 5
        delay = min_delay + random() * (max_delay - min_delay)
        self.reroll_clock = Clock.schedule_once(self.roll_with_reroll, delay)

    def cancel_dice_reroll(self):
        ''' if the user clicks on the dice abandon the scheduled reroll '''

        if self.reroll_clock is not None:
            self.reroll_clock.cancel()

class NewGamePopup(Popup):
    pass

class OptionsPopup(Popup):
    pass

class ClickableImage(Image):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            popup = OptionsPopup()
            popup.open()

class Container(Widget):

    # Label text will update automatically as these variables update
    time_remaining = NumericProperty(0)
    score = NumericProperty(0)
    dice_clicked = NumericProperty(0)
    high_score_table_text = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # create a list to store our dice in, so we can add/remove/update them
        self.dice_list = []

        # create a game timer
        self.game_clock = None

        # adjust the popup text for subsequent games (e.g. show score)
        self.games_played = 0
        
        # show the new game popup once Container has finished rendering
        Clock.schedule_once(self.new_game_popup, 0.5)

        # high scores
        data_path = App.get_running_app().user_data_dir # using this approach based on https://developer.apple.com/forums/thread/675522
        self.hs_path = os.path.join(data_path, 'high_scores.json')
        if not os.path.isfile(self.hs_path): # create a blank high score file if none exists
            with open(self.hs_path, 'w') as f:
                f.write(json.dumps([]))
        if False: # TEMP - use to find file to manually delete it and reset scores
            print(self.hs_path)
        self.max_high_scores = 3

        # Discuss - options for saving/loading data: text, pickle, json
        # https://docs.python.org/3/library/pickle.html#comparison-with-json
        # also Json for dict vs list

    def add_dice(self):
        extra_dice = Dice()
        self.dice_list.append(extra_dice)
        self.ids.dice_zone.add_widget(extra_dice)
        extra_dice.init_dice()

    def remove_dice(self):
        if self.dice_list: # check we have at least one dice
            extra_dice = self.dice_list.pop()
            extra_dice.bounce_clock.cancel()
            extra_dice.cancel_dice_reroll()
            self.ids.dice_zone.remove_widget(extra_dice)

    def remove_all_dice(self):
        while self.dice_list:
            self.remove_dice()

    def resolve_collisions(self, moving_dice):
        for dice in self.dice_list:
            if dice != moving_dice:

                # when thinking about the following, it's helpful to note note .x is left and .y is bottom
                if (dice.y > moving_dice.top) or (moving_dice.y > dice.top) or (moving_dice.x > dice.right) or (dice.x > moving_dice.right):
                    pass # no collision
                else:
                    if (moving_dice.top > dice.y) and (moving_dice.top < dice.center_y): # collision from below
                        moving_dice.velocity_y = -1 * abs(moving_dice.velocity_y) # move down
                        dice.velocity_y = abs(dice.velocity_y) # move up
                    elif (moving_dice.y < dice.top) and (moving_dice.y > dice.center_y): # collision from above
                        moving_dice.velocity_y = abs(moving_dice.velocity_y) # move up
                        dice.velocity_y = -1 * abs(dice.velocity_y) # move down

                    # keep x and y separate as a collision could happen at a corner
                    if (moving_dice.right > dice.x) and (moving_dice.right < dice.center_x): # collision from left
                        moving_dice.velocity_x = -1 * abs(moving_dice.velocity_x) # move left
                        dice.velocity_x = abs(dice.velocity_x) # move right
                    elif (moving_dice.x < dice.right) and (moving_dice.x > dice.center_x): # collision from right
                        moving_dice.velocity_x = abs(moving_dice.velocity_x) # move right
                        dice.velocity_x = -1 * abs(dice.velocity_x) # move left

    def new_game(self): #, game_length = 50): # game_length is in seconds
        if self.game_clock is None: # work around button events firing twice on ios
            self.time_remaining = game_length
            self.score = 0
            self.game_clock = Clock.schedule_interval(self.update_game_clock, 0.5) # update every half second (so we can flash in last 10 sec)
            self.add_dice() # always start with one die

    def update_game_clock(self, dt):
        self.time_remaining -= 0.5

        # end the game when the timer runs out
        if self.time_remaining <= 0:
            self.end_game()

        # add a new dice every 10 seconds
        elif self.time_remaining % 10 == 0:
            self.add_dice()

        # for the last 10 seconds, flash the score/timer label (red/white)
        if self.time_remaining <= 10:
            if self.time_remaining % 1 == 0:
                self.ids.score_time.color = [1, 1, 1, 1]
            else:
                self.ids.score_time.color = [240/255, 10/255, 10/255, 1]

    def end_game(self):
        self.game_clock.cancel()
        self.game_clock = None
        self.remove_all_dice()
        self.games_played += 1
        self.new_game_popup()

    def new_game_popup(self, *args):
        ''' show new game popup initially and after each game '''
        self.popup = NewGamePopup()
        self.can_add_high_score = False
        if self.games_played == 0: # first game played
            # remove all the "end of game" items from the popup
            self.popup.title = "Welcome to Dice Chase!"
            self.popup.ids.play.text = "Play game"
            self.popup.ids.buttons.remove_widget(self.popup.ids.exit)
            self.popup.ids.buttons.remove_widget(self.popup.ids.options)
            self.popup.ids.newgame_contents.remove_widget(self.popup.ids.high_scores)
            self.popup.ids.newgame_contents.remove_widget(self.popup.ids.new_high_score)
            self.popup.ids.newgame_contents.remove_widget(self.popup.ids.bait)
            Window.release_all_keyboards()
        else:
            self.popup.ids.label.text = "Congratulations! You scored {}".format(self.score)
            self.update_high_score_table()
            if self.is_new_high_score():
                self.can_add_high_score = True
            else:
                self.popup.ids.newgame_contents.remove_widget(self.popup.ids.new_high_score)
                Window.release_all_keyboards()
        self.popup.open()

    def is_new_high_score(self):
        ''' reads high score file and returns True if current score is a new high score 
            this approach ensures the person who first gets the score maintains it
        '''

        high_scores = json.load(open(self.hs_path))
        n_scores = 0
        for score in high_scores:
            n_scores += 1
            if self.score > score[1]:
                return True
        if n_scores < self.max_high_scores:
            return True
        return False   

    def add_new_high_score(self):
        ''' edits high score file to include current score '''

        if self.can_add_high_score:

            high_scores = json.load(open(self.hs_path))
            
            # append current score
            player_name = self.popup.ids.player_name.text[0:20] # max name length 30 for display purposes
            if player_name == "":
                player_name = "Anonymous"
            high_scores.append([player_name, self.score])

            # sort high scores
            high_scores = sorted(high_scores, key=itemgetter(1), reverse=True)
            
            # remove extra high score if we're over the cap
            while len(high_scores) > self.max_high_scores:
                high_scores.pop()

            # save high scores
            json.dump(high_scores, open(self.hs_path, 'w'))

            # you can only enter your name once
            self.popup.ids.newgame_contents.remove_widget(self.popup.ids.new_high_score)

            # update high score table
            self.update_high_score_table()
            
            self.can_add_high_score = False

    def update_high_score_table(self):
        ''' updates self.high_score_table_text with current high score file formatted as a string '''

        high_scores = json.load(open(self.hs_path))

        # figure out how wide the name column needs to be
        max_name_chars = 0
        for name, score in high_scores:
            if len(name) > max_name_chars:
                max_name_chars = len(name)
        max_name_chars += 3
        
        if len(high_scores) == 0:
            label_text = ""
        else:
            label_text = "High scores:\n"
            for name, score in high_scores:
                label_text += '\n' + name.ljust(max_name_chars) + str(score)

        if label_text == "":
            label_text = "No high scores yet!"
        
        self.high_score_table_text = label_text
    
    def reset_high_scores(self):
        with open(self.hs_path, 'w') as f:
            f.write(json.dumps([]))  

        self.update_high_score_table()

class DiceApp(App):
    # by calling class named DiceApp, we automatically load the layout from dice.kv

    # overwrite the build method of the App class to use Container as our root widget
    # and grant it additional functionality (e.g. updating periodically)
    def build(self):
        game = Container()
        self.icon = path.abspath(path.join(path.dirname(__file__), 'img', 'dice_chase.ico'))
        return game
    
    # when keyboard shows to enter high score, prevent it covering the window
    Window.softinput_mode = 'below_target' # options: 'pan' 'below_target' 'resize'
    
    if play_background_sound:
        sound_background.loop = True
        sound_background.play()

if __name__ == '__main__':

    # for pyinstaller packaging - allows elements in .kv file to locate the img directory
    if hasattr(sys, '_MEIPASS'):
        resource_add_path(sys._MEIPASS)

    DiceApp().run()