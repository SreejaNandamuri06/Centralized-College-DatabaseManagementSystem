CREATE DATABASE IF NOT EXISTS dbmscollege;
USE dbmscollege;

DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Result;
DROP TABLE IF EXISTS Attendance;
DROP TABLE IF EXISTS Enrollment;
DROP TABLE IF EXISTS Course;
DROP TABLE IF EXISTS Student;
DROP TABLE IF EXISTS Faculty;
DROP TABLE IF EXISTS Department;

CREATE TABLE Department (
    DepartmentID INT AUTO_INCREMENT PRIMARY KEY,
    DepartmentName VARCHAR(100) NOT NULL UNIQUE,
    HOD VARCHAR(100)
);

CREATE TABLE Faculty (
    FacultyID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) UNIQUE,
    Phone VARCHAR(15),
    DepartmentID INT,
    Designation VARCHAR(50),
    FOREIGN KEY (DepartmentID) REFERENCES Department(DepartmentID)
);

CREATE TABLE Student (
    StudentID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Email VARCHAR(100) UNIQUE,
    Phone VARCHAR(15),
    DepartmentID INT,
    EnrollmentYear INT,
    FOREIGN KEY (DepartmentID) REFERENCES Department(DepartmentID)
);

CREATE TABLE Course (
    CourseID INT AUTO_INCREMENT PRIMARY KEY,
    CourseName VARCHAR(100) NOT NULL,
    CourseCode VARCHAR(20) NOT NULL UNIQUE,
    Credits INT,
    DepartmentID INT,
    FacultyID INT,
    FOREIGN KEY (DepartmentID) REFERENCES Department(DepartmentID),
    FOREIGN KEY (FacultyID) REFERENCES Faculty(FacultyID)
);

CREATE TABLE Enrollment (
    EnrollmentID INT AUTO_INCREMENT PRIMARY KEY,
    EnrollmentDate DATE,
    StudentID INT,
    CourseID INT,
    UNIQUE KEY uq_student_course (StudentID, CourseID),
    FOREIGN KEY (StudentID) REFERENCES Student(StudentID),
    FOREIGN KEY (CourseID) REFERENCES Course(CourseID)
);

CREATE TABLE Attendance (
    AttendanceID INT AUTO_INCREMENT PRIMARY KEY,
    Date DATE,
    Status VARCHAR(20),
    StudentID INT,
    CourseID INT,
    FOREIGN KEY (StudentID) REFERENCES Student(StudentID),
    FOREIGN KEY (CourseID) REFERENCES Course(CourseID)
);

CREATE TABLE Result (
    ResultID INT AUTO_INCREMENT PRIMARY KEY,
    Marks INT,
    Grade VARCHAR(5),
    Semester INT,
    StudentID INT,
    CourseID INT,
    FOREIGN KEY (StudentID) REFERENCES Student(StudentID),
    FOREIGN KEY (CourseID) REFERENCES Course(CourseID)
);

CREATE TABLE Users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) UNIQUE NOT NULL,
    Password VARCHAR(50) NOT NULL,
    Role VARCHAR(20) NOT NULL,
    LinkedID INT
);

INSERT INTO Department (DepartmentName, HOD) VALUES
('Computer Science', 'Dr. Sharma'),
('Electronics', 'Dr. Kumar'),
('Mechanical', 'Dr. Reddy'),
('Civil', 'Dr. Rao');

INSERT INTO Faculty (FirstName, LastName, Email, Phone, DepartmentID, Designation) VALUES
('Ramesh', 'Kumar', 'ramesh@college.com', '9876543201', 1, 'Professor'),
('Kavitha', 'Rao', 'kavitha@college.com', '9876543202', 1, 'Assistant Professor'),
('Arun', 'Prasad', 'arun@college.com', '9876543203', 2, 'Professor'),
('Meena', 'Reddy', 'meena@college.com', '9876543204', 3, 'Lecturer'),
('Suresh', 'Naidu', 'suresh@college.com', '9876543205', 4, 'Professor');

INSERT INTO Student (FirstName, LastName, Email, Phone, DepartmentID, EnrollmentYear) VALUES
('Sreeja', 'R', 'sreeja@gmail.com', '9876543210', 1, 2023),
('Rahul', 'Sharma', 'rahul@gmail.com', '9876543211', 1, 2023),
('Priya', 'Nair', 'priya@gmail.com', '9876543212', 2, 2022),
('Kiran', 'Rao', 'kiran@gmail.com', '9876543213', 3, 2021),
('Anjali', 'Das', 'anjali@gmail.com', '9876543214', 4, 2022);

INSERT INTO Course (CourseName, CourseCode, Credits, DepartmentID, FacultyID) VALUES
('Database Management System', 'DBMS101', 4, 1, 1),
('Data Structures', 'DS102', 3, 1, 2),
('Digital Electronics', 'DE201', 4, 2, 3),
('Thermodynamics', 'ME301', 3, 3, 4),
('Structural Analysis', 'CE401', 4, 4, 5);

INSERT INTO Enrollment (EnrollmentDate, StudentID, CourseID) VALUES
('2026-01-10', 1, 1),
('2026-01-11', 1, 2),
('2026-01-12', 2, 1),
('2026-01-13', 3, 3),
('2026-01-14', 4, 4),
('2026-01-15', 5, 5);

INSERT INTO Attendance (Date, Status, StudentID, CourseID) VALUES
('2026-02-01', 'Present', 1, 1),
('2026-02-01', 'Absent', 1, 2),
('2026-02-01', 'Present', 2, 1),
('2026-02-02', 'Present', 3, 3),
('2026-02-02', 'Absent', 4, 4),
('2026-02-03', 'Present', 5, 5);

INSERT INTO Result (Marks, Grade, Semester, StudentID, CourseID) VALUES
(88, 'A', 1, 1, 1),
(76, 'B', 1, 1, 2),
(91, 'A+', 1, 2, 1),
(69, 'B', 2, 3, 3),
(72, 'B+', 2, 4, 4),
(85, 'A', 2, 5, 5);

INSERT INTO Users (Username, Password, Role, LinkedID) VALUES
('admin', 'admin123', 'admin', NULL),
('student1', 'student123', 'student', 1),
('student2', 'student123', 'student', 2),
('faculty1', 'faculty123', 'faculty', 1),
('faculty2', 'faculty123', 'faculty', 2),
('faculty3', 'faculty123', 'faculty', 3),
('faculty4', 'faculty123', 'faculty', 4),
('faculty5', 'faculty123', 'faculty', 5);

CREATE OR REPLACE VIEW StudentPerformance AS
SELECT s.StudentID,
       CONCAT(s.FirstName, ' ', s.LastName) AS StudentName,
       c.CourseName,
       r.Marks,
       r.Grade,
       r.Semester
FROM Result r
JOIN Student s ON r.StudentID = s.StudentID
JOIN Course c ON r.CourseID = c.CourseID;

CREATE OR REPLACE VIEW AttendanceSummary AS
SELECT s.StudentID,
       CONCAT(s.FirstName, ' ', s.LastName) AS StudentName,
       c.CourseName,
       ROUND(
           SUM(CASE WHEN a.Status = 'Present' THEN 1 ELSE 0 END) * 100.0 / COUNT(a.AttendanceID),
           2
       ) AS AttendancePercentage
FROM Attendance a
JOIN Student s ON a.StudentID = s.StudentID
JOIN Course c ON a.CourseID = c.CourseID
GROUP BY s.StudentID, c.CourseID;
