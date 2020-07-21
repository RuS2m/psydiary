class RatingEvent:
    def __init__(self, rate, datetime):
        self.rate = rate
        self.datetime = datetime

class Note:
    def __init__(self, note_id, a, b, c, b1, c1, is_reflected):
        self.note_id = note_id
        self.a = str(a).strip()
        self.b = str(b).strip()
        self.c = str(c).strip()
        self.b1 = str(b1).strip()
        self.c1 = str(c1).strip()
        self.is_reflected = is_reflected
    def __str__(self):
        not_reflected_part = 'A (Activitating event)\n' \
               '<pre>{}</pre>\n\n' \
               'B (Beliefs)\n' \
               '<pre>{}</pre>\n\n' \
               'C (Consequences)\n' \
               '<pre>{}</pre>'.format(self.a, self.b, self.c)
        reflected_part = 'B1 (Reflected beliefs)\n' \
               '<pre>{}</pre>\n\n' \
               'C1 (Reflected consequences)\n' \
               '<pre>{}</pre>'.format( self.b1, self.c1)
        if self.is_reflected:
            return "%s\n\n%s" % (not_reflected_part, reflected_part)
        else:
            return not_reflected_part

class NoteExistence:
    def __init__(self, note_date, existence):
        self.note_date = note_date
        self.existence = existence
    def __str__(self):
        return 'NoteExistence(note_date: {}, existence: {})\n'\
            .format(self.note_date, self.existence)