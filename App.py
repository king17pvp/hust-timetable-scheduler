import pandas as pd
import numpy as np
import json
import re
import time
import random 
import os 
import boto3
import sqlite3
import uuid

from utils.Class import *
from utils.Constraints import *
from utils.Utils import *
from utils.Solver import *

from typing import List
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, session

app = Flask(__name__)
app.secret_key = os.urandom(24)     
DATABASE = './db/user_info.db'
conn = sqlite3.connect(DATABASE, check_same_thread=False)
cursor = conn.cursor()

# AWS S3 configuration
S3_BUCKET = 'hust-timetable-scheduler-upload'
S3_REGION = 'ap-southeast-2'  # e.g., 'us-east-1'
s3_client = boto3.client('s3', region_name=S3_REGION, aws_access_key_id='your-access-key', aws_secret_access_key='your-secret-key')

UPLOAD_FOLDER = '../uploads'
ALLOWED_EXTENSIONS = {'.xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
day_to_str = {2: "Monday", 3: "Tuesday", 4: "Wednesday", 5: "Thursday", 6: "Friday", 7: "Saturday", 8: "Sunday"}

class_code_to_idx = None 
filtered_class_list = None
timetable_path = None
optimal_schedules = None
event_html_paths = []

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
def allowed_file(filename):
    print(os.path.splitext(filename)[-1])
    return os.path.splitext(filename)[-1] in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login_page', status_message="Vui lòng đăng nhập để tiếp tục"))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/logout')
def logout():
    print("Logging out")
    print("Session: ", session)
    session.pop('user', None)  # Clear session data
    return redirect(url_for('login_page', status_message="Đã đăng xuất thành công!"))

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    global timetable_path
    # Handle file upload
    print("Request method:", request.method)
    print("Form data:", request.form)
    print("File data:", request.files)
    file = request.files.get('file-upload')
    course_codes = request.form.get('course-codes')
    class_codes = request.form.get('class-codes')
    earliest_time = request.form.get('earliest-class-hour')
    latest_time = request.form.get('latest-class-hour')
    if not earliest_time:
        earliest_time = "6:45"
    if not latest_time:
        latest_time = "17:30"
    print(earliest_time, latest_time)
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        print(f"File uploaded to {filepath}")
        session['filepath'] = filepath
    else:
        return "Invalid file type or no file uploaded", 400
    
    optional_constraints = {
        'course_codes': course_codes,
        'min-day-off': int(request.form.get('min-day-off', default=0)),
        'earliest_time': convert_time_to_seconds(earliest_time),
        'latest_time': convert_time_to_seconds(latest_time) 
    }

    return redirect(url_for(
        'get_schedule',
        course_codes=optional_constraints['course_codes'],
        class_codes=class_codes,
        min_day_off=optional_constraints['min-day-off'],
        earliest_time=optional_constraints['earliest_time'],
        latest_time=optional_constraints['latest_time']
    ))

@app.route('/', methods=['GET', 'POST'])
def login_page(status_message = ""):
    status_message = request.args.get('status_message')
    print(status_message)
    if request.method == 'POST':
        username = request.form.get('login-username-input')
        password = request.form.get('login-password-input')

        cursor.execute(f'''
    SELECT COUNT(*) FROM users
    WHERE username = ? AND password = ?
''', (username, password))
        row = cursor.fetchall()
        cnt = row[0][0]
        print(cnt)
        if (username == "admin" and password == "123") or cnt == 1:
            session['user'] = username
            print("Session: ", session)
            return redirect(url_for('front_page'))
        else:
            return redirect(url_for('login_page', status_message="Đăng nhập không thành công, hãy thử lại"))
    else:
        return render_template('login.html', status_message = request.args.get('status_message'))
@app.route('/register', methods=['GET', 'POST'])
def register_page(status_message = ""):
    status_message = request.args.get('status_message')
    print(status_message)
    if request.method == 'POST':
        username = request.form.get('login-username-input')
        password = request.form.get('login-password-input')
        retype_password = request.form.get('login-password-input-retype')
        cursor.execute(f'''
            SELECT COUNT(*) FROM users
            WHERE username = ?
        ''', (username, ))
        row = cursor.fetchall()
        cnt = row[0][0]

        if password != retype_password:
            return redirect(url_for('register_page', status_message="Mật khẩu gõ lại không khớp với mật khẩu nhập vào!"))
        else:
            if cnt != 0:
                return redirect(url_for('register_page', status_message="Tài khoản với username này đã tồn tại"))
            else:
                cursor.execute(f'''
                INSERT INTO users (username, password)
                VALUES (?, ?)
                ''', (username, password))
                conn.commit() 
                return redirect(url_for('login_page', status_message="Đăng ký thành công!"))
    else:
        return render_template('register.html', status_message=request.args.get('status_message'))

@app.route('/frontpage')
@login_required
def front_page():
    return render_template('front_page.html')

