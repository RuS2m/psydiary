class RatingEvent:
    def __init__(self, rate, datetime):
        self.rate = rate
        self.datetime = datetime

class Note:
    def __init__(self, a1, b1, c1, a2, b2, c2):
        self.a1 = a1
        self.b1 = b1
        self.c1 = c1
        self.a2 = a2
        self.b2 = b2
        self.c2 = c2

class NoteExistence:
    def __init__(self, note_date, existence):
        self.note_date = note_date
        self.existence = existence