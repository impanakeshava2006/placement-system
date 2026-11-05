-- ============================================================
-- Placement Management System — Sample Data (5 rows per table)
-- Run AFTER placement_schema_mysql.sql has created the tables.
-- If you already ran the smaller sample data file earlier,
-- clear the tables first (see the TRUNCATE block below).
-- ============================================================

USE placement_system;

-- ------------------------------------------------------------
-- Wipe existing sample rows before reloading (clean slate).
-- Order matters (children before parents) — handled automatically
-- here since FK checks are disabled for this block.
-- ------------------------------------------------------------
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE round_result;
TRUNCATE TABLE placement_record;
TRUNCATE TABLE prediction;
TRUNCATE TABLE application;
TRUNCATE TABLE drive;
TRUNCATE TABLE student;
TRUNCATE TABLE company;
TRUNCATE TABLE admin;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- ADMIN (5 rows, all columns filled)
-- ------------------------------------------------------------
INSERT INTO admin (name, role, email, password_hash) VALUES
('Priya Sharma', 'Placement Officer', 'priya.sharma@college.edu', 'placeholder_hash_a1'),
('Ravi Kumar', 'Placement Coordinator', 'ravi.kumar@college.edu', 'placeholder_hash_a2'),
('Meera Pillai', 'Training & Placement Head', 'meera.pillai@college.edu', 'placeholder_hash_a3'),
('Suresh Babu', 'Placement Officer', 'suresh.babu@college.edu', 'placeholder_hash_a4'),
('Kavya Reddy', 'Placement Coordinator', 'kavya.reddy@college.edu', 'placeholder_hash_a5');

-- ------------------------------------------------------------
-- COMPANY (5 rows, all columns filled)
-- ------------------------------------------------------------
INSERT INTO company (name, sector, package_offered, min_cgpa_required, eligible_branches) VALUES
('TechNova Solutions', 'IT Services', 650000.00, 7.0, 'CSE,IT,ECE'),
('FinEdge Analytics', 'Finance/Analytics', 900000.00, 7.5, 'CSE,IT'),
('GreenBuild Infra', 'Core/Infrastructure', 500000.00, 6.5, 'Civil,Mechanical'),
('Quantify Labs', 'Product/AI', 1200000.00, 8.0, 'CSE,IT,ECE'),
('UrbanLogix', 'Supply Chain/Logistics', 550000.00, 6.8, 'Mechanical,IT');

-- ------------------------------------------------------------
-- STUDENT (5 rows, all columns filled)
-- ------------------------------------------------------------
INSERT INTO student (name, branch, cgpa, backlogs, skills, internships, email, phone, password_hash) VALUES
('Ananya Rao', 'CSE', 8.7, 0, 'Python, SQL, React', 'Summer intern at Infosys', 'ananya.rao@college.edu', '9876543210', 'placeholder_hash_s1'),
('Rahul Mehta', 'IT', 7.9, 1, 'Java, Spring Boot', 'Intern at TCS', 'rahul.mehta@college.edu', '9876543211', 'placeholder_hash_s2'),
('Sneha Iyer', 'ECE', 8.2, 0, 'Embedded C, MATLAB', 'VLSI internship at Qualcomm', 'sneha.iyer@college.edu', '9876543212', 'placeholder_hash_s3'),
('Arjun Nair', 'Civil', 7.1, 0, 'AutoCAD, Revit', 'Site internship at L&T', 'arjun.nair@college.edu', '9876543213', 'placeholder_hash_s4'),
('Divya Krishnan', 'Mechanical', 7.6, 0, 'SolidWorks, ANSYS', 'Design internship at Tata Motors', 'divya.krishnan@college.edu', '9876543214', 'placeholder_hash_s5');

-- ------------------------------------------------------------
-- DRIVE (5 rows, all columns filled)
-- ------------------------------------------------------------
INSERT INTO drive (company_id, admin_id, drive_date, job_role, location, rounds) VALUES
(1, 1, '2026-11-10', 'Software Engineer', 'Bangalore', 3),
(2, 1, '2026-11-15', 'Data Analyst', 'Mumbai', 2),
(3, 2, '2026-11-20', 'Site Engineer', 'Chennai', 2),
(4, 3, '2026-11-25', 'ML Engineer', 'Hyderabad', 4),
(5, 2, '2026-12-01', 'Logistics Analyst', 'Pune', 2);

-- ------------------------------------------------------------
-- APPLICATION (5 rows, all columns filled)
-- ------------------------------------------------------------
INSERT INTO application (student_id, drive_id, status, applied_date) VALUES
(1, 1, 'Selected', '2026-10-20'),
(2, 1, 'In Progress', '2026-10-21'),
(3, 2, 'Rejected', '2026-10-22'),
(4, 3, 'Applied', '2026-10-23'),
(5, 4, 'Selected', '2026-10-24');

-- ------------------------------------------------------------
-- ROUND_RESULT (5 rows, all columns filled — no NULLs)
-- PK = application_id + round_name
-- ------------------------------------------------------------
INSERT INTO round_result (application_id, round_name, status, remarks) VALUES
(1, 'Aptitude Test', 'Cleared', 'Scored 85%'),
(1, 'Technical Interview', 'Cleared', 'Strong DSA fundamentals'),
(2, 'Aptitude Test', 'Cleared', 'Scored 72%'),
(3, 'Aptitude Test', 'Rejected', 'Below cutoff'),
(5, 'Technical Interview', 'Cleared', 'Excellent ML project discussion');

-- ------------------------------------------------------------
-- PLACEMENT_RECORD (5 rows, all columns filled; 1 per student)
-- ------------------------------------------------------------
INSERT INTO placement_record (student_id, company_id, package, date_of_offer) VALUES
(1, 1, 650000.00, '2026-10-25'),
(2, 1, 650000.00, '2026-10-26'),
(3, 2, 900000.00, '2026-10-27'),
(4, 3, 500000.00, '2026-10-28'),
(5, 4, 1200000.00, '2026-10-29');

-- ------------------------------------------------------------
-- PREDICTION (5 rows, all columns filled; 1 per student)
-- ------------------------------------------------------------
INSERT INTO prediction (student_id, placement_probability, generated_on) VALUES
(1, 0.9123, '2026-10-01 10:00:00'),
(2, 0.6745, '2026-10-01 10:05:00'),
(3, 0.7230, '2026-10-01 10:10:00'),
(4, 0.5510, '2026-10-01 10:15:00'),
(5, 0.8890, '2026-10-01 10:20:00');
