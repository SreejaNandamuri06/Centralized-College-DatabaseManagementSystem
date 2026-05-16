USE dbmscollege;

SELECT s.StudentID, s.FirstName, s.LastName, d.DepartmentName
FROM Student s
JOIN Department d ON s.DepartmentID = d.DepartmentID;

SELECT f.FacultyID, CONCAT(f.FirstName, ' ', f.LastName) AS FacultyName, d.DepartmentName
FROM Faculty f
JOIN Department d ON f.DepartmentID = d.DepartmentID;

SELECT c.CourseName, c.CourseCode, d.DepartmentName,
       CONCAT(f.FirstName, ' ', f.LastName) AS FacultyName
FROM Course c
JOIN Department d ON c.DepartmentID = d.DepartmentID
JOIN Faculty f ON c.FacultyID = f.FacultyID;

SELECT e.EnrollmentID, CONCAT(s.FirstName, ' ', s.LastName) AS StudentName, c.CourseName
FROM Enrollment e
JOIN Student s ON e.StudentID = s.StudentID
JOIN Course c ON e.CourseID = c.CourseID;

SELECT d.DepartmentName, COUNT(s.StudentID) AS TotalStudents
FROM Department d
LEFT JOIN Student s ON d.DepartmentID = s.DepartmentID
GROUP BY d.DepartmentID, d.DepartmentName;

SELECT d.DepartmentName, COUNT(f.FacultyID) AS TotalFaculty
FROM Department d
LEFT JOIN Faculty f ON d.DepartmentID = f.DepartmentID
GROUP BY d.DepartmentID, d.DepartmentName;

SELECT c.CourseName, AVG(r.Marks) AS AverageMarks
FROM Result r
JOIN Course c ON r.CourseID = c.CourseID
GROUP BY c.CourseID, c.CourseName;

SELECT c.CourseName, CONCAT(s.FirstName, ' ', s.LastName) AS StudentName, r.Marks
FROM Result r
JOIN Student s ON r.StudentID = s.StudentID
JOIN Course c ON r.CourseID = c.CourseID
WHERE (r.CourseID, r.Marks) IN (
    SELECT CourseID, MAX(Marks)
    FROM Result
    GROUP BY CourseID
);

SELECT CONCAT(s.FirstName, ' ', s.LastName) AS StudentName, COUNT(e.CourseID) AS TotalCourses
FROM Enrollment e
JOIN Student s ON e.StudentID = s.StudentID
GROUP BY s.StudentID, StudentName
HAVING COUNT(e.CourseID) > 1;

SELECT * FROM StudentPerformance;
SELECT * FROM AttendanceSummary;
