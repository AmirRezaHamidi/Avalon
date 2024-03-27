import os
from random import shuffle

import telebot
from emoji import demojize, emojize
from loguru import logger
from telebot import types
import time

from Constants import Sub_States, States, Keys, Texts, Char_Texts
from Engines import Avalon_Engine
from utils.io import read_txt_file

current_working_directory = os.getcwd()
TOKEN = read_txt_file(f"{current_working_directory}\\src\\Data\\Bot_Token.txt")
creating_game_word = read_txt_file(
    f"{current_working_directory}\\src\\Data\\creating_game_word.txt")
terminating_game_word = read_txt_file(
    f"{current_working_directory}\\src\\Data\\terminating_game_word.txt")


class Bot():

    def initial_condition(self):

        # admin parameters
        self.creating_game_word = creating_game_word
        self.terminating_game_word = terminating_game_word
        self.admin_id = int()

        # game state parameter
        self.game_state = States.no_game
        self.game_sub_state = None

        # players parameters
        self.names = list()
        self.checked_names = list()
        self.ids = list()

        self.ids_to_names = dict()
        self.names_to_ids = dict()

        # Character parameters
        # characters
        merlin = Char_Texts.merlin
        assassin = Char_Texts.assassin
        mordred = Char_Texts.mordred
        obron = Char_Texts.oberon
        persival = Char_Texts.persival_morgana
        # lady = Char_Texts.lady
        key = Keys.check_box

        # lists
        self.choosed_characters = [merlin, assassin]

        optional = [obron, mordred, persival]
        self.optional_characters = optional

        self.checked_optional_characters = [f"{key}{i}" for i in optional]
        self.Evil_team_id = list()

        # commander parameters
        self.commander_order = list()
        self.current_commander = str()
        self.current_commander_id = int()
        self.first_commander = True
        self.shuffle_commander_order = True
        self.commander_number = 0

        # committee parameters
        self.committee_voters = list()
        self.committee_votes = list()

        # mission parameters
        self.mission_voters = list()
        self.mission_voters_name = list()
        self.mission_votes = list()

        # assassin parameters
        self.assassin_id = int()
        self.assassins_guess = str()

        # summary parameters
        self.committee_summary = str()
        self.mission_summary = str()
        self.all_time_summary = list()
        self.do_wait = False

    def __init__(self):

        # Initializing the bot ...
        self.initial_condition()
        self.bot = telebot.TeleBot(TOKEN)

        # defining bot handlders ...
        logger.info("Defining the handlers ...")
        self.handlers()

        # Start polling ...
        logger.info("Starting the bots ...")
        self.bot.infinity_polling()

    def handlers(self):

        # Handlers with not condition.
        @self.bot.message_handler(regexp=self.creating_game_word)
        def creating_game_word(message):
            print("creating_game_word")

            if self.game_state == States.no_game:

                self.created_game_state(message)
                self.add_player(message)

                name = self.ids_to_names[message.chat.id]
                text = f"{Texts.CG}{name}."
                keyboard = self.character_keyboard()

                self.bot.send_message(
                    message.chat.id, text, reply_markup=keyboard)

            else:

                text = Texts.GOG
                self.bot.send_message(message.chat.id, text)

        # Search Command #
        @self.bot.message_handler(commands=["search"])
        def search_command(message):
            print("search_command")

            if message.chat.id not in self.ids:

                keyboard = self.remove_keyboard()
                text = Texts.SFG

                self.bot.send_message(
                    message.chat.id, text, reply_markup=keyboard)
                time.sleep(1)

                if self.game_state == States.no_game:

                    text = Texts.NGSC

                elif self.game_state == States.started:
                    text = Texts.NGSC

                elif self.game_state == States.created:

                    text = Texts.GESC
                    keyboard = self.join_game_keyboard()

                self.bot.send_message(
                    message.chat.id, text, reply_markup=keyboard)

            else:

                text = Texts.YAJ
                self.bot.send_message(message.chat.id, text)

        # Join Game #
        @self.bot.message_handler(regexp=Keys.join_game)
        def joining_game(message):
            print("join_game")

            if message.chat.id not in self.ids:

                self.add_player(message)
                name = self.ids_to_names[message.chat.id]

                text = f"{Texts.YJGS}\n{Texts.YN}{name}."
                keyboard = self.remove_keyboard()

                self.bot.send_message(
                    message.chat.id, text, reply_markup=keyboard)

                text = f"{name}{Texts.GAJG}"

                self.bot.send_message(self.admin_id, text)

            else:

                text = Texts.YAJ
                self.bot.send_message(message.chat.id, text)

        # Choose_character #
        @self.bot.message_handler(func=self.is_admin_choosing_character)
        def Choose_character(message):
            print("choose_character")
            self.admin_choose_characters(message)

        # Terminate Game #
        @self.bot.message_handler(func=self.is_admin_terminating_game)
        def terminating_game_word(message):
            print("terminate_game")

            self.bot.delete_message(message.chat.id, message.id)
            if self.game_state == States.no_game:

                self.bot.send_message(message.chat.id, Texts.NGET)

            else:

                keyboard = self.remove_keyboard()

                for id in self.ids:

                    self.bot.send_message(id, Texts.TGT, reply_markup=keyboard)

                self.ended_game_state()

        # Send Info #
        @self.bot.message_handler(func=self.is_admin_starting_game)
        def starting_game(message):
            print("starting_game")

            if self.game_state == States.created:

                self.start_game(message)

            else:

                text = Texts.TGHS
                self.bot.send_message(message.chat.id, text)

        # ccommander choosing name #
        @self.bot.message_handler(func=self.is_commander_choosing_name)
        def commander_choosing_name(message):
            print("commander_choosing_name")

            self.commander_choose_name(message)

        # commander pressing button #
        @self.bot.message_handler(func=self.is_commander_pressing_button)
        def commander_press_button(message):
            print("commander_press_button")

            self.game.check_committee(self.mission_voters)

            if self.game.acceptable_round:

                self.commander_decision(message)

            else:

                self.pick_right_players(message)

        # committee vote #
        @self.bot.message_handler(func=self.is_eligible_vote)
        def vote_for_committee(message):
            print("vote_for_committee")

            name = self.ids_to_names[message.chat.id]

            if name in self.committee_voters:

                self.committee_voters.remove(name)

                if self.committee_voters:

                    self.handle_committee_vote(message)

                else:

                    self.handle_committee_vote(message)
                    self.game.count_committee_vote(self.committee_votes)
                    self.send_committee_summary()

                    if self.game.reject_count == 5:

                        self.end_5_reject()

                    elif self.game.committee_accept:

                        self.go_to_mission_voting()

                    else:

                        self.go_to_next_commander()

            else:

                self.you_voted(message)

        # mission vote #
        @self.bot.message_handler(func=self.is_eligible_fail_success)
        def vote_for_mission(message):
            print("vote_for_mission")

            name = self.ids_to_names[message.chat.id]

            if name in self.mission_voters:

                self.mission_voters.remove(name)

                if self.mission_voters:

                    self.handle_mission_vote(message)

                else:

                    self.handle_mission_vote(message)
                    self.game.mission_result(self.mission_votes)
                    self.send_mission_summary()

                    if self.game.evil_wins == 3:

                        self.end_evil_3_won()

                    elif self.game.city_wins == 3:

                        self.city_3_won()

                    else:

                        self.go_to_next_commander()

            else:

                self.you_voted(message)

        @self.bot.message_handler(func=self.is_assassin_choosing_name)
        def assassin_choosing_name(message):
            print("assassin_choosing_name")

            self.assassin_choose_name(message)

        @self.bot.message_handler(func=self.is_assassin_pressing_button)
        def assassin_pressing_button(message):
            print("assassin_pressing_button")

            if self.assassins_guess == str():

                self.choose_someone()

            else:

                self.end_assassin_shot()

        # Print Input #
        @self.bot.message_handler()
        def print_function(message):
            print("print_function")

            text = demojize(message.text)
            self.bot.send_message(message.chat.id, text)

    # main functions #
    # the following functions are the main functions of the bot

    def grab_name(self, message):

        name = str()

        if message.chat.type == "private":

            if ((message.chat.first_name is not None)
               and (message.chat.last_name is not None)):
                name = message.chat.first_name + " " + message.chat.last_name

            elif not (message.chat.last_name):
                name = message.chat.first_name

            elif not (message.chat.first_name):
                name = message.chat.last_name

            return name

        elif message.chat.type == "group" or message.chat.type == "supergroup":

            if ((message.from_user.first_name is not None)
               and (message.from_user.last_name is not None)):

                name = (message.from_user.first_name +
                        " " + message.from_user.last_name)

            elif not (message.from_user.last_name):
                name = message.from_user.first_name

            elif not (message.from_user.first_name):
                name = message.from_user.last_name

            name = name + " @ " + message.chat.title

            return name

    def fix_name(self, currupted_name):

        if currupted_name[0:len(Keys.check_box)] == Keys.check_box:

            return currupted_name[len(Keys.check_box):]

        else:

            return currupted_name

    def add_player(self, message):

        name = self.grab_name(message)
        temp_name = name

        id = message.chat.id
        similar_name_count = 0

        while True:

            if temp_name in self.names:

                similar_name_count += 1
                temp_name = f"{name}_{similar_name_count}"

            else:

                name = temp_name
                break

        self.names.append(name)
        self.ids.append(id)

        self.checked_names.append(emojize(f"{Keys.check_box}{name}"))

        self.names_to_ids[name] = id
        self.ids_to_names[id] = name

    def admin_choose_characters(self, message):

        self.bot.delete_message(message.chat.id, message.id)
        add_remove_name = self.fix_name(message.text)

        if add_remove_name in self.choosed_characters:

            self.choosed_characters.remove(add_remove_name)
            text = f"{add_remove_name}{Texts.RFG}"

        else:

            self.choosed_characters.append(add_remove_name)
            text = f"{add_remove_name}{Texts.ATG}"

        keyboard = self.character_keyboard()
        self.bot.send_message(message.chat.id, text, reply_markup=keyboard)

    def define_game(self):

        name_for_game = self.names[:]
        character_for_game = self.choosed_characters[:]
        self.game = Avalon_Engine(name_for_game, character_for_game)

    def my_wait(self, k):

        if self.do_wait:

            n = len(self.names) / k

            for i in range(1, 4):

                for id in self.ids:

                    self.bot.send_message(id, "." * i)

                    time.sleep(1/n)

    def send_info(self):

        self.define_game()
        self.started_game_state()

        for id in self.ids:

            self.bot.send_message(id, Texts.YR)

        for name, character in self.game.names_to_characters.items():

            if character.name == Char_Texts.assassin:
                self.assassin_id = self.names_to_ids[name]

            text = self.game.all_messages[character.name]

            self.bot.send_message(self.names_to_ids[name], text)

    def make_commander_order(self):

        self.commander_order = self.names[:]

        if self.shuffle_commander_order:

            shuffle(self.commander_order)

    def resolve_commander(self):

        if self.commander_number == len(self.names):

            self.commander_number = 0

        self.current_commander = self.commander_order[self.commander_number]
        self.current_commander_id = self.names_to_ids[self.current_commander]
        self.commander_number += 1

    def send_round_info(self):

        round_info = "Rounds:\n\n"
        two_fail = "(2)" if self.game.two_fails else ""

        for index, this_round in enumerate(self.game.all_round[1:]):

            if index + 1 >= self.game.round:

                sign = "" if index == 0 else "|"

                if index + 1 == 4:

                    if index + 1 == self.game.round:

                        text = emojize(f":keycap_{this_round}: {two_fail}")

                    else:

                        text = f"{this_round} {two_fail}"

                else:

                    if index + 1 == self.game.round:

                        text = emojize(f":keycap_{this_round}:")

                    else:

                        text = f"{this_round}"

                round_info += sign
                round_info += f"{text: ^10}"

            else:

                result = self.game.all_wins[index + 1]
                sign = "" if index == 0 else "|"

                if result == 1:

                    text = f"{Keys.city_win}"

                elif result == -1:

                    text = f"{Keys.evil_win}"

                round_info += sign
                round_info += f"{text: ^7}"

        for id in self.ids:

            self.bot.send_message(id, round_info)

    def send_commander_order(self):

        commander_order_show = str()

        for index, name in enumerate(self.commander_order):

            if index == self.commander_number - 1:

                commander_order_show += emojize(f"{name} --> (:crown:)\n")

            else:

                commander_order_show += f"{name}\n"

        n_players = f"{len(self.names)} Players"
        text = emojize(f"{Texts.CO} ({n_players})\n\n" + commander_order_show)
        keyboard = self.remove_keyboard()

        for id in self.ids:

            self.bot.send_message(id, text, reply_markup=keyboard)

    def go_to_next_commander(self):

        self.committee_choosing_state()
        self.resolve_commander()
        self.send_round_info()
        self.send_commander_order()

        n_committee = self.game.all_round[self.game.round]

        text = f"{Texts.CCN1}{Texts.CCN2_1}{n_committee}{Texts.CCN2_2}"
        keyboard = self.commander_keyboard()

        self.bot.send_message(self.current_commander_id,
                              text, reply_markup=keyboard)

    def start_game(self, message):

        try:

            self.send_info()
            self.make_commander_order()
            self.go_to_next_commander()

        except ValueError as e:

            self.bot.send_message(message.chat.id, e.args[0])

    def transfer_committee_vote(self, message):

        if message.text == Keys.agree:
            self.committee_votes.append(1)

        elif message.text == Keys.disagree:
            self.committee_votes.append(0)

    def transfer_mission_vote(self, message):

        if message.text == Keys.success:
            self.mission_votes.append(1)

        elif message.text == Keys.fail:
            self.mission_votes.append(0)

    def commander_choose_name(self, message):

        self.bot.delete_message(message.chat.id, message.id)
        add_remove_name = self.fix_name(message.text)

        if add_remove_name in self.mission_voters:

            self.mission_voters.remove(add_remove_name)
            text = f"{add_remove_name}{Texts.RFC}"

        else:

            self.mission_voters.append(add_remove_name)
            text = f"{add_remove_name}{Texts.ATC}"

        keyboard = self.commander_keyboard()
        self.bot.send_message(message.chat.id, text, reply_markup=keyboard)

    def commander_decision(self, message):

        self.bot.delete_message(message.chat.id, message.id)

        if message.text == Keys.propose:

            text = f"{Texts.PCC}\n-" + "\n-".join(self.mission_voters)

            for id in self.ids:

                self.bot.send_message(id, text)

        elif message.text == Keys.final:

            text = f"{Texts.FCC}\n-" + "\n-".join(self.mission_voters)
            keyboard = self.committee_vote_keyboard()

            for id in self.ids:
                self.bot.send_message(id, text, reply_markup=keyboard)

            self.committee_voting_state()

    def pick_right_players(self, message):

        self.bot.delete_message(message.chat.id, message.id)
        n_committee = self.game.all_round[self.game.round]

        text = f"{Texts.CCN2_1}{n_committee}{Texts.CCN2_2}"
        keyboard = self.commander_keyboard()

        self.bot.send_message(message.chat.id, text, reply_markup=keyboard)

    def go_to_mission_voting(self):

        text = Texts.CM

        for name in self.mission_voters:

            self.mission_voters_name.append(name)
            keyboard = self.mission_vote_keyboard()

            self.bot.send_message(
                self.names_to_ids[name], text, reply_markup=keyboard)

        self.mission_voting_state()

    def handle_committee_vote(self, message):

        self.bot.delete_message(message.chat.id, message.id)

        name = self.ids_to_names[message.chat.id]
        self.transfer_committee_vote(message)

        text = emojize(f"{Texts.CV}{message.text}")
        keyboard = self.remove_keyboard()

        self.bot.send_message(message.chat.id, text, reply_markup=keyboard)
        self.committee_summary += self.add_committee_vote(name, message.text)

    def handle_mission_vote(self, message):

        self.transfer_mission_vote(message)

        text = Texts.SFV
        keyboard = self.remove_keyboard()

        self.bot.send_message(message.chat.id, text, reply_markup=keyboard)
        self.bot.delete_message(message.chat.id, message.id)

    def you_voted(self, message):

        self.bot.send_message(message.chat.id, emojize(Texts.YVB))
        self.bot.delete_message(message.chat.id, message.id)

    def city_3_won(self):

        self.send_round_info()
        text = Texts.CW3R
        keyboard = self.remove_keyboard()

        for id in self.ids:

            self.bot.send_message(id, text, reply_markup=keyboard)

        text = Texts.ASS1
        keyboard = self.assassin_keyboard()

        self.bot.send_message(self.assassin_id, text, reply_markup=keyboard)

        self.assassin_shooting_state()

    def assassin_choose_name(self, message):

        self.bot.delete_message(message.chat.id, message.id)
        self.assassins_guess = self.fix_name(message.text)

        text = emojize(f"{Texts.ASS2_1}{self.assassins_guess}{Texts.ASS2_2}")
        keyboard = self.assassin_keyboard()

        self.bot.send_message(self.assassin_id, text, reply_markup=keyboard)

    def choose_someone(self):

        text = Texts.ASS3
        keyboard = self.assassin_keyboard()

        self.bot.send_message(self.assassin_id, text, reply_markup=keyboard)

    def end_assassin_shot(self):

        self.game.assassin_shoot(self.assassins_guess)

        if self.game.assassin_shooted_right:

            text = f"{Texts.EW}{Texts.REW2}"

        else:

            text = f"{Texts.CW}{Texts.RCW}"

        self.my_wait(1)

        keyboard = self.remove_keyboard()

        for id in self.ids:

            self.bot.send_message(id, text, reply_markup=keyboard)

        self.ended_game_state()

    def end_evil_3_won(self):

        self.send_round_info()
        text = f"{Texts.EW}{Texts.REW3}"
        keyboard = self.remove_keyboard()

        for id in self.ids:

            self.bot.send_message(id, text, reply_markup=keyboard)

        self.ended_game_state()

    def end_5_reject(self):

        text = f"{Texts.EW}{Texts.REW1}"
        keyboard = self.remove_keyboard()

        for id in self.ids:

            self.bot.send_message(id, text, reply_markup=keyboard)

        self.ended_game_state()

    # State functions
    # These functions help keep track of the state during the game.

    def created_game_state(self, message):

        self.game_state = States.created
        self.admin_id = message.chat.id

    def started_game_state(self):

        self.game_state = States.started

    def committee_choosing_state(self):

        self.game_state = States.started
        self.game_sub_state = Sub_States.committee_choosing
        self.mission_voters = list()
        self.mission_voters_name = list()

    def committee_voting_state(self):

        self.game_state = States.started
        self.game_sub_state = Sub_States.committee_voting
        self.committee_voters = self.names[:]

        self.committee_votes = list()
        self.committee_summary = str()

    def mission_voting_state(self):

        self.game_state = States.started
        self.game_sub_state = Sub_States.mission_voting
        self.mission_votes = list()

    def assassin_shooting_state(self):

        self.game_state = States.started
        self.game_sub_state = Sub_States.assassin_shooting

    def ended_game_state(self):

        self.initial_condition()

    # rule checkers
    # the following functions check the necessary rules
    # for each message handler. their output is either True or False.

    # Whos Conditions
    def is_admin(self, message):
        print("is_admin")

        c_1 = self.admin_id == message.chat.id
        return c_1

    def is_player(self, message):
        print("is_player")

        c_1 = message.chat.id in self.ids
        return c_1

    def is_commander(self, message):
        print("is_commander")

        c_1 = self.current_commander_id == message.chat.id
        return c_1

    def is_assassin(self, message):
        print("is_assassin")

        c_1 = self.assassin_id == message.chat.id
        return c_1

    # Whens Conditions
    # Main State
    def is_no_game_state(self):
        print("is_no_game_state")

        c_1 = self.game_state == States.no_game
        return c_1

    def is_created_state(self):
        print("is_created_state")

        c_1 = self.game_state == States.created
        return c_1

    def is_started_state(self):
        print("is_started_state")

        c_1 = self.game_state == States.started
        return c_1

    # Whens Conditions
    # Sub States
    def is_committee_choosing_state(self):

        c_1 = self.is_started_state()
        c_2 = self.game_sub_state == Sub_States.committee_choosing

        return c_1 and c_2

    def is_committee_voting_state(self):

        c_1 = self.is_started_state()
        c_2 = self.game_sub_state == Sub_States.committee_voting

        return c_1 and c_2

    def is_mission_voting_state(self):

        c_1 = self.is_started_state()
        c_2 = self.game_sub_state == Sub_States.mission_voting

        return c_1 and c_2

    def is_assassin_shooting_state(self):

        c_1 = self.is_started_state()
        c_2 = self.game_sub_state == Sub_States.assassin_shooting

        return c_1 and c_2

    # Whos, Whens, Whats (Copmlex Conditions)
    def is_admin_choosing_character(self, message):
        print("is_admin_choosing_character")

        # who
        c_1 = self.is_admin(message)

        # when
        c_2 = self.is_created_state()

        # What
        c_3 = message.text in self.optional_characters
        c_4 = message.text in self.checked_optional_characters

        return c_1 and c_2 and (c_3 or c_4)

    def is_admin_starting_game(self, message):

        # who
        c_1 = self.is_admin(message)

        # when
        c_2 = self.is_created_state()

        # what
        c_3 = message.text == Keys.start_game

        return c_1 and c_2 and c_3

    def is_admin_terminating_game(self, message):

        # who
        c_1 = self.is_admin(message)

        # when
        c_2 = self.is_created_state()
        c_3 = self.is_started_state()

        # what
        c_4 = message.text == self.terminating_game_word

        return c_1 and (c_2 or c_3) and c_4

    def is_commander_choosing_name(self, message):
        print("is_commander_choosing_name")

        # who
        c_1 = self.is_commander(message)

        # when
        c_2 = self.is_committee_choosing_state()

        # what
        c_3 = message.text in self.names
        c_4 = message.text in self.checked_names

        return c_1 and c_2 and (c_3 or c_4)

    def is_commander_pressing_button(self, message):
        print("is_commander_pressing_button")

        # who
        c_1 = self.is_commander(message)

        # when
        c_2 = self.is_committee_choosing_state()

        # what
        c_3 = message.text in [Keys.final, Keys.propose]

        return c_1 and c_2 and c_3

    def is_eligible_vote(self, message):
        print("is_eligible_vote")

        # what
        c_1 = self.is_player(message)

        # when
        c_2 = self.is_committee_voting_state()

        # what
        c_3 = emojize(message.text) in [Keys.agree, Keys.disagree]

        return c_1 and c_2 and c_3

    def is_eligible_fail_success(self, message):
        print("is_eligible_fail_success")

        # when
        c_1 = self.is_player(message)

        # who
        c_2 = self.is_mission_voting_state()

        # what
        c_3 = message.text in [Keys.success, Keys.fail]

        return c_1 and c_2 and c_3

    def is_assassin_choosing_name(self, message):
        print("is_assassin_choosing_name")

        # who
        c_1 = self.is_assassin(message)

        # when
        c_2 = self.is_assassin_shooting_state()

        # what
        c_3 = message.text != Keys.assassin_shoots

        return c_1 and c_2 and c_3

    def is_assassin_pressing_button(self, message):
        print("is_assassin_pressing_button")

        # who
        c_1 = self.is_assassin(message)

        # when
        c_2 = self.is_assassin_shooting_state()

        # what
        c_3 = message.text == Keys.assassin_shoots

        return c_1 and c_2 and c_3

    # keyboard makers
    # the following functions make keyboard for players.

    def character_keyboard(self):

        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        buttons = []

        for character in self.optional_characters:

            if character in self.choosed_characters:

                temp_str = demojize(Keys.check_box)

            else:

                temp_str = ""

            buttons.append(types.KeyboardButton(emojize(temp_str + character)))

        keyboard.add(*buttons)
        buttons_last_layers = [Keys.start_game]

        last_layer_buttons = map(types.KeyboardButton, buttons_last_layers)

        keyboard.add(*last_layer_buttons)

        return keyboard

    def join_game_keyboard(self):

        buttons_text = [Keys.join_game]
        buttons = map(types.KeyboardButton, buttons_text)
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        keyboard.add(*buttons)

        return keyboard

    def commander_keyboard(self):

        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

        for name in self.names:

            if name in self.mission_voters:

                temp_str = demojize(Keys.check_box)

            else:

                temp_str = ""

            button = types.KeyboardButton(emojize(f"{temp_str}{name}"))
            keyboard.row(button)

        buttons_str = [Keys.propose, Keys.final]
        buttons = map(types.KeyboardButton, buttons_str)
        keyboard.row(*buttons)

        return keyboard

    def committee_vote_keyboard(self):

        buttons_str = [Keys.agree, Keys.disagree]
        buttons = map(types.KeyboardButton, buttons_str)
        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        keyboard.add(*buttons)
        return keyboard

    def mission_vote_keyboard(self):

        buttons_str = [Keys.success, Keys.fail]
        shuffle(buttons_str)
        buttons = map(types.KeyboardButton, buttons_str)
        keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        keyboard.add(*buttons)
        return keyboard

    def assassin_keyboard(self):

        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

        for name in self.names:

            if self.names_to_ids[name] in self.Evil_team_id:

                continue

            if name == self.assassins_guess:

                temp_str = demojize(Keys.check_box)

            else:

                temp_str = ""

            button = types.KeyboardButton(emojize(f"{temp_str}{name}"))
            keyboard.row(button)

        buttons_str = Keys.assassin_shoots
        buttons = types.KeyboardButton(emojize(buttons_str))
        keyboard.row(buttons)

        return keyboard

    def remove_keyboard(self):
        return types.ReplyKeyboardRemove()

    # Summary Functions
    # the following function are to make summary during the fellow of the game.

    def add_committee_header(self, rejected_count):

        sep = "-" * 15
        return ("\n" + f"Rejection Count: {rejected_count}" +
                "\n" + sep +
                "\n" + "Committee Votes:" +
                "\n")

    def add_committee_vote(self, name, vote):

        return emojize(f"-{name} voted: {vote}" +
                       "\n")

    def add_committee_footer(self):

        sign = Keys.accept if self.game.committee_accept else Keys.declined
        sep = "-" * 15

        return (sep +
                "\n" + "Committee Result:"
                "\n" + sign)

    def add_mission_vote(self, names, fail, success, who_won, Round,
                         commander):
        sep = "-" * 15

        return (f"Round: {Round} (Commander: {commander})" +
                "\n" + sep +
                "\n" + "Committee Memebers:" +
                "\n" + "-" + names +
                "\n" + sep +
                "\n" + "Mission Results:" +
                "\n" + f"# Sucesses: {success}" +
                "\n" + f"# Fails: {fail}")

    def send_committee_summary(self):

        if self.game.committee_accept:

            self.game.reject_count = 0

        else:

            self.game.reject_count += 1

        rejected = self.game.reject_count

        self.committee_summary = (self.add_committee_header(rejected) +
                                  self.committee_summary)
        self.committee_summary += self.add_committee_footer()

        keyboard = self.remove_keyboard()

        for id in self.ids:

            self.bot.send_message(
                id, self.committee_summary, reply_markup=keyboard)

    def send_mission_summary(self):

        Round = self.game.round - 1
        who_won = self.game.who_won
        names = "\n-".join(self.mission_voters_name)
        commander = self.current_commander

        self.all_time_summary.append(
            self.add_mission_vote(names, self.game.fail_count,
                                  self.game.success_count,
                                  who_won, Round, commander))

        keyboard = self.remove_keyboard()

        self.my_wait(0.5)

        for id in self.ids:

            for i in range(len(self.all_time_summary)):

                self.bot.send_message(id, self.all_time_summary[i],
                                      reply_markup=keyboard)


my_bot = Bot()
