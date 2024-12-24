import pandas as pd
import numpy as np
import json
import re
import time

from .Class import *
from typing import List
from datetime import datetime

def convert_time_to_seconds(time_str) -> int:
    if ":" not in time_str:
        return int(time_str[:2]) * 3600 + int(time_str[2:]) * 60
    else:
        t = time_str.split(":")
        h, m = t[0], t[1]
        return int(h) * 3600 + int(m) * 60
def seconds_to_time(seconds):
    """Convert seconds to HH:MM format."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"

def overlap(t1: str, t2: str):
    
    t1_st, t1_en = t1.split("-")
    t2_st, t2_en = t2.split("-")
    t1_st, t1_en = t1_st.replace(" ", ""), t1_en.replace(" ", "")
    t2_st, t2_en = t2_st.replace(" ", ""), t2_en.replace(" ", "")
    # print(t1_st, t1_en)
    # print(t2_st, t2_en)
    t1_st, t1_en = convert_time_to_seconds(t1_st), convert_time_to_seconds(t1_en)
    t2_st, t2_en = convert_time_to_seconds(t2_st), convert_time_to_seconds(t2_en)
    # print(t1_st, t1_en)
    # print(t2_st, t2_en)
    if (t1_en > t2_st):
        return True
    return False

def parse_week_range(week_range) -> List:
    """
    Parses the 'Tuần' column, extracting the list of weeks a class takes place.
    Handles cases like `March-10` or `a/b/year`.

    Parameters:
        week_range (str or int/float): A value describing the weeks.

    Returns:
        list: A sorted list of unique weeks as integers.
    """
    if pd.isna(week_range):
        return []

    if isinstance(week_range, (datetime, pd.Timestamp)):
        numeric_parts = [week_range.month, week_range.day]  # Extract numeric parts (e.g., 3 and 10)
        start, end = min(numeric_parts), max(numeric_parts)
        return list(range(start, end + 1))

    # If the value is a number, convert it to a single-element list
    if isinstance(week_range, (int, float)):
        return [int(week_range)]

    weeks = set()  # To avoid duplicate weeks

    # Split by commas to handle multiple ranges or single weeks
    parts = str(week_range).split(',')

    for part in parts:
        part = part.strip()
        
        # Match ranges like "a-b" where a and b are integers
        range_match = re.match(r'^(\d+)-(\d+)$', part)
        if range_match:
            start, end = map(int, range_match.groups())
            weeks.update(range(start, end + 1))
            continue
        
        # Handle formats like "March-10", "3/10/2024"
        cleaned_part = re.sub(r'[^\d/-]', '', part)  # Remove non-numeric/non-separator characters
        numeric_parts = re.findall(r'\d+', cleaned_part)
        if len(numeric_parts) >= 2:  # At least two numeric values to form a range
            start, end = map(int, sorted(numeric_parts[:2]))  # Take first two values and sort
            weeks.update(range(start, end + 1))
            continue

        # Handle single weeks like "3"
        if part.isdigit():
            weeks.add(int(part))

    return sorted(weeks)

def get_class_list(df) -> List[HUSTClass]:
    """
    Classifiy classes from excel file to their true class objects
    """
    class_list = []
    class_map_id = {}
    new_id = 0
    df['Tuần'] = df['Tuần'].astype(str)
    for i, tmp in enumerate(df.iterrows()):
        row = tmp[1]
        if pd.isnull(row['Mã_lớp']):
            room = np.nan 
        else:
            room = str(row['Phòng']).strip()
        class_code = str(row['Mã_lớp'])
        weeks = parse_week_range(row['Tuần'])
        if pd.isnull(row['Thời_gian']):
            start, end = np.nan, np.nan
        else: 
            start, end = row['Thời_gian'].split('-')    
            start, end = convert_time_to_seconds(start), convert_time_to_seconds(end)
            # print(start, end)
        if pd.isnull(row['Thứ']):
            day = -1
        else:
            day = int(row['Thứ'])
        appeared = True
        # Check if a class code exists in list
        # If not exist, assign new id to it
        if class_map_id.get(class_code, -1) == -1:
            class_map_id[class_code] = new_id
            appeared = False
            new_id += 1
        # print(len(class_list), class_code, class_map_id[class_code], appeared)
        if (row['Loại_lớp'] in ["LT+BT", "LT"]):
            if row['Cần_TN'] == "TN":
                tmp1 = True
            else:
                tmp1 = False
            if not appeared:
                # set([(day, (start, end))])
                t = HUSTTheoryClass(row['Mã_HP'], class_code, week=row['Tuần'], requires_lab = tmp1)
                for week in weeks:
                    t.times[week].add((day, (start, end, room)))
                class_list.append(t)
            else:
                for week in weeks:
                    class_list[class_map_id[class_code]].times[week].add((day, (start, end, room)))
        elif(row['Loại_lớp'] == "BT"):
            if row['Cần_TN'] == "TN":
                tmp1 = True
            else:
                tmp1 = False
            if not appeared:
                t = HUSTRecitationClass(row['Mã_HP'], class_code, week=row['Tuần'], associated_class=row['Mã_lớp_kèm'], requires_lab = tmp1)
                for week in weeks:
                    t.times[week].add((day, (start, end, room)))
                class_list.append(t)
                # print("added")
            else:
                for week in weeks:
                    class_list[class_map_id[class_code]].times[week].add((day, (start, end, room)))
        elif(row['Loại_lớp'] == "TN"):
            if not appeared:
                t = HUSTLabClass(row['Mã_HP'], class_code, week=row['Tuần'])
                for week in weeks:
                    t.times[week].add((day, (start, end, room)))
                class_list.append(t)
                # print("added")
            else:
                for week in weeks:
                    class_list[class_map_id[class_code]].times[week].add((day, (start, end, room)))
        else:
            # Do an
            if not appeared:
                t = HUSTThesisClass(row['Mã_HP'], class_code, week=row['Tuần'])
                for week in weeks:
                    t.times[week].add((day, (start, end, room)))
                class_list.append(t)
                # print("added")
            else:
                for week in weeks:
                    class_list[class_map_id[class_code]].times[week].add((day, (start, end, room)))
    return class_list

def filter_classes_by_course_code(classes: List[HUSTClass], course_code: str) -> List[HUSTClass]:
    """
    Filter classes by a specific course code.
    """
    return [cls for cls in classes if cls.course_code in course_code]

def generate_combinations(classes: List[HUSTClass]):
    """
    dict: {course_code: {Theory_only: []} or {Theory_recitation_pair: []} and lab class[]}
    """
    iterate_dict = {}
    recitation_dict = {}
    lab_dict = {}
    code_to_idx = {}
    unique_keys = set()
    for i, c in enumerate(classes):
        unique_keys.add(c.course_code)
        code_to_idx[c.class_code] = i
        if c.class_type == 'Recitation':
            recitation_dict[c.course_code] = True 
        if c.class_type == 'Lab':
            lab_dict[c.course_code] = True
    unique_keys = list(unique_keys)
    for code in unique_keys:
        iterate_dict[code] = dict()
        if recitation_dict.get(code, False):
            iterate_dict[code]['Theory_Recitation_Pair'] = []
        if not recitation_dict.get(code, False): 
            iterate_dict[code]['Theory'] = []
        if lab_dict.get(code, False):
            iterate_dict[code]["Lab"] = []
    
    for c in classes:
        if c.class_type == 'Recitation' and recitation_dict.get(c.course_code, False):
            iterate_dict[c.course_code]['Theory_Recitation_Pair'].append((c.class_code, c.associated_class))
        if c.class_type == 'Theory' and not recitation_dict.get(c.course_code, False):
            iterate_dict[c.course_code]['Theory'].append(c.class_code)
        if c.class_type == 'Lab':
            iterate_dict[c.course_code]['Lab'].append(c.class_code)
    class_combinations = {}
    for code in unique_keys:
        tmp = []
        if lab_dict.get(code, False):
            if not recitation_dict.get(code, False):
                for class_code_i in iterate_dict[code]['Theory']:
                    for class_code_j in iterate_dict[code]["Lab"]:
                        if not classes[code_to_idx[class_code_i]].is_overlapping(classes[code_to_idx[class_code_j]]):
                            tmp.append((class_code_i, class_code_j))
            else:
                for class_code_i1, class_code_i2 in iterate_dict[code]['Theory_Recitation_Pair']:
                    for class_code_j in iterate_dict[code]["Lab"]:
                        if classes[code_to_idx[class_code_i1]].is_overlapping(classes[code_to_idx[class_code_j]]):
                            continue
                        if classes[code_to_idx[class_code_i2]].is_overlapping(classes[code_to_idx[class_code_j]]):
                            continue
                        tmp.append((class_code_i1, class_code_i2, class_code_j))
        else:
            if recitation_dict.get(code, False):
                tmp = iterate_dict[code]['Theory_Recitation_Pair']
            else:
                tmp = iterate_dict[code]['Theory']
        class_combinations[code] = tmp
    
    return code_to_idx, class_combinations
def create_timetable(class_code_to_idx, 
                     course_codes, 
                     combinations, 
                     class_list, 
                     constraints):
    """
    Generate timetables based on the constraints.
    Returns:
        list: A list of optimal timetables with minimized idle time.
    """
    def is_valid_schedule(current_schedule, new_class_code):
        """
        Check if a new class can be added to the current schedule without overlap.
        """
        candidate_class_list = [class_list[class_code_to_idx[existing_class_code]] for existing_class_code in current_schedule] + [class_list[class_code_to_idx[new_class_code]]]
        for constraint in constraints[:-1]:
            if not constraint.valid(candidate_class_list):
                return False 

        return True

    def backtrack(course_idx, course_list, current_schedule):
        """
        Backtracking to generate valid timetables.
        """
        # print(current_schedule)
        if course_idx == len(course_list):
            # All courses are scheduled
            candidate_class_list = [class_list[class_code_to_idx[existing_class_code]] for existing_class_code in current_schedule]
            if constraints[-1].valid(candidate_class_list):
                optimal_schedules.append(current_schedule[:])
            return
        
        course_code = course_list[course_idx]
        bool_found = True
        for combination in combinations[course_code]:
            if not isinstance(combination, tuple):
                iter_list = [combination]
            else:
                iter_list = combination
            # Check if the combination is valid
            valid = True
            new_classes = []
            tmp = []
            for classes in iter_list:
                # print(current_schedule, classes)
                if not is_valid_schedule(current_schedule, classes):
                    valid = False
                    break 
                else:
                    tmp.append(classes)
                    
            if valid:
                # Add classes and backtrack
                for _ in tmp:
                    current_schedule.append(_)
                backtrack(course_idx + 1, course_list, current_schedule)
                # Remove classes after backtracking
                for _ in tmp:
                    current_schedule.remove(_)

    # Initialize variables
    min_idle = [float('inf')]
    optimal_schedules = []
    current_schedules = []
    new_course_code = sorted(course_codes, key=lambda x: len(combinations[x]))
    backtrack(0, new_course_code, current_schedules)
    return optimal_schedules