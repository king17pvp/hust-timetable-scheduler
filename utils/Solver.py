from abc import ABC, abstractmethod
from typing import List
from .Class import *
from .Utils import *
class Solver(ABC):
    def __init__(self):
        self.constraints = []
    
    def add_constraint(self, constraint):
        self.constraints.append(constraint)


    @abstractmethod
    def solve(self, course_list: list):
        pass 

class BacktrackSolver(Solver):
    def __init__(self, class_list: List[HUSTClass]):
        super().__init__()
        self.class_list = class_list
        self.timetable_space = None
        self.filtered_class_list = None
        self.solutions = None
        self.status = False 
        self.class_code_to_idx = None
    
    def add_constraint(self, constraint):
        return super().add_constraint(constraint)

    def solve(self, course_list: list):
        unique_course_list = list(set(course_list))
        self.filtered_class_list = filter_classes_by_course_code(self.class_list, unique_course_list)
        class_code_to_idx, combinations = generate_combinations(self.filtered_class_list) 
        self.class_code_to_idx = class_code_to_idx 
        optimal_schedules = create_timetable(class_code_to_idx, 
                                             unique_course_list, 
                                             combinations, 
                                             self.filtered_class_list,
                                             self.constraints)
        if len(optimal_schedules) == 0:
            self.status = False 
        else:
            self.status = True
            self.solutions = optimal_schedules