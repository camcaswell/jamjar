class Person:
    def __init__(self, ID, TZ, EXP, T1, T2):
        self.ID = ID
        self.TZ = TZ % 24
        self.EXP = EXP
        self.T1 = T1
        self.T2 = False if T1 else T2
        self.team = None

    def __eq__(self, other):
        return self.ID == other.ID

    def __hash__(self):
        return hash(self.ID)

    def __repr__(self):
        return f"Person({self.ID}, TZ={self.TZ}, EXP={self.EXP}, {self.T1}, {self.T2}, {self.team})"