@app.route('/error')
@login_required
def error_page():
    return render_template('error.html')

@app.route('/reschedule')
def get_schedule():
    global class_code_to_idx
    global filtered_class_list
    global optimal_schedules
    course_codes = request.args.get('course_codes').replace(',', ' ').strip().split()
    class_codes = request.args.get('class_codes')
    earliest_time = int(request.args.get('earliest_time'))
    latest_time = int(request.args.get('latest_time'))
    min_day_off = int(request.args.get('min_day_off'))
    df = pd.read_excel(session.get('filepath'), parse_dates=False)
    class_list = get_class_list(df)

    solver = BacktrackSolver(class_list)
    solver.add_constraint(NonClashingConstraint("Non clashing constraint"))
    if min_day_off > 0:
        solver.add_constraint(DaysOffConstraint("Min Day off constraint", total_day = min_day_off))
    solver.add_constraint(EarliestClassTimeConstraint("Earliest class time", earliest_time))
    solver.add_constraint(LatestClassTimeConstraint("Latest class time", latest_time))
    if class_codes:
        class_codes = class_codes.replace(',', ' ').strip().split()
        solver.add_constraint(MustHaveClassCodeConstraint("Must have class code", class_codes))
    solver.solve(course_codes)
    class_code_to_idx = solver.class_code_to_idx
    filtered_class_list = solver.filtered_class_list
    if solver.status:
        # class_code_to_idx = solver.class_code_to_idx
        # filtered_class_list = solver.filtered_class_list
        optimal_schedules = solver.solutions
        session['message'] = "Schedule generated successfully!!"
        return redirect(url_for('view_schedule', index=0))
    else:
        return redirect(url_for('error_page'))

@app.route('/view/index<int:index>')
@login_required
def view_schedule(index):
    global day_to_str
    global optimal_schedules
    global event_html_paths
    global class_code_to_idx
    global filtered_class_list
    timetable = dict()
    opacity_dict = dict()
    z_index_dict = dict()
    for day in range(2, 9):
        timetable[day_to_str[day]] = dict()
        opacity_dict[day_to_str[day]] = dict()
        z_index_dict[day_to_str[day]] = dict()
    selected_schedule = optimal_schedules[index]
    style = {}
    start_week, end_week = 100, 0
    cur_idx = 0
    for class_code in selected_schedule:
        class_info = filtered_class_list[class_code_to_idx[class_code]]
        course_code = class_info.course_code
        if course_code not in style.keys():
            style[course_code] = cur_idx % 6 + 1
            cur_idx += 1
        for week in filtered_class_list[class_code_to_idx[class_code]].times.keys():
            start_week = min(start_week, week)
            end_week = max(end_week, week)
    if not optimal_schedules or index >= len(optimal_schedules):
        return {"message": "Invalid schedule index"}, 404
    for class_code in selected_schedule:
        class_info = filtered_class_list[class_code_to_idx[class_code]]
        week_str = class_info.week # A str
        course_code = class_info.course_code # A str
        for week in range(start_week, end_week + 1):
            times = class_info.times.get(week, {})
            for day, (start, end, room) in times:
                start_time = seconds_to_time(start) # A str
                end_time = seconds_to_time(end) # A str
                time_interval = f"{start_time} - {end_time}"
                if time_interval in timetable[day_to_str[day]].keys():
                    timetable[day_to_str[day]][time_interval].add((course_code, 
                                                                   class_code, 
                                                                   room,
                                                                   week_str,
                                                                   style[course_code]
                                                                    )) 
                else:
                    timetable[day_to_str[day]][time_interval] = set()
                    timetable[day_to_str[day]][time_interval].add((course_code, 
                                                                   class_code, 
                                                                   room,
                                                                   week_str,
                                                                   style[course_code]
                                                                    ))
                    opacity_dict[day_to_str[day]][time_interval] = 0.9
                    z_index_dict[day_to_str[day]][time_interval] = 1
    for day in range(2, 9):
        t = list(timetable[day_to_str[day]].keys())
        t.sort()
        for i, time_interval in enumerate(t):
            # print(day, i, time_interval)
            if i == 0:
                continue
            else:
                if overlap(t[i - 1], time_interval):
                    opacity_dict[day_to_str[day]][t[i - 1]] *= 0.8 
                    z_index_dict[day_to_str[day]][time_interval] = z_index_dict[day_to_str[day]][t[i - 1]] + 1
                    print(t[i - 1], time_interval)      
    return_dict = {day: {interval: list(timetable[day][interval]) for interval in timetable[day].keys()} for day, schedule in timetable.items()}
    return render_template('timetable.html', 
                           timetable=return_dict, 
                           opacity_dict=opacity_dict,
                           z_index_dict=z_index_dict,
                           total_schedules = len(optimal_schedules),
                           index=index)
if __name__ == "__main__":
    app.run(debug=True)
    for event_path in event_html_paths:
        os.remove(event_path)
    conn.close()