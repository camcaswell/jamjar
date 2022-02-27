
class Team():
    def __init__(self, iterable=None):
        if iterable is None:
            iterable = []
        self._members = set(iterable)
        self.energy = None
        self.hypothetical = None  # cache calculated hypothetical energy values
    
    def add(self, person):
        if person in self._members:
            raise ValueError(f"{person} is already on that team")
        self._members.add(person)
        self.energy = None # needs recalculating, depending on Cooler for that logic
        self.hypothetical = None

    
    def remove(self, person):
        self._members.remove(person)
        self.energy = None # needs recalculating, depending on Cooler for that logic
        self.hypothetical = None


    def realize_hypothetical(self):
        if self.hypothetical is None:
            raise Exception("No stored hypothetical energy value")
        self.energy = self.hypothetical
        self.hypothetical = None
    
    def __iter__(self):
        return iter(self._members)
    
    def __eq__(self, other):
        return self._members == other._members
    
    def __len__(self):
        return len(self._members)
    
    def __add__(self, other):
        return Team(self._members | set(other))
    
    def __radd__(self, other):
        return self + other
    
    def __repr__(self):
        lst = '\n'.join('\t'+str(p) for p in self._members)
        return f"{self.__class__.__name__}(\n{lst}\n)"