-- ============================================================
-- Placement Management System — JOIN queries
-- Run after the schema, sample data, and triggers/procedures.
-- Column names are taken from placement_trigger_procedure.sql;
-- adjust if your schema differs.
-- ============================================================

USE placement_system;

-- ------------------------------------------------------------
-- JOIN 1 (INNER JOIN, 4 tables)
-- Every application with student, company and drive details.
-- ------------------------------------------------------------
SELECT a.application_id,
       s.name        AS student_name,
       s.branch,
       c.name        AS company_name,
       d.job_role,
       d.drive_date,
       a.status
FROM application a
JOIN student s ON s.student_id = a.student_id
JOIN drive   d ON d.drive_id   = a.drive_id
JOIN company c ON c.company_id = d.company_id
ORDER BY a.applied_date;

-- ------------------------------------------------------------
-- JOIN 2 (LEFT JOIN + GROUP BY)
-- Per company: number of drives, applications and selected
-- students. Selected is counted with a conditional SUM so the
-- count is correct and companies with no applications show 0.
-- ------------------------------------------------------------
SELECT c.name AS company_name,
       COUNT(DISTINCT d.drive_id)                    AS total_drives,
       COUNT(a.application_id)                       AS total_applications,
       COALESCE(SUM(a.status = 'Selected'), 0)       AS selected_count
FROM company c
LEFT JOIN drive d       ON d.company_id = c.company_id
LEFT JOIN application a ON a.drive_id   = d.drive_id
GROUP BY c.company_id, c.name
ORDER BY selected_count DESC, c.name;

-- ------------------------------------------------------------
-- JOIN 3 (INNER JOIN with placement_record)
-- Placed students with company and package, highest first.
-- ------------------------------------------------------------
SELECT s.student_id,
       s.name AS student_name,
       s.branch,
       s.cgpa,
       c.name AS company_name,
       p.package,
       p.date_of_offer
FROM placement_record p
JOIN student s ON s.student_id = p.student_id
JOIN company c ON c.company_id = p.company_id
ORDER BY p.package DESC;

-- ------------------------------------------------------------
-- JOIN 4 (LEFT JOIN ... IS NULL)
-- Students who have not applied to any drive yet.
-- ------------------------------------------------------------
SELECT s.student_id, s.name, s.branch, s.cgpa
FROM student s
LEFT JOIN application a ON a.student_id = s.student_id
WHERE a.application_id IS NULL
ORDER BY s.branch, s.name;
