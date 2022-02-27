
import logging
import random
from collections import defaultdict
from math import exp
import pandas as pd
from typing import Any, Union

from load import load_data
from person import Person
from rack import Rack
from team import Team


def tz_range(tzs: Union[float, int]) -> Union[float, int]:
    """ Size of minimum window in which all the timezones fit.
        All timezones should be positive offsets.
    """
    tzs = tuple(tzs)
    gaps = [b-a for a,b in zip(tzs, tzs[1:])]
    gaps.append(tzs[0] - tzs[-1] + 24)
    return max(gaps)


class Cooler():
    """ A class for finding low-energy states of team assignment
    """
    def __init__(self, people, size_target, tz_penalty, exp_penalty, size_penalty, lead_penalty, max_temp, start_temp=None, init_team_size=1):

        self.max_temp = max_temp
        if start_temp is None:
            start_temp = self.max_temp
        self.temp = start_temp

        self.size_target = size_target
        self.people = tuple(people)
        self.avg_exp = sum(person.EXP for person in self.people) / len(self.people)

        # Weight coefficients for the energy function
        total_pen = tz_penalty + exp_penalty + size_penalty + lead_penalty
        self.tz_penalty = tz_penalty / total_pen
        self.exp_penalty = exp_penalty / total_pen
        self.size_penalty = size_penalty / total_pen
        self.lead_penalty = lead_penalty / total_pen

        self.teams = Rack()
        for i in range(len(self.people)//init_team_size):
            team = Team(self.people[init_team_size*i:init_team_size*(i+1)])
            team_idx = self.teams.push(team)
            for person in team:
                person.team = team_idx
        
        # for idx, team in self.teams.items():
        #     for person in team:
        #         assert person.team == idx
        #         assert self.teams[person.team] == team
        #         assert person in self.teams[person.team]

        # for person in self.people:
        #     person.team = self.teams.push(Team([person]))
        
        self.telemetry = pd.DataFrame(
            columns=("global_energy", "change_accepted", "delta", "avg_size")
        )

    def record(self, col: str, value: Any) -> None:
        self.telemetry.at[self.iteration, col] = value

    def cool(self, log : bool = False, record: bool = False) -> None:
        """ Make state changes to the team assignments that, on the whole, reduce its energy level.
            There is an ambient temperature that gradually reduces over time.
            Higher ambient temperature allows more postive-energy state changes.
        """


        self.log = log
        # if self.log:
        #     #open("cooling.log", "w").close()
        logging.basicConfig(filename="cooling.log", level=logging.DEBUG)

        self.iteration = 0
        while self.temp > 0:

            candidate = self.pick_neighbor()
            accepted = self.pswap(candidate)

            #if self.log:
            logging.info(f"STATE CHANGE: {'accepted' if accepted else 'rejected'}")
            logging.info(f"ENERGY LEVEL: {self.energy_levels()}")
            if record:
                levels = self.energy_levels()
                self.record("exp_pen", levels["exp"])
                self.record("size_pen", levels["size"])
                self.record("tz_pen", levels["tz"])
                self.record("lead_pen", levels["leader"])
                self.record("change_accepted", int(accepted))
                self.record("global_energy", sum(levels.values()))
                self.record("avg_size", len(self.people)/len(self.teams))

            self.reduce_temp()
            self.iteration += 1

    def reduce_temp(self) -> None:
        """ Function for reducing the ambient temperature.
        """
        self.temp -= 1

    def energy_levels(self) -> dict[str, float]:
        """ Calculate the energy level of the current state.
        """
        exp_en = 0
        tz_en = 0
        size_en = 0
        leaderless_en = 0
        for team in self.teams:
            size = len(team)
            exp_en += abs(sum(p.EXP for p in team)/size - self.avg_exp)
            tz_en += tz_range(p.TZ for p in team)
            size_en += abs(size - self.size_target)
            leaderless_en += (not any(p.T1 or p.T2 for p in team)) * size
        #return (self.exp_penalty*exp_en + self.tz_penalty*tz_en + self.size_penalty*size_en + self.lead_penalty*leaderless_en) / len(self.teams)
        return {
            "exp": self.exp_penalty*exp_en,
            "tz": self.tz_penalty*tz_en,
            "size": self.size_penalty*size_en,
            "leader": self.lead_penalty*leaderless_en,
        }

    def local_energy_level(self, team: Team) -> float:
        """ Overall energy level is a simple average of the energy levels of the teams,
            so we can calculate local energy levels if we want, i.e. to find energy deltas without redundant calculation.
            Note that this function does **NOT** divide by the number of teams, so this measure is **NOT** immediately commensurable with the global enery level.
            This is because this is used to help calculate the energy delta of a state change, which might involve creating or destroying a team.
        """
        if team.energy is None:
            team.energy = sum(self.local_energy_audit(team).values())
        return team.energy
    
    def local_energy_audit(self, team: Team) -> dict[str, float]:
        size = len(team)
        if size == 0:
            return {
                "exp": 0,
                "tz": 0,
                "size": 0,
                "leader": 0,
            }
        exp_en = abs(sum(p.EXP for p in team)/size - self.avg_exp)
        tz_en = max(p.TZ for p in team) - min(p.TZ for p in team)
        size_en = abs(size - self.size_target)
        leaderless_en = not any(p.T1 or p.T2 for p in team)
        return {
                "exp": self.exp_penalty * exp_en * size,
                "tz": self.tz_penalty * tz_en * size,
                "size": self.size_penalty * size_en * size,
                "leader": self.lead_penalty * leaderless_en * size,
        }
    

    def pick_neighbor(self) -> tuple[Person, int]:
        """ Pick a neighbor state as a candidate for a jump.
            In this context it means choosing a person to move, or two people to swap.
            Whether the state change actually happens is subject to `pswap`
        """
        while (candidate := random.choice(self.people)).T1: pass     # don"t touch Tier 1 leaders

        destination_idx = random.choice(tuple(self.teams.keys()))
        assert destination_idx in self.teams.keys()

        return candidate, -1 if candidate.team == destination_idx else destination_idx  # -1 means found a new team

    def energy_delta(self, candidate: Person, destination: Team, new_team_flag: bool) -> float:
        """ Calculate the hypothetical energy delta of the proposed change.
        """
        if self.teams[candidate.team] is destination:
            return 0
        home = self.teams[candidate.team]
        destination_pre = self.local_energy_level(destination)
        home_pre = self.local_energy_level(home)
        home_post = self.local_energy_level(Team([p for p in home if p != candidate]))
        destination_post = self.local_energy_level(destination + [candidate])
        home.hypothetical = home_post
        destination.hypothetical = destination_post
        # count_pre = len(self.teams)
        # count_post = count_pre + new_team_flag - (len(home)==1)
        energy_pre = (home_pre + destination_pre)#/count_pre
        energy_post = (home_post + destination_post)#/count_post
        return energy_post - energy_pre

    def pswap(self, change: tuple[Person, int]) -> bool:
        """ Execute the given state change with a certain probability.
            The probability depends on the energy delta of the change and the current ambient temperature.
        """
        candidate, destination_idx = change
        home_idx = candidate.team
        home = self.teams[home_idx]
        new_team_flag = destination_idx == -1  # if candidate is starting a new team
        if new_team_flag:
            destination = Team()
        else:
            destination = self.teams[destination_idx]

        assert home != destination
        assert home_idx != destination_idx

        #print(f"{temp=}; {MAX_TEMP=}; {delta=}")
        delta = self.energy_delta(candidate, destination, new_team_flag)
        if delta <= 0 or random.random() < exp(-delta/(10*self.temp/self.max_temp)):
            if new_team_flag:
                destination_idx = self.teams.push(destination)
            home.realize_hypothetical()
            destination.realize_hypothetical()
            destination.add(candidate)
            candidate.team = destination_idx
            home.remove(candidate)
            if not home:
                del self.teams[home_idx]
            self.record("delta", delta)
            return True
        return False

    def print_teams(self):
        with open("final_teams.txt", "w") as file:
            file.write(f"{len(self.teams)} teams formed\n")
            for team in self.teams:
                file.write(f"||{len(team)}||\n")
                for person in team:
                    file.write(f"{repr(person)}\n")
                file.write("\n")


""" Shortest path from initial to optimal state is ~  len(people) * (1 - 1/SIZE_TARGET)
    For context when choosing iteration limit (shortest path is of course highly non-obvious, so make sure to allow for significantly more steps)
"""
if __name__ == "__main__":
    people = load_data()
    logging.info(f"{len(people)} participants")

    cooler = Cooler(
        people,
        size_target=5.5,
        tz_penalty=900,
        exp_penalty=15000,
        size_penalty=2000,
        lead_penalty=2000,
        max_temp=400_00,
    )

    cooler.cool(log=True)
    cooler.print_teams()
