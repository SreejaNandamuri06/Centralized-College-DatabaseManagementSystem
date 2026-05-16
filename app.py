
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import fetch_all, fetch_one, execute_query

app = Flask(__name__)
app.secret_key = 'replace_with_a_secure_secret_key'


def login_required(role=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('login'))
            if role and session.get('role') != role:
                flash('You are not authorized to access that page.', 'danger')
                return redirect(url_for('dashboard'))
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user_profile():
    role = session.get('role')
    linked_id = session.get('linked_id')

    if role == 'student' and linked_id:
        return fetch_one(
            """SELECT s.StudentID AS profile_id, s.FirstName, s.LastName, s.Email, s.Phone,
                      s.EnrollmentYear, d.DepartmentName, 'Student' AS role_label
               FROM Student s
               LEFT JOIN Department d ON s.DepartmentID = d.DepartmentID
               WHERE s.StudentID = %s""",
            (linked_id,)
        )
    if role == 'faculty' and linked_id:
        return fetch_one(
            """SELECT f.FacultyID AS profile_id, f.FirstName, f.LastName, f.Email, f.Phone,
                      f.Designation, d.DepartmentName, 'Faculty' AS role_label
               FROM Faculty f
               LEFT JOIN Department d ON f.DepartmentID = d.DepartmentID
               WHERE f.FacultyID = %s""",
            (linked_id,)
        )
    return {'FirstName': session.get('username', 'Admin'), 'LastName': '', 'role_label': 'Admin'}


@app.context_processor
def inject_layout_data():
    profile = get_current_user_profile() if 'user_id' in session else None
    return dict(current_profile=profile)


