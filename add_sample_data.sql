-- ============================================================
-- Placement Management System — Extra sample data
-- Run AFTER the schema, original sample data, triggers and procedures:
--     mysql -u root -p placement_system < add_sample_data.sql
-- Adds 20 students, creates applications only for eligible
-- student/drive pairs, and spreads the application statuses.
-- (Setting a status to 'Selected' fires trg_application_selected,
--  which creates the placement records automatically.)
-- ============================================================

USE placement_system;

INSERT INTO student (name, branch, cgpa, backlogs, skills, internships, email, phone, password_hash) VALUES
('Kavya Shetty', 'CSE', 9.1, 0, 'Python, Java, SQL', 'Intern at Infosys', 'kavya.shetty@college.edu', '9800000001', 'x'),
('Rohan Gowda', 'CSE', 8.4, 0, 'Java, React', 'Intern at Wipro', 'rohan.gowda@college.edu', '9800000002', 'x'),
('Meera Nambiar', 'CSE', 7.8, 1, 'C++, SQL', NULL, 'meera.nambiar@college.edu', '9800000003', 'x'),
('Aditya Kulkarni', 'CSE', 8.9, 0, 'Python, ML, SQL', 'Intern at Bosch', 'aditya.kulkarni@college.edu', '9800000004', 'x'),
('Pooja Hegde', 'CSE', 6.9, 2, 'HTML, CSS', NULL, 'pooja.hegde@college.edu', '9800000005', 'x'),
('Suresh Babu', 'IT', 8.1, 0, 'Java, Spring', 'Intern at TCS', 'suresh.babu@college.edu', '9800000006', 'x'),
('Nisha Patil', 'IT', 8.8, 0, 'Python, Django, SQL', 'Intern at Accenture', 'nisha.patil@college.edu', '9800000007', 'x'),
('Karthik Reddy', 'IT', 7.5, 1, 'JavaScript, Node', NULL, 'karthik.reddy@college.edu', '9800000008', 'x'),
('Lakshmi Prasad', 'IT', 9.0, 0, 'Java, AWS, SQL', 'Intern at Amazon', 'lakshmi.prasad@college.edu', '9800000009', 'x'),
('Varun Joshi', 'IT', 7.2, 0, 'C, Python', NULL, 'varun.joshi@college.edu', '9800000010', 'x'),
('Deepa Menon', 'ECE', 8.3, 0, 'Embedded C, MATLAB', 'Intern at Texas Instruments', 'deepa.menon@college.edu', '9800000011', 'x'),
('Harsha Vardhan', 'ECE', 7.9, 0, 'VLSI, Python', NULL, 'harsha.vardhan@college.edu', '9800000012', 'x'),
('Anjali Desai', 'ECE', 8.6, 0, 'IoT, Python', 'Intern at Samsung', 'anjali.desai@college.edu', '9800000013', 'x'),
('Manoj Kumar', 'ECE', 6.8, 1, 'Arduino, C', NULL, 'manoj.kumar@college.edu', '9800000014', 'x'),
('Shreya Bhat', 'ECE', 9.2, 0, 'Signal Processing, Python', 'Intern at ISRO', 'shreya.bhat@college.edu', '9800000015', 'x'),
('Vikram Singh', 'Mechanical', 7.7, 0, 'AutoCAD, SolidWorks', 'Intern at Tata Motors', 'vikram.singh@college.edu', '9800000016', 'x'),
('Tanvi Rao', 'Mechanical', 8.2, 0, 'CATIA, Python', NULL, 'tanvi.rao@college.edu', '9800000017', 'x'),
('Girish Naik', 'Civil', 7.4, 0, 'AutoCAD, STAAD Pro', 'Intern at L and T', 'girish.naik@college.edu', '9800000018', 'x'),
('Sahana Murthy', 'Civil', 8.0, 0, 'Revit, Surveying', NULL, 'sahana.murthy@college.edu', '9800000019', 'x'),
('Yash Agarwal', 'CSE', 8.7, 0, 'Python, ML, Docker', 'Intern at Flipkart', 'yash.agarwal@college.edu', '9800000020', 'x');

INSERT INTO application (student_id, drive_id, status, applied_date)
SELECT s.student_id, d.drive_id, 'Applied',
       DATE_SUB(CURDATE(), INTERVAL ((s.student_id + d.drive_id) MOD 20) DAY)
FROM student s
JOIN drive d
JOIN company c ON c.company_id = d.company_id
WHERE s.student_id > 5
  AND s.cgpa >= IFNULL(c.min_cgpa_required, 0)
  AND (c.eligible_branches IS NULL OR c.eligible_branches = ''
       OR FIND_IN_SET(s.branch, REPLACE(c.eligible_branches, ' ', '')) > 0)
  AND (s.student_id + d.drive_id) MOD 3 <> 0
  AND NOT EXISTS (SELECT 1 FROM application a
                  WHERE a.student_id = s.student_id AND a.drive_id = d.drive_id);

UPDATE application
SET status = CASE MOD(application_id, 5)
        WHEN 0 THEN 'Selected'
        WHEN 1 THEN 'In Progress'
        WHEN 2 THEN 'Rejected'
        ELSE 'Applied' END
WHERE application_id > 5;

SELECT COUNT(*) AS students     FROM student;
SELECT COUNT(*) AS applications FROM application;
SELECT COUNT(*) AS placed       FROM placement_record;
CALL sp_branch_placement_report();
