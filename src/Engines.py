import random

from Characters import (Assassin, King, Merlin, Minion, Mordred, Morgana,
                        Oberon, Persival, Servant)


class Avalon_Engine():

    def __init__(self, names, prefered_characters=None):
        
        if prefered_characters is []: 
            prefered_characters = None

        self.names = names
        self.prefered_characters = prefered_characters

        self.round = 0
        self.city_wins = 0
        self.evil_wins = 0
        self.reject_count = 0
        self.win_side = "Not Determined"

        self.continues = True
        self.acceptable_round = False
        self.committee_accept = False
        self.king_guessed_right = False
        self.assassin_shooted_right = False

        self.round_info()
        self.character_assignment()
        self.character_message()

    def round_info(self):

        if len(self.names) == 5:
            self.all_round = [2, 3, 2, 3, 3]
            self.two_fails = False

        elif len(self.names) == 6:
            self.all_round = [2, 3, 4, 3, 4]
            self.two_fails = False

        elif len(self.names) == 7:
            self.all_round = [2, 3, 3, 4, 4]
            self.two_fails = True

        elif len(self.names) == 8:
            self.all_round = [3, 4, 4, 5, 5]
            self.two_fails = True

        elif len(self.names) == 9:
            self.all_round = [3, 4, 4, 5, 5]
            self.two_fails = True

        elif len(self.names) == 10:
            self.all_round = [3, 4, 4, 5, 5]
            self.two_fails = True
    
    def count_side(self):

        current_city = 0
        current_evil = 0

        for character in self.game_character:

            if character.side == "City":

                current_city += 1

            elif character.side == "Evil":
                current_evil += 1

        return current_city, current_evil

    def power_character(self):

        self.game_character = [Assassin(), Merlin()]

        if self.prefered_characters is not None:

            if "Persival and Morgana" in self.prefered_characters:

                self.game_character.append(Morgana())
                self.game_character.append(Persival())

            if "Mordred" in self.prefered_characters:

                self.game_character.append(Mordred())

            if "King" in self.prefered_characters:

                self.game_character.append(King())

            if "Oberon" in self.prefered_characters:

                self.game_character.append(Oberon())

    def non_power_characters(self, n_city, n_evil):

        current_city, current_evil = self.count_side()
        city_diff = n_city - current_city
        evil_diff = n_evil - current_evil

        if city_diff >= 0 and evil_diff >= 0:

            for _ in range(city_diff):
                self.game_character.append(Servant())

            for _ in range(evil_diff):
                self.game_character.append(Minion())
        else:
            message = "Number of characters does not "\
                      "match the number of players."
            raise ValueError(message)

    def resolve_character(self):

        self.power_character()

        if len(self.game_character) > len(self.names):

            message = "Number of characters are more than number of players :)"
            raise ValueError(message)

        else:

            if len(self.names) == 5:

                n_city = 3
                n_evil = 2
                self.non_power_characters(n_city, n_evil)

            elif len(self.names) == 6:

                n_city = 4
                n_evil = 2
                self.non_power_characters(n_city, n_evil)

            elif len(self.names) == 7:

                n_city = 4
                n_evil = 3
                self.non_power_characters(n_city, n_evil)

            elif len(self.names) == 8:

                n_city = 5
                n_evil = 3
                self.non_power_characters(n_city, n_evil)

            elif len(self.names) == 9:

                n_city = 6
                n_evil = 3
                self.non_power_characters(n_city, n_evil)

            elif len(self.names) == 10:

                n_city = 6
                n_evil = 4
                self.non_power_characters(n_city, n_evil)

    def character_assignment(self):

        self.resolve_character()
        self.assigned_character = dict()
        self.string_character = []

        random.shuffle(self.names)

        for index, name in enumerate(self.names):

            self.assigned_character[name] = self.game_character[index]
            self.string_character.append(self.game_character[index].name)

    def character_message(self):

        self.all_info = dict()
        self.all_info["King"] = []
        self.all_info["Merlin"] = []
        self.all_info["Persival"] = []
        self.all_info["Evil_Team"] = []

        for name, character in self.assigned_character.items():

            if (character.side == "Evil") and (character.name != "Oberon"):

                self.all_info["Evil_Team"].append(name)

            if (character.side == "Evil") and (character.name != "Mordred"):

                self.all_info["Merlin"].append(name)

            if (character.side == "Evil"):

                self.all_info["King"].append(name)

        if "Persival" in self.string_character:

            for name, character in self.assigned_character.items():

                Persival_Condition_1 = character.name == "Merlin"
                Persival_Condition_2 = character.name == "Morgana"

                if (Persival_Condition_1) or (Persival_Condition_2):
                    self.all_info["Persival"].append(name)

            random.shuffle(self.all_info["Persival"])

    def check_committee(self, committee_names):

        if len(committee_names) == self.all_round[self.round]:
            self.acceptable_round = True

    def count_committee_vote(self, committee_votes):

        negative_votes = committee_votes.count(0)
        positive_votes = committee_votes.count(1)

        if positive_votes>= negative_votes:

            self.committee_accept = True
            self.reject_count = 0

        else:

            self.committee_accept = False
            self.reject_count += 1

    def mission_result(self, mission_votes):

        self.fail_count = mission_votes.count(0)
        self.success_count = mission_votes.count(1)

        condition_1 = self.round  == 3
        condition_2 = self.two_fails == True

        if (condition_1) and (condition_2):

            if self.fail_count >= 2:

                self.evil_wins += 1

            else:

                self.city_wins += 1

        else:

            if self.fail_count >= 1:

                self.evil_wins += 1

            else:

                self.city_wins += 1

    def king_guess(self, guesses):
        
        king_point = 0

        for name in guesses:

            if name in self.all_info["King"]:

                king_point += 1

        if king_point == len(self.all_info["King"]):

            self.king_guessed_right = True

    def assassin_shoot(self, shooted_name):

        if self.assigned_character[shooted_name].name == "Merlin":
            self.assassin_shooted_right = True