@app.route('/')
def home():
    return redirect(url_for('dashboard' if 'user_id' in session else 'login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        user = fetch_one(
            'SELECT UserID, Username, Role, LinkedID FROM Users WHERE Username=%s AND Password=%s',
            (username, password)
        )

        if user:
            session['user_id'] = user['UserID']
            session['username'] = user['Username']
            session['role'] = user['Role']
            session['linked_id'] = user['LinkedID']
            flash(f"Welcome back, {user['Username']}!", 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required()
def dashboard():
    role = session.get('role')

    if role == 'admin':
        stats = {
            'students': fetch_one('SELECT COUNT(*) AS total FROM Student')['total'],
            'faculty': fetch_one('SELECT COUNT(*) AS total FROM Faculty')['total'],
            'departments': fetch_one('SELECT COUNT(*) AS total FROM Department')['total'],
            'courses': fetch_one('SELECT COUNT(*) AS total FROM Course')['total'],
            'enrollments': fetch_one('SELECT COUNT(*) AS total FROM Enrollment')['total'],
        }
        departments = fetch_all(
            """SELECT d.DepartmentName,
                      COUNT(DISTINCT s.StudentID) AS student_count,
                      COUNT(DISTINCT f.FacultyID) AS faculty_count
               FROM Department d
               LEFT JOIN Student s ON d.DepartmentID = s.DepartmentID
               LEFT JOIN Faculty f ON d.DepartmentID = f.DepartmentID
               GROUP BY d.DepartmentID, d.DepartmentName
               ORDER BY d.DepartmentName"""
        )
        recent_students = fetch_all(
            """SELECT s.StudentID, CONCAT(s.FirstName, ' ', s.LastName) AS StudentName,
                      d.DepartmentName, s.EnrollmentYear
               FROM Student s
               LEFT JOIN Department d ON s.DepartmentID = d.DepartmentID
               ORDER BY s.StudentID DESC LIMIT 5"""
        )
        return render_template('dashboard_admin.html', stats=stats, departments=departments, recent_students=recent_students)

    if role == 'faculty':
        faculty_id = session.get('linked_id')
        faculty = fetch_one(
            """SELECT f.*, d.DepartmentName
               FROM Faculty f
               LEFT JOIN Department d ON f.DepartmentID = d.DepartmentID
               WHERE f.FacultyID=%s""",
            (faculty_id,)
        )
        courses = fetch_all(
            """SELECT c.CourseID, c.CourseName, c.CourseCode, c.Credits,
                      (SELECT COUNT(*) FROM Enrollment e WHERE e.CourseID = c.CourseID) AS student_count
               FROM Course c
               WHERE c.FacultyID=%s
               ORDER BY c.CourseName""",
            (faculty_id,)
        )
        summary = {
            'course_count': len(courses),
            'student_total': sum(int(item['student_count']) for item in courses),
        }
        return render_template('dashboard_faculty.html', faculty=faculty, courses=courses, summary=summary)

    if role == 'student':
        student_id = session.get('linked_id')
        student = fetch_one(
            """SELECT s.*, d.DepartmentName
               FROM Student s
               LEFT JOIN Department d ON s.DepartmentID = d.DepartmentID
               WHERE s.StudentID=%s""",
            (student_id,)
        )
        results = fetch_all(
            """SELECT c.CourseName, c.CourseCode, r.Marks, r.Grade, r.Semester
               FROM Result r
               JOIN Course c ON r.CourseID = c.CourseID
               WHERE r.StudentID=%s
               ORDER BY r.Semester, c.CourseName""",
            (student_id,)
        )
        attendance = fetch_all(
            """SELECT c.CourseName,
                      ROUND(SUM(CASE WHEN a.Status='Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS attendance_percentage
               FROM Attendance a
               JOIN Course c ON a.CourseID = c.CourseID
               WHERE a.StudentID=%s
               GROUP BY c.CourseName""",
            (student_id,)
        )
        course_count = fetch_one('SELECT COUNT(*) AS total FROM Enrollment WHERE StudentID=%s', (student_id,))['total']
        average_marks = fetch_one('SELECT ROUND(AVG(Marks), 2) AS avg_marks FROM Result WHERE StudentID=%s', (student_id,))
        return render_template(
            'dashboard_student.html',
            student=student,
            results=results,
            attendance=attendance,
            course_count=course_count,
            average_marks=average_marks['avg_marks'] or 0,
        )

    flash('Unknown role.', 'danger')
    return redirect(url_for('logout'))


@app.route('/students')
@login_required('admin')
def students():
    student_rows = fetch_all(
        """SELECT s.StudentID, s.FirstName, s.LastName, s.Email, s.Phone,
                  s.EnrollmentYear, d.DepartmentName
           FROM Student s
           LEFT JOIN Department d ON s.DepartmentID = d.DepartmentID
           ORDER BY s.StudentID"""
    )
    return render_template('students.html', students=student_rows)


@app.route('/students/add', methods=['GET', 'POST'])
@login_required('admin')
def add_student():
    departments = fetch_all('SELECT DepartmentID, DepartmentName FROM Department ORDER BY DepartmentName')

    if request.method == 'POST':
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        enrollment_year = request.form['enrollment_year'].strip()
        department_id = request.form['department_id']
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        existing_user = fetch_one('SELECT UserID FROM Users WHERE Username=%s', (username,))
        if existing_user:
            flash('Username already exists. Please choose another username.', 'danger')
            return render_template('add_student.html', departments=departments)

        student_id = execute_query(
            """INSERT INTO Student (FirstName, LastName, Email, Phone, DepartmentID, EnrollmentYear)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (first_name, last_name, email, phone, department_id, enrollment_year)
        )

        execute_query(
            """INSERT INTO Users (Username, Password, Role, LinkedID)
               VALUES (%s, %s, 'student', %s)""",
            (username, password, student_id)
        )

        flash('Student added successfully.', 'success')
        return redirect(url_for('students'))

    return render_template('add_student.html', departments=departments)


@app.route('/faculty')
@login_required()
def faculty():
    faculty_rows = fetch_all(
        """SELECT f.FacultyID, f.FirstName, f.LastName, f.Email, f.Phone,
                  f.Designation, d.DepartmentName
           FROM Faculty f
           LEFT JOIN Department d ON f.DepartmentID = d.DepartmentID
           ORDER BY f.FacultyID"""
    )
    return render_template('faculty.html', faculty_members=faculty_rows)


@app.route('/faculty/add', methods=['GET', 'POST'])
@login_required('admin')
def add_faculty():
    departments = fetch_all('SELECT DepartmentID, DepartmentName FROM Department ORDER BY DepartmentName')

    if request.method == 'POST':
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        designation = request.form['designation'].strip()
        department_id = request.form['department_id']
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        existing_user = fetch_one('SELECT UserID FROM Users WHERE Username=%s', (username,))
        if existing_user:
            flash('Username already exists. Please choose another username.', 'danger')
            return render_template('add_faculty.html', departments=departments)

        faculty_id = execute_query(
            """INSERT INTO Faculty (FirstName, LastName, Email, Phone, DepartmentID, Designation)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (first_name, last_name, email, phone, department_id, designation)
        )

        execute_query(
            """INSERT INTO Users (Username, Password, Role, LinkedID)
               VALUES (%s, %s, 'faculty', %s)""",
            (username, password, faculty_id)
        )

        flash('Faculty member added successfully.', 'success')
        return redirect(url_for('faculty'))

    return render_template('add_faculty.html', departments=departments)


@app.route('/courses')
@login_required()
def courses():
    role = session.get('role')
    linked_id = session.get('linked_id')

    if role == 'faculty':
        course_rows = fetch_all(
            """SELECT c.CourseID, c.CourseName, c.CourseCode, c.Credits,
                      d.DepartmentName, CONCAT(f.FirstName, ' ', f.LastName) AS FacultyName
               FROM Course c
               LEFT JOIN Department d ON c.DepartmentID = d.DepartmentID
               LEFT JOIN Faculty f ON c.FacultyID = f.FacultyID
               WHERE c.FacultyID=%s
               ORDER BY c.CourseID""",
            (linked_id,)
        )
    elif role == 'student':
        course_rows = fetch_all(
            """SELECT c.CourseID, c.CourseName, c.CourseCode, c.Credits,
                      d.DepartmentName, CONCAT(f.FirstName, ' ', f.LastName) AS FacultyName
               FROM Enrollment e
               JOIN Course c ON e.CourseID = c.CourseID
               LEFT JOIN Department d ON c.DepartmentID = d.DepartmentID
               LEFT JOIN Faculty f ON c.FacultyID = f.FacultyID
               WHERE e.StudentID=%s
               ORDER BY c.CourseID""",
            (linked_id,)
        )
    else:
        course_rows = fetch_all(
            """SELECT c.CourseID, c.CourseName, c.CourseCode, c.Credits,
                      d.DepartmentName, CONCAT(f.FirstName, ' ', f.LastName) AS FacultyName
               FROM Course c
               LEFT JOIN Department d ON c.DepartmentID = d.DepartmentID
               LEFT JOIN Faculty f ON c.FacultyID = f.FacultyID
               ORDER BY c.CourseID"""
        )

    return render_template('courses.html', courses=course_rows)


@app.route('/attendance')
@login_required()
def attendance():
    role = session.get('role')
    linked_id = session.get('linked_id')

    if role == 'student':
        attendance_rows = fetch_all(
            """SELECT a.Date, a.Status, c.CourseName, c.CourseCode
               FROM Attendance a
               JOIN Course c ON a.CourseID = c.CourseID
               WHERE a.StudentID=%s
               ORDER BY a.Date DESC""",
            (linked_id,)
        )
    elif role == 'faculty':
        attendance_rows = fetch_all(
            """SELECT a.Date, a.Status,
                      CONCAT(s.FirstName, ' ', s.LastName) AS StudentName,
                      c.CourseName, c.CourseCode
               FROM Attendance a
               JOIN Student s ON a.StudentID = s.StudentID
               JOIN Course c ON a.CourseID = c.CourseID
               WHERE c.FacultyID=%s
               ORDER BY a.Date DESC""",
            (linked_id,)
        )
    else:
        attendance_rows = fetch_all(
            """SELECT a.Date, a.Status,
                      CONCAT(s.FirstName, ' ', s.LastName) AS StudentName,
                      c.CourseName, c.CourseCode
               FROM Attendance a
               JOIN Student s ON a.StudentID = s.StudentID
               JOIN Course c ON a.CourseID = c.CourseID
               ORDER BY a.Date DESC"""
        )

    return render_template('attendance.html', attendance_rows=attendance_rows, role=role)


@app.route('/results')
@login_required()
def results():
    role = session.get('role')
    linked_id = session.get('linked_id')

    if role == 'student':
        result_rows = fetch_all(
            """SELECT c.CourseName, c.CourseCode, r.Marks, r.Grade, r.Semester
               FROM Result r
               JOIN Course c ON r.CourseID = c.CourseID
               WHERE r.StudentID=%s
               ORDER BY r.Semester DESC, c.CourseName""",
            (linked_id,)
        )
    elif role == 'faculty':
        result_rows = fetch_all(
            """SELECT CONCAT(s.FirstName, ' ', s.LastName) AS StudentName,
                      c.CourseName, c.CourseCode, r.Marks, r.Grade, r.Semester
               FROM Result r
               JOIN Student s ON r.StudentID = s.StudentID
               JOIN Course c ON r.CourseID = c.CourseID
               WHERE c.FacultyID=%s
               ORDER BY r.Semester DESC, c.CourseName""",
            (linked_id,)
        )
    else:
        result_rows = fetch_all(
            """SELECT CONCAT(s.FirstName, ' ', s.LastName) AS StudentName,
                      c.CourseName, c.CourseCode, r.Marks, r.Grade, r.Semester
               FROM Result r
               JOIN Student s ON r.StudentID = s.StudentID
               JOIN Course c ON r.CourseID = c.CourseID
               ORDER BY r.Semester DESC, c.CourseName"""
        )

    return render_template('results.html', result_rows=result_rows, role=role)


@app.route('/profile')
@login_required()
def profile():
    role = session.get('role')
    linked_id = session.get('linked_id')

    if role == 'student':
        profile_data = fetch_one(
            """SELECT s.StudentID AS EntityID, s.FirstName, s.LastName, s.Email, s.Phone,
                      s.EnrollmentYear, d.DepartmentName
               FROM Student s
               LEFT JOIN Department d ON s.DepartmentID = d.DepartmentID
               WHERE s.StudentID=%s""",
            (linked_id,)
        )
    elif role == 'faculty':
        profile_data = fetch_one(
            """SELECT f.FacultyID AS EntityID, f.FirstName, f.LastName, f.Email, f.Phone,
                      f.Designation, d.DepartmentName
               FROM Faculty f
               LEFT JOIN Department d ON f.DepartmentID = d.DepartmentID
               WHERE f.FacultyID=%s""",
            (linked_id,)
        )
    else:
        profile_data = {'EntityID': session.get('user_id'), 'FirstName': session.get('username'), 'LastName': '', 'Email': 'admin@college.com'}

    return render_template('profile.html', profile=profile_data, role=role)


if __name__ == '__main__':
    app.run(debug=True)
