from collections import defaultdict

class HUSTClass:
    def __init__(self, 
                 course_code: str, 
                 class_code: str, 
                 week: str):
        """
        Times should considered as a dictionary of weeks:
            where times[week] = set of (day, (start, end, room))
        """
        self.times = defaultdict(set) # times must be in terms of ((day, (start, end, room), weeks:))
        self.course_code = course_code
        self.class_code = class_code
        self.week = week
        self.class_type = None
    def __str__(self):
        tmp: str = ""
        for i, (key, value) in enumerate(self.times.items()):
            tmp += f"Week {key}:\n"
            for j, lesson in enumerate(value):
                tmp += f"Lesson {j + 1}: {lesson[0]} - From {lesson[1][0]} to {lesson[1][1]}\n"
            if i != len(self.times.keys()) - 1:
                tmp += "\n"
        return f"Class: {self.class_code}, course: {self.course_code} \n{tmp}"

    def is_overlapping(self, other):
        """
        Check if this class overlaps with another class based on their times.
        Returns:
            bool: True if there is an overlap, False otherwise.
        """
        first_check = set(self.times.keys()) & set(other.times.keys())
        if len(first_check) == 0:
            return False
        for week, lessons in self.times.items():
            if week in other.times.keys():  # Only compare if both classes have lessons in the same week
                for day, (start, end, room) in lessons:
                    for other_day, (other_start, other_end, other_room) in other.times[week]:
                        if day == other_day:  # Same day
                            if not (end <= other_start or start >= other_end):
                                return True
        return False

class HUSTThesisClass(HUSTClass):
    def __init__(self, 
                 course_code: str, 
                 class_code: str, 
                 week: str):
        super().__init__(course_code, class_code, week)
        self.class_type = "Thesis"
    def __str__(self):
        tmp: str = ""
        for i, (key, value) in enumerate(self.times.items()):
            tmp += f"Week {key}:\n"
            for j, lesson in enumerate(value):
                tmp += f"Lesson {j + 1}: {lesson[0]} - From {lesson[1][0]} to {lesson[1][1]}\n"
            if i != len(self.times.keys()) - 1:
                tmp += "\n"
        return f"Class: {self.class_code}, course: {self.course_code}, class type: {self.class_type} \n{tmp}"

class HUSTTheoryClass(HUSTClass):
    def __init__(self, 
                 course_code: str, 
                 class_code: str, 
                 week: str, 
                 requires_lab = False):
        super().__init__(course_code, class_code, week)
        self.requires_lab = requires_lab
        self.class_type = 'Theory'

    def __str__(self):
        tmp: str = ""
        for i, (key, value) in enumerate(self.times.items()):
            tmp += f"Week {key}:\n"
            for j, lesson in enumerate(value):
                tmp += f"Lesson {j + 1}: {lesson[0]} - From {lesson[1][0]} to {lesson[1][1]}\n"
            if i != len(self.times.keys()) - 1:
                tmp += "\n"
        return f"Class: {self.class_code}, course: {self.course_code}, class type: {self.class_type} \n{tmp}"

class HUSTRecitationClass(HUSTClass):
    def __init__(self, 
                 course_code: str, 
                 class_code: str, 
                 week: str, 
                 associated_class: str, 
                 requires_lab = False):
        super().__init__(course_code, class_code, week)
        self.associated_class = str(int(associated_class))
        self.requires_lab = requires_lab
        self.class_type = 'Recitation'
    def __str__(self):
        tmp: str = ""
        for i, (key, value) in enumerate(self.times.items()):
            tmp += f"Week {key}:\n"
            for j, lesson in enumerate(value):
                tmp += f"Lesson {j + 1}: {lesson[0]} - From {lesson[1][0]} to {lesson[1][1]}\n"
            if i != len(self.times.keys()) - 1:
                tmp += "\n"
        return f"Class: {self.class_code}, course: {self.course_code}, Class type: {self.class_type}, Associatied Theory class code: {self.associated_class}\n{tmp}"

class HUSTLabClass(HUSTClass):
    def __init__(self, 
                 course_code: str, 
                 class_code: str, 
                 week: str
                 ):
        super().__init__(course_code, class_code, week)
        self.class_type = 'Lab'

    def __str__(self):
        tmp: str = ""
        for i, (key, value) in enumerate(self.times.items()):
            tmp += f"Week {key}:\n"
            for j, lesson in enumerate(value):
                tmp += f"Lesson {j + 1}: {lesson[0]} - From {lesson[1][0]} to {lesson[1][1]}\n"
            if i != len(self.times.keys()) - 1:
                tmp += "\n"
        return f"Class: {self.class_code}, course: {self.course_code}, class type: {self.class_type} \n{tmp}"

if __name__ == "__main__":
    tmp = HUSTRecitationClass("9:20", "11:45", [1, 2, 3, 4, 5, 6], "IT3080E", "123456", None, True)