
class Rack:
    """ A data structure for when you just want to put something in it,
        and get an index back that you can use to retrieve it later
    """
    def __init__(self, iterable=None):
        self._d = {}
        self._index = 0
        if iterable is not None:
            self.extend(iterable)

    def push(self, item):
        self._d[self._index] = item
        self._index += 1
        return self._index - 1

    def get(self, index, default=None):
        return self._d.get(index, default)

    def pop(self, index):
        return self._d.pop(index)

    def items(self):
        return self._d.items()
    
    def keys(self):
        return self._d.keys()

    def extend(self, iterable):
        """ Returns a tuple with indices of the inserted items.
            Probably not very useful.
        """
        return tuple(self.push(item) for item in iterable)
    
    def key(self, target):
        for idx, item in self._d.items():
            if target == item:
                return idx
        raise ValueError(f"{target} is not in the rack")

    def __delitem__(self, index):
        del self._d[index]

    def __getitem__(self, index):
        return self._d[index]

    def __contains__(self, item):
        return item in self._d.values()

    def __len__(self):
        return len(self._d)

    def __iter__(self):
        return iter(self._d.values())
    
    def __bool__(self):
        return bool(self._d)
    
    def __str__(self):
        return f"<{self.__class__.__name__}: {', '.join(str(item) for item in self._d.values())}>"
    
    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self._d)})"
