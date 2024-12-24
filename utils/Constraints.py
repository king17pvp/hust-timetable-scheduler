from abc import ABC, abstractmethod
from .Class import *
from typing import List
class Constraint(ABC):
    @abstractmethod
    def valid(self, classes: List[HUSTClass]):
        pass
class NonClashingConstraint(Constraint):
    def __init__(self, name):
        self.name = name 
    def valid(self, classes: List[HUSTClass]):
        if len(classes) == 1:
            return True
        for i in range(len(classes) - 1):
            for j in range(i + 1, len(classes)):
                if classes[i].is_overlapping(classes[j]):
                    return False 
        return True

class MustHaveClassCodeConstraint(Constraint):
    def __init__(self, name, desired_class_codes: list = []):
        self.name = name
        self.desired_class_codes = desired_class_codes
    def valid(self, classes: List[HUSTClass]):
        tmp_class_codes = [cls.class_code for cls in classes]
        for class_code in self.desired_class_codes:
            if class_code not in tmp_class_codes:
                return False
        return True

class EarliestClassTimeConstraint(Constraint):
    def __init__(self, name, earliest_hour):
        self.name = name
        self.earliest_hour = earliest_hour
    
    def valid(self, classes: List[HUSTClass]):
        for cls in classes:
            for week in list(cls.times.keys()):
                for lesson in cls.times[week]:
                    # print(class_code.course_code, lesson, self.earliest_hour)
                    if lesson[1][0] < self.earliest_hour:
                        return False 
        return True
class LatestClassTimeConstraint(Constraint):
    def __init__(self, name, latest_hour):
        self.name = name
        self.latest_hour = latest_hour
    
    def valid(self, classes: List[HUSTClass]):
        for cls in classes:
            for week in list(cls.times.keys()):
                for lesson in cls.times[week]:
                    # print(class_code.course_code, lesson, self.latest_hour)
                    if lesson[1][0] > self.latest_hour:
                        return False 
        return True           
class FreeMorningSession(Constraint):
    def __init__(self, name, total_free_mornings = 1, day: list = []):
        self.name = name 
        self.day = day
        self.total_free_mornings = total_free_mornings
    def valid(self, classes: List[HUSTClass]):
        free_status = {}
        total_free_day = 0

        # Monday to Saturday
        weeks = set()
        for class_code in classes:
            for week in class_code.times.keys():
                weeks.add(week)
        free_status = {week: dict() for week in weeks}
        #print(len(classes))
        for class_code in classes:
            #print(class_code.course_code)
            for week in list(class_code.times.keys()):
                for lesson in class_code.times[week]:
                    # print(class_code.course_code, week, lesson[1][0])
                    if lesson[1][0] < 43200:
                        free_status[week][lesson[0]] = True
                        if lesson[0] in self.day:
                            return False 
        t = []
        # print(free_status.keys())
        for week in list(free_status.keys()):
            
            tmp = 0
            tmp = 6 - len(list(free_status[week].keys()))
            t.append(tmp)
            #print(week, free_status[week].keys(), tmp)
        # return True
        min_day_off = min(t)
        return min_day_off >= self.total_free_mornings

class DaysOffConstraint(Constraint):
    def __init__(self, name, total_day = 0, day: list = []):
        super()
        self.total_day = total_day
        self.day = day

    def valid(self, classes: List[HUSTClass]):
        free_status = {}
        total_free_day = 0

        # Monday to Saturday
        weeks = set()
        for cls in classes:
            for week in cls.times.keys():
                weeks.add(week)
        free_status = {week: dict() for week in weeks}
        #print(len(classes))
        for cls in classes:
            #print(class_code.course_code)
            for week in list(cls.times.keys()):
                for lesson in cls.times[week]:
                    free_status[week][lesson[0]] = True
                    if lesson[0] in self.day:
                        return False 
        t = []
        # print(free_status.keys())
        for week in list(free_status.keys()):
            
            tmp = 0
            tmp = 6 - len(list(free_status[week].keys()))
            t.append(tmp)
            #print(week, free_status[week].keys(), tmp)
        # return True
        min_day_off = max(t)
        print(t)
        return min_day_off >= self.total_day