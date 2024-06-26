from random import shuffle
from types import SimpleNamespace
from telebot.apihelper import ApiTelegramException

import telebot
from emoji import demojize, emojize
from loguru import logger
from telebot import types

from Constants import Commands, Directories, \
    Keys, PanelM_T, Sub_States, States, \
    GaS_T, Char_T, Ass_T, GaSi_T, Co_T, Vote_T, Oth_T, \
    Panel_Keys

from Engines import Avalon_Engine
from utils.io import read_txt_file

TOKEN = read_txt_file(Directories.Token)


class Bot():

    def __init__(self):

        # Debuding parameters
        self.debug_mode = True

        # Initializing the parameters
        logger.info("Initializing ...")
        self.initial_condition()

        # Defining the bot ...
        logger.info("Defining bot ...")
        self.bot = telebot.TeleBot(TOKEN)

        # defining bot handlders ...
        logger.info("Defining handlers ...")
        self.handlers()

        # Start polling ...
        logger.info("Polling ... ")
        self.bot.infinity_polling()

    def initial_condition(self):

        if self.debug_mode:

            print("initial_condition")

        # # admin parameters
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
        self.id_to_message_id = dict()
        self.id_to_temp_message_id = dict()

        # Panel parameters
        self.panel = SimpleNamespace()
        self.panel.keyboard = self.panel_keyboard()
        self.panel.button_str = self.get_panel_str()

        # Character parameters
        merlin = Char_T.merlin
        assassin = Char_T.assassin
        mordred = Char_T.mordred
        obron = Char_T.oberon
        persival = Char_T.persival_morgana
        # lady = Char_T.lady

        key = Keys.check_box
        self.choosed_characters = [merlin, assassin]
        optional = [obron, mordred, persival]
        self.optional_characters = optional
        self.checked_optional_characters = [f"{key}{i}" for i in optional]

        # commander parameters
        self.commander_order = list()
        self.current_commander = str()
        self.current_commander_id = int()
        self.shuffle_commander_order = False
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
        self.game_summary = str()

    def handlers(self):

        if self.debug_mode:
            print("handlers")

        # Start Command #
        @self.bot.message_handler(commands=[Commands.start])
        def start_command(message):

            if self.debug_mode:

                print("start_command")

            chat_id = message.chat.id
            text = GaS_T.SC
            keyboard = self.join_create_game_keyboard()
            self.bot.send_message(chat_id, text, reply_markup=keyboard)

        # Print Input #
        @self.bot.message_handler()
        def print_function(message):

            if self.debug_mode:

                print("print_function")

            text = Oth_T.NAVC
            chat_id = message.chat.id

            self.bot.send_message(chat_id, text)
            print(demojize(message.text))

        # Create game #
        @self.bot.callback_query_handler(func=self.is_creating_game)
        def create_game(query):

            if self.debug_mode:

                print("create_game")

            chat_id = query.message.chat.id
            query_id = query.id
            message_id = query.message.id

            if self.game_state == States.no_game:

                self.created_game_state(query)
                self.add_player(query)

                names = "\n".join(self.names)
                text = f"{GaS_T.YJGS}{GaS_T.PSF}{names}"
                self.bot.edit_message_text(text, chat_id, message_id)

                text = GaS_T.CHC
                keyboard = self.character_keyboard()
                self.bot.send_message(chat_id, text, reply_markup=keyboard)

            else:

                text = GaS_T.GOG
                self.bot.answer_callback_query(query_id, text, cache_time=5)

        @self.bot.callback_query_handler(func=self.is_joining_game)
        def join_game(query):

            if self.debug_mode:

                print("join_game")

            chat_id = query.message.chat.id
            query_id = query.id
            message_id = query.message.id

            if self.game_state == States.created:

                if chat_id not in self.ids:

                    self.add_player(query)

                    names = "\n".join(self.names)
                    text = f"{GaS_T.YJGS}{GaS_T.PSF}{names}"

                    for chat_id, message_id in self.id_to_message_id.items():

                        self.bot.edit_message_text(text, chat_id, message_id)

                else:

                    text = GaS_T.YAJ
                    self.bot.answer_callback_query(query_id, text)

            elif self.game_state == States.started:

                text = GaS_T.GIOG
                self.bot.answer_callback_query(query_id, text)

            elif self.game_state == States.no_game:

                text = GaS_T.NGSC
                self.bot.answer_callback_query(query_id, text)

        # panel_hit
        @self.bot.callback_query_handler(func=self.is_player_hitting_panel)
        def panel_hit(query):

            if query.data == Panel_Keys.game_info or \
               query.data == Keys.cancle:

                self.panel_show_game_info(query)

            elif query.data == Panel_Keys.commander_order:

                self.panel_show_commander_order(query)

            elif query.data == Panel_Keys.assassin_shoot:

                self.panel_assassin_shoot(query)

            elif query.data == Panel_Keys.lady:

                self.panel_use_lady(query)

        # Choose_character #
        @self.bot.callback_query_handler(func=self.is_admin_choosing_character)
        def Choose_character_query(query):

            if self.debug_mode:

                print("choose_character")

            self.admin_choose_characters(query)

        # Send Info #
        @self.bot.callback_query_handler(func=self.is_admin_starting_game)
        def starting_game_query(query):

            if self.debug_mode:

                print("starting_game_query")

            if self.game_state == States.created:

                self.start_game(query)

            elif self.game_state == States.no_game:

                text = GaS_T.YSCG
                self.bot.answer_callback_query(query.id, text)

            else:

                text = GaS_T.TGHS
                self.bot.answer_callback_query(query.id, text)

        # ccommander choosing name #
        @self.bot.callback_query_handler(func=self.is_commander_choosing_name)
        def commander_choosing_name(query):

            if self.debug_mode:

                print("commander_choosing_name")

            self.commander_choose_name(query)

        # commander pressing button #
        @self.bot.callback_query_handler(
                func=self.is_commander_pressing_button)
        def commander_press_button(query):

            if self.debug_mode:

                print("commander_press_button")

            self.game.check_committee(self.mission_voters)

            if self.game.acceptable_round:

                self.commander_decision(query)

            else:

                self.pick_right_players(query)

        # committee vote #
        @self.bot.callback_query_handler(func=self.is_eligible_vote)
        def vote_for_committee(query):

            if self.debug_mode:

                print("vote_for_committee")

            name = self.ids_to_names[query.message.chat.id]

            if name in self.committee_voters:

                self.committee_voters.remove(name)

                if self.committee_voters:

                    self.handle_committee_vote(query)

                else:

                    self.handle_committee_vote(query)

                    self.id_to_temp_message_id = dict()

                    self.game.count_committee_vote(self.committee_votes)
                    self.send_committee_summary()

                    if self.game.reject_count == 5:

                        self.end_5_reject()

                    elif self.game.committee_accept:

                        self.go_to_mission_voting()

                    else:

                        self.go_to_next_commander()

            else:

                self.you_voted(query)

        # mission vote #
        @self.bot.callback_query_handler(func=self.is_eligible_fail_success)
        def vote_for_mission(query):

            if self.debug_mode:

                print("vote_for_mission")

            name = self.ids_to_names[query.message.chat.id]

            if name in self.mission_voters:

                self.mission_voters.remove(name)

                if self.mission_voters:

                    self.handle_mission_vote(query)

                else:

                    self.handle_mission_vote(query)
                    self.game.mission_result(self.mission_votes)
                    self.send_mission_summary()

                    if self.game.evil_wins == 3:

                        self.end_evil_3_won()

                    elif self.game.city_wins == 3:

                        self.city_3_won()

                    else:

                        self.go_to_next_commander()

            else:

                self.you_voted(query)

        @self.bot.callback_query_handler(func=self.is_assassin_choosing_name)
        def assassin_choosing_name(query):

            if self.debug_mode:

                print("assassin_choosing_name")

            self.assassin_choose_name(query)

        @self.bot.callback_query_handler(func=self.is_assassin_pressing_button)
        def assassin_pressing_button(query):

            if self.debug_mode:

                print("assassin_pressing_button")

            if self.assassins_guess == str():

                self.choose_someone(query)

            else:

                self.end_assassin_shot(query)

        @self.bot.callback_query_handler(func=lambda x: x)
        def delete_inline_keyboards(query):

            if self.debug_mode:

                print("delete_inline_keyboard")

            chat_id = query.message.chat.id
            message_id = query.message.id

            if self.game_state == States.no_game:

                self.bot.delete_message(chat_id, message_id)

            else:

                word_list = [Keys.fail, Keys.success,
                             Keys.agree, Keys.disagree,
                             *self.names, *self.checked_names,
                             *self.optional_characters,
                             *self.checked_optional_characters]

                if query.data in word_list:

                    self.bot.answer_callback_query(query.id, Oth_T.TA)

                else:

                    self.bot.delete_message(chat_id, message_id)

    # auxilary functions. They help functionalize the code.
    def send_all(self, text):

        for id in self.ids:

            self.bot.send_message(id, text)

    def edit_one(self, query_id, chat_id, text=None,
                 keyboard=None, message_id=None):

        if text is None:

            if message_id is None:
                message_id = self.id_to_message_id[chat_id]

            if keyboard is None:
                keyboard = self.panel.keyboard

            try:

                self.bot.edit_message_reply_markup(chat_id, message_id,
                                                   reply_markup=keyboard)

            except ApiTelegramException:

                text = PanelM_T.AR
                self.bot.answer_callback_query(query_id, text)
                print("\nsimilar request\n")

        else:

            if message_id is None:
                message_id = self.id_to_message_id[chat_id]

            if keyboard is None:
                keyboard = self.panel.keyboard

            try:

                self.bot.edit_message_text(text, chat_id, message_id,
                                           reply_markup=keyboard)

            except ApiTelegramException:

                text = PanelM_T.AR
                self.bot.answer_callback_query(query_id, text)
                print("\nsimilar request\n")

    def get_panel_str(self):

        panel_strs = list()

        for item in vars(Panel_Keys):

            attr = Panel_Keys.__getattribute__(item)

            if isinstance(attr, list):

                for single_attr in attr:

                    panel_strs.append(single_attr)

            else:

                panel_strs.append(attr)

        return panel_strs

    def panel_show_game_info(self, query):

        chat_id = query.message.chat.id
        query_id = query.id
        big_sep = GaS_T.big_sep

        character = self.game.names_to_characters[self.ids_to_names[chat_id]]
        role_text = (GaS_T.IGI +
                     "\n" + big_sep +
                     "\n" + GaS_T.YR +
                     "\n" + "-" + self.game.all_messages[character.name])

        game_info_text = (self.game.character_in_game +
                          big_sep +
                          "\n" + "Board:" + self.add_round_info())

        text = (role_text +
                "\n" + big_sep +
                "\n" + game_info_text)

        self.edit_one(query_id, chat_id, text)

    def panel_show_commander_order(self, query):

        chat_id = query.message.chat.id
        query_id = query.id
        text = self.make_commander_order_message(1)

        self.edit_one(query_id, chat_id, text)

    def panel_assassin_shoot(self, query):

        chat_id = query.message.chat.id
        query_id = query.id

        if chat_id == self.assassin_id:

            text = Ass_T.ASS1
            keyboard = self.assassin_keyboard()
            self.edit_one(query_id, chat_id, text, keyboard=keyboard)

        else:

            text = PanelM_T.ASE
            self.bot.answer_callback_query(query_id, text)

    def panel_use_lady(self, query):

        text = PanelM_T.CS
        query_id = query.id
        self.bot.answer_callback_query(query_id, text)

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

    def add_player(self, query):

        message = query.message
        chat_id = query.message.chat.id
        message_id = query.message.id

        name = self.grab_name(message)
        temp_name = name

        similar_name_count = 0

        while True:

            if temp_name in self.names:

                similar_name_count += 1
                temp_name = f"{name}_{similar_name_count}"

            else:

                name = temp_name
                break

        self.names.append(name)
        self.ids.append(chat_id)

        self.checked_names.append(emojize(f"{Keys.check_box}{name}"))

        self.names_to_ids[name] = chat_id
        self.ids_to_names[chat_id] = name
        self.id_to_message_id[chat_id] = message_id

    def admin_choose_characters(self, query):

        chat_id = query.message.chat.id
        message_id = query.message.id
        query_id = query.id

        add_remove_name = self.fix_name(query.data)

        if add_remove_name in self.choosed_characters:

            self.choosed_characters.remove(add_remove_name)
            text = f"{add_remove_name}{GaS_T.RFG}"

        else:

            self.choosed_characters.append(add_remove_name)
            text = f"{add_remove_name}{GaS_T.ATG}"

        self.bot.answer_callback_query(query.id, text)

        keyboard = self.character_keyboard()
        self.edit_one(query_id, chat_id,
                      keyboard=keyboard, message_id=message_id)

    def define_game(self):

        name_for_game = self.names[:]
        character_for_game = self.choosed_characters[:]
        self.game = Avalon_Engine(name_for_game, character_for_game)

    def send_info(self, query):

        self.define_game()
        self.started_game_state()

        chat_id = query.message.chat.id
        query_id = query.id
        message_id = query.message.id

        self.bot.delete_message(chat_id, message_id)

        big_sep = GaS_T.big_sep

        for name, character in self.game.names_to_characters.items():

            if character.name == Char_T.assassin:
                self.assassin_id = self.names_to_ids[name]

            chat_id = self.names_to_ids[name]

            text = (GaS_T.IGI +
                    "\n" + big_sep +
                    "\n" + GaS_T.YR +
                    "\n" + "-" + self.game.all_messages[character.name] +
                    "\n" + big_sep +
                    "\n" + self.game.character_in_game +
                    big_sep +
                    "\n" + "Board:" + self.add_round_info())

            self.edit_one(query_id, chat_id, text)

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

    def add_round_info(self):

        round_info = str()
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

                else:

                    text = f"{Keys.evil_win}"

                round_info += sign
                round_info += f"{text: ^7}"

        return round_info

    def make_commander_order_message(self, offset):

        commander_order_show = str()

        for index, name in enumerate(self.commander_order):

            if index == self.commander_number - offset:

                commander_order_show += emojize(f"-{name} --> (:crown:)\n")

            else:

                commander_order_show += f"-{name}\n"

        text = emojize(f"{Co_T.CO} \n" + commander_order_show)

        return text

    def go_to_next_commander(self):

        self.committee_choosing_state()
        self.make_commander_order()
        self.resolve_commander()

        n_committee = self.game.all_round[self.game.round]

        text = f"{Co_T.CCN1}{Co_T.CCN2_1}{n_committee}{Co_T.CCN2_2}"
        keyboard = self.commander_keyboard()

        self.bot.send_message(self.current_commander_id,
                              text, reply_markup=keyboard)

    def start_game(self, query):

        try:

            self.send_info(query)
            self.go_to_next_commander()

        except ValueError as e:

            query_id = query.id
            self.bot.answer_callback_query(query_id, e.args[0])

    def transfer_committee_vote(self, query):

        if query.data == Keys.agree:
            self.committee_votes.append(1)

        elif query.data == Keys.disagree:
            self.committee_votes.append(0)

    def transfer_mission_vote(self, query):

        if query.data == Keys.success:
            self.mission_votes.append(1)

        elif query.data == Keys.fail:
            self.mission_votes.append(0)

    def commander_choose_name(self, query):

        query_id = query.id
        chat_id = query.message.chat.id
        message_id = query.message.id

        add_remove_name = self.fix_name(query.data)

        if add_remove_name in self.mission_voters:

            self.mission_voters.remove(add_remove_name)
            text = f"{add_remove_name}{Co_T.RFC}"

        else:

            self.mission_voters.append(add_remove_name)
            text = f"{add_remove_name}{Co_T.ATC}"

        self.bot.answer_callback_query(query_id, text)

        keyboard = self.commander_keyboard()

        self.edit_one(query_id, chat_id,
                      keyboard=keyboard, message_id=message_id)

    def commander_decision(self, query):

        text = f"{Co_T.PCC}\n-" + "\n-".join(self.mission_voters)
        keyboard = self.committee_vote_keyboard()
        self.bot.delete_message(query.message.chat.id, query.message.id)

        for id in self.ids:
            self.bot.send_message(id, text, reply_markup=keyboard)

        self.committee_voting_state()

    def pick_right_players(self, query):

        query_id = query.id
        n_committee = self.game.all_round[self.game.round]
        text = f"{Co_T.CCN2_1}{n_committee}{Co_T.CCN2_2}"

        self.bot.answer_callback_query(query_id, text)

    def go_to_mission_voting(self):

        text = Vote_T.MV

        for name in self.mission_voters:

            self.mission_voters_name.append(name)
            chat_id = self.names_to_ids[name]
            keyboard = self.mission_vote_keyboard()

            self.bot.send_message(chat_id, text, reply_markup=keyboard)

        self.mission_voting_state()

    def handle_committee_vote(self, query):

        self.transfer_committee_vote(query)

        chat_id = query.message.chat.id
        message_id = query.message.id
        query_id = query.id

        query_text = emojize(f"{Vote_T.CV}{query.data}")
        self.bot.answer_callback_query(query_id, query_text)

        self.id_to_temp_message_id[chat_id] = message_id

        if len(self.id_to_temp_message_id) == len(self.names):

            for chat_id, message_id in self.id_to_temp_message_id.items():
                self.bot.delete_message(chat_id, message_id)

        else:

            text = Vote_T.PTV + "-" + "\n-".join(self.committee_voters)
            keyboard = self.committee_vote_keyboard()

            for chat_id, message_id in self.id_to_temp_message_id.items():
                self.edit_one(query_id, chat_id, text,
                              keyboard=keyboard, message_id=message_id)

        name = self.ids_to_names[chat_id]
        self.committee_summary += self.add_committee_vote(name, query.data)

    def handle_mission_vote(self, query):

        self.transfer_mission_vote(query)

        chat_id = query.message.chat.id
        message_id = query.message.id
        text = Vote_T.SFV

        self.bot.answer_callback_query(query.id, text)
        self.bot.delete_message(chat_id, message_id)

    def you_voted(self, query):

        query_id = query.id
        text = emojize(Vote_T.YVB)

        self.bot.answer_callback_query(query_id, text)

    def city_3_won(self):

        self.assassin_shooting_state()
        text = GaSi_T.CW3R

        self.send_all(text)

        text = Ass_T.ASS1
        keyboard = self.assassin_keyboard()

        self.bot.send_message(self.assassin_id, text, reply_markup=keyboard)

    def assassin_choose_name(self, query):

        query_id = query.id
        chat_id = query.message.chat.id
        message_id = query.message.id

        self.assassins_guess = self.fix_name(query.data)
        text = emojize(f"{Ass_T.ASS2_1}{self.assassins_guess}{Ass_T.ASS2_2}")
        self.bot.answer_callback_query(query_id, text)

        keyboard = self.assassin_keyboard()
        self.edit_one(query_id, chat_id,
                      keyboard=keyboard, message_id=message_id)

    def choose_someone(self, query):

        query_id = query.id
        text = Ass_T.ASS3
        self.bot.answer_callback_query(query_id, text)

    def end_assassin_shot(self, query):

        chat_id = query.message.chat.id
        message_id = query.message.id
        self.bot.delete_message(chat_id, message_id)

        self.game.assassin_shoot(self.assassins_guess)

        if self.game.assassin_shooted_right:

            text = (f"{GaSi_T.EW}{GaSi_T.REW2}" +
                    "\n" + f"{GaSi_T.ASG}{self.assassins_guess}")

        else:

            text = (f"{GaSi_T.CW}{GaSi_T.RCW}" +
                    "\n" + f"{GaSi_T.ASG}{self.assassins_guess}")

        self.send_all(text)
        self.ended_game_state()

    def end_evil_3_won(self):

        text = f"{GaSi_T.EW}{GaSi_T.REW3}"
        self.send_all(text)
        self.ended_game_state()

    def end_5_reject(self):

        text = f"{GaSi_T.EW}{GaSi_T.REW1}"
        self.send_all(text)
        self.ended_game_state()

    def show_all_characters(self):

        text = str()

        for name, character in self.game.names_to_characters.items():

            text += f"{name} --> {character.name}\n"

        self.send_all(text)

    # State functions
    # These functions help keep track of the state during the game.

    def created_game_state(self, query):

        self.game_state = States.created
        self.admin_id = query.message.chat.id

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

        self.show_all_characters()
        self.initial_condition()

    # rule checkers

    # Whos Condition
    def is_admin(self, query):

        c_1 = self.admin_id == query.message.chat.id

        return c_1

    def is_creating_game(self, query):

        c_1 = query.data == Keys.create_game

        return c_1

    def is_joining_game(self, query):

        c_1 = query.data == Keys.join_game

        return c_1

    def is_player(self, query):

        c_1 = query.message.chat.id in self.ids

        return c_1

    def is_commander(self, query):

        c_1 = self.current_commander_id == query.message.chat.id

        return c_1

    def is_assassin(self, query):

        c_1 = self.assassin_id == query.message.chat.id

        return c_1

    # Whens Conditions
    # Main State
    def is_no_game_state(self):

        c_1 = self.game_state == States.no_game

        return c_1

    def is_created_state(self):

        c_1 = self.game_state == States.created

        return c_1

    def is_started_state(self):

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

    # Whos, Whens, Whats
    # Copmlex Conditions
    def is_player_hitting_panel(self, query):

        # who
        c_1 = self.is_player(query)

        # when
        c_2 = True

        # what
        c_3 = query.data in self.panel.button_str
        c_4 = query.data == Keys.cancle

        return c_1 and c_2 and (c_3 or c_4)

    def is_admin_starting_game(self, query):

        # who
        c_1 = self.is_admin(query)

        # when
        c_2 = self.is_created_state()

        # what
        c_3 = query.data == Keys.start_game

        return c_1 and c_2 and c_3

    def is_admin_choosing_character(self, query):

        # who
        c_1 = self.is_admin(query)

        # when
        c_2 = self.is_created_state()

        # What
        c_3 = query.data in self.optional_characters
        c_4 = query.data in self.checked_optional_characters

        return c_1 and c_2 and (c_3 or c_4)

    def is_commander_choosing_name(self, query):

        # who
        c_1 = self.is_commander(query)

        # when
        c_2 = self.is_committee_choosing_state()

        # what
        c_3 = query.data in self.names
        c_4 = query.data in self.checked_names

        return c_1 and c_2 and (c_3 or c_4)

    def is_commander_pressing_button(self, query):

        # who
        c_1 = self.is_commander(query)

        # when
        c_2 = self.is_committee_choosing_state()

        # what
        c_3 = query.data == Keys.final

        return c_1 and c_2 and c_3

    def is_eligible_vote(self, query):

        # what
        c_1 = self.is_player(query)

        # when
        c_2 = self.is_committee_voting_state()

        # what
        c_3 = query.data in [Keys.agree, Keys.disagree]

        return c_1 and c_2 and c_3

    def is_eligible_fail_success(self, query):

        # when
        c_1 = self.is_player(query)

        # who
        c_2 = self.is_mission_voting_state()

        # what
        c_3 = query.data in [Keys.success, Keys.fail]

        return c_1 and c_2 and c_3

    def is_assassin_choosing_name(self, query):

        # who
        c_1 = self.is_assassin(query)

        # when
        c_2 = True

        # what
        c_3 = query.data != Keys.assassin_shoots

        return c_1 and c_2 and c_3

    def is_assassin_pressing_button(self, query):

        # who
        c_1 = self.is_assassin(query)

        # when
        c_2 = True

        # what
        c_3 = query.data == Keys.assassin_shoots

        return c_1 and c_2 and c_3

    # keyboard makers
    # the following functions make keyboard for players.

    def join_create_game_keyboard(self):

        keyboard = types.InlineKeyboardMarkup()
        buttons = list()

        cg = Keys.create_game
        jg = Keys.join_game

        buttons.append(types.InlineKeyboardButton(cg, callback_data=cg))
        buttons.append(types.InlineKeyboardButton(jg, callback_data=jg))

        keyboard.row(*buttons)

        return keyboard

    def character_keyboard(self):

        keyboard = types.InlineKeyboardMarkup()

        for character in self.optional_characters:

            if character in self.choosed_characters:

                temp_str = demojize(Keys.check_box)

            else:

                temp_str = ""

            button = emojize(f"{temp_str}{character}")
            inline = types.InlineKeyboardButton(button, callback_data=button)

            keyboard.row(inline)

        start = Keys.start_game
        inline = types.InlineKeyboardButton(start, callback_data=start)
        keyboard.add(inline)

        return keyboard

    def panel_keyboard(self):

        keyboard = types.InlineKeyboardMarkup()

        for item in vars(Panel_Keys):

            attr = Panel_Keys.__getattribute__(item)
            inline = types.InlineKeyboardButton(attr, callback_data=attr)
            keyboard.row(inline)

        return keyboard

    def commander_keyboard(self):

        keyboard = types.InlineKeyboardMarkup()

        for name in self.names:

            if name in self.mission_voters:

                temp_str = demojize(Keys.check_box)

            else:

                temp_str = ""

            button = emojize(f"{temp_str}{name}")
            inline = types.InlineKeyboardButton(button, callback_data=button)
            keyboard.row(inline)

        final = Keys.final
        f_inline = types.InlineKeyboardButton(final, callback_data=final)
        keyboard.add(f_inline)

        return keyboard

    def committee_vote_keyboard(self):

        keyboard = types.InlineKeyboardMarkup(row_width=2)

        agree = Keys.agree
        disagree = Keys.disagree
        a_inline = types.InlineKeyboardButton(agree, callback_data=agree)
        d_inline = types.InlineKeyboardButton(disagree, callback_data=disagree)

        keyboard.add(a_inline, d_inline)
        return keyboard

    def mission_vote_keyboard(self):

        keyboard = types.InlineKeyboardMarkup(row_width=2)

        sucess = Keys.success
        fail = Keys.fail

        s_inline = types.InlineKeyboardButton(sucess, callback_data=sucess)
        f_inline = types.InlineKeyboardButton(fail, callback_data=fail)

        inline_buttons = [s_inline, f_inline]
        shuffle(inline_buttons)

        keyboard.add(*inline_buttons)

        return keyboard

    def assassin_keyboard(self):

        keyboard = types.InlineKeyboardMarkup(row_width=2)

        for name in self.names:

            if name == self.assassins_guess:

                temp_str = demojize(Keys.check_box)

            else:

                temp_str = ""

            button = emojize(f"{temp_str}{name}")
            inline = types.InlineKeyboardButton(button, callback_data=button)
            keyboard.row(inline)

        if not self.is_assassin_shooting_state():

            assassin = Keys.assassin_shoots
            cancle = Keys.cancle

            ainline = types.InlineKeyboardButton(assassin,
                                                 callback_data=assassin)
            cinline = types.InlineKeyboardButton(cancle, callback_data=cancle)

            keyboard.row(ainline, cinline)

        else:

            assassin = Keys.assassin_shoots
            ainline = types.InlineKeyboardButton(assassin,
                                                 callback_data=assassin)
            keyboard.row(ainline)

        return keyboard

    # Summary Functions
    # the following function are to make summary during the fellow of the game.

    def add_committee_header(self, Round, rejected_count):

        sep = GaS_T.small_sep
        return ("\n" + f"Round: {Round}, Rejection Count: {rejected_count}" +
                "\n" + sep +
                "\n" + "Committee Votes:" +
                "\n")

    def add_committee_vote(self, name, vote):

        return emojize(f"-{name} voted: {vote}" +
                       "\n")

    def add_committee_footer(self):

        sign = Keys.accept if self.game.committee_accept else Keys.declined
        sep = GaS_T.small_sep

        return (sep +
                "\n" + "Committee Result:"
                "\n" + sign)

    def add_mission_vote(self, names, fail, success, Round, commander):
        sep = GaS_T.small_sep

        return (f"Round: {Round} (Commander: {commander})" +
                "\n" + sep +
                "\n" + "Committee Memebers:" +
                "\n" + "-" + names +
                "\n" + sep +
                "\n" + "Mission Results:" +
                "\n" + f"-Sucesses: {success}" +
                "\n" + f"-Fails: {fail}" +
                "\n" + sep +
                "\n" + f"Board: {self.add_round_info()}" +
                "\n" + sep +
                "\n" + self.make_commander_order_message(0))

    def send_committee_summary(self):

        if self.game.committee_accept:

            self.game.reject_count = 0

        else:

            self.game.reject_count += 1

        rejected = self.game.reject_count
        Round = self.game.round

        self.committee_summary = (self.add_committee_header(Round, rejected) +
                                  self.committee_summary)

        self.committee_summary += self.add_committee_footer()

        self.send_all(self.committee_summary)

    def send_mission_summary(self):

        Round = self.game.round - 1
        names = "\n-".join(self.mission_voters_name)
        commander = self.current_commander
        self.game_summary = self.add_mission_vote(names, self.game.fail_count,
                                                  self.game.success_count,
                                                  Round, commander)

        self.send_all(self.game_summary)


my_bot = Bot()
