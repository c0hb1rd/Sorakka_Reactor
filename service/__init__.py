class SorakaService:
    def __init__(self, name):
        self.rules = []
        self.name = name

    def insert_routines(self, rules):
        for item in rules:
            self.insert_routine(item[0], item[1])

    def insert_routine(self, routine, note=''):
        routine_name = routine.__name__[0].lower() + routine.__name__[1:]

        self.rules.append({
            'service': self.name,
            'routine': routine_name,
            'func': routine.get_func(routine_name),
            'note': note,
        })


