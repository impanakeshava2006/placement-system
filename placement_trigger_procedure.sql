-- ============================================================
-- Placement Management System — Triggers and Stored Procedures
-- Run this AFTER placement_schema_mysql.sql and the sample data:
--     mysql -u root -p < placement_trigger_procedure.sql
-- (It can be run again at any time: old versions are dropped first.)
-- ============================================================

USE placement_system;

DROP TRIGGER IF EXISTS trg_check_eligibility;
DROP TRIGGER IF EXISTS trg_application_selected;
DROP PROCEDURE IF EXISTS sp_branch_placement_report;
DROP PROCEDURE IF EXISTS sp_student_applications;

DELIMITER $$

-- ------------------------------------------------------------
-- TRIGGER 1 (BEFORE INSERT on application)
-- Stops an ineligible student from applying, even if the
-- insert is done directly in SQL: CGPA below the company's
-- minimum, or a branch that is not in the eligible list.
-- ------------------------------------------------------------
CREATE TRIGGER trg_check_eligibility
BEFORE INSERT ON application
FOR EACH ROW
BEGIN
    DECLARE v_cgpa      DECIMAL(4,2);
    DECLARE v_branch    VARCHAR(50);
    DECLARE v_min_cgpa  DECIMAL(4,2);
    DECLARE v_branches  VARCHAR(255);

    SELECT cgpa, branch INTO v_cgpa, v_branch
    FROM student
    WHERE student_id = NEW.student_id;

    SELECT c.min_cgpa_required, c.eligible_branches INTO v_min_cgpa, v_branches
    FROM drive d
    JOIN company c ON c.company_id = d.company_id
    WHERE d.drive_id = NEW.drive_id;

    IF v_min_cgpa IS NOT NULL AND v_cgpa < v_min_cgpa THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Not eligible: CGPA is below the minimum required';
    END IF;

    IF v_branches IS NOT NULL AND v_branches <> ''
       AND FIND_IN_SET(v_branch, REPLACE(v_branches, ' ', '')) = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Not eligible: branch is not allowed for this drive';
    END IF;
END$$

-- ------------------------------------------------------------
-- TRIGGER 2 (AFTER UPDATE on application)
-- When an application becomes 'Selected', a placement record is
-- created automatically (one per student; the company and the
-- package come from the drive's company).
-- ------------------------------------------------------------
CREATE TRIGGER trg_application_selected
AFTER UPDATE ON application
FOR EACH ROW
BEGIN
    IF NEW.status = 'Selected' AND OLD.status <> 'Selected' THEN
        INSERT IGNORE INTO placement_record (student_id, company_id, package, date_of_offer)
        SELECT NEW.student_id, d.company_id, c.package_offered, CURDATE()
        FROM drive d
        JOIN company c ON c.company_id = d.company_id
        WHERE d.drive_id = NEW.drive_id;
    END IF;
END$$

-- ------------------------------------------------------------
-- STORED PROCEDURE 1 (no parameter)
-- Branch-wise placement report: students, placed students,
-- placement percentage and average package for every branch.
-- ------------------------------------------------------------
CREATE PROCEDURE sp_branch_placement_report()
BEGIN
    SELECT s.branch,
           COUNT(DISTINCT s.student_id)  AS total_students,
           COUNT(DISTINCT p.record_id)   AS students_placed,
           ROUND(100 * COUNT(DISTINCT p.record_id) / COUNT(DISTINCT s.student_id), 1) AS placement_percent,
           ROUND(AVG(p.package), 0)      AS avg_package
    FROM student s
    LEFT JOIN placement_record p ON p.student_id = s.student_id
    GROUP BY s.branch
    ORDER BY placement_percent DESC, s.branch;
END$$

-- ------------------------------------------------------------
-- STORED PROCEDURE 2 (IN parameter)
-- All applications of one student with company and drive details.
-- ------------------------------------------------------------
CREATE PROCEDURE sp_student_applications(IN p_student_id INT)
BEGIN
    SELECT a.application_id,
           c.name AS company_name,
           d.job_role,
           d.location,
           d.drive_date,
           a.status,
           a.applied_date
    FROM application a
    JOIN drive d   ON a.drive_id   = d.drive_id
    JOIN company c ON d.company_id = c.company_id
    WHERE a.student_id = p_student_id
    ORDER BY a.applied_date;
END$$

DELIMITER ;
