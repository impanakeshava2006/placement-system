-- ============================================================
-- Placement Management System — MySQL Schema
-- Generated from the ER / Relational diagram
-- ============================================================

CREATE DATABASE IF NOT EXISTS placement_system;
USE placement_system;

-- ------------------------------------------------------------
-- STUDENT
-- ------------------------------------------------------------
CREATE TABLE student (
    student_id      INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    branch          VARCHAR(50)  NOT NULL,
    cgpa            DECIMAL(4,2) NOT NULL,
    backlogs        INT          DEFAULT 0,
    skills          TEXT,
    internships     TEXT,
    email           VARCHAR(100) NOT NULL UNIQUE,
    phone           VARCHAR(15),
    password_hash   VARCHAR(255) NOT NULL
);

-- ------------------------------------------------------------
-- ADMIN
-- ------------------------------------------------------------
CREATE TABLE admin (
    admin_id        INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    role            VARCHAR(50)  NOT NULL,
    email           VARCHAR(100) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL
);

-- ------------------------------------------------------------
-- COMPANY
-- ------------------------------------------------------------
CREATE TABLE company (
    company_id          INT AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(150) NOT NULL,
    sector              VARCHAR(100),
    package_offered     DECIMAL(10,2),
    min_cgpa_required   DECIMAL(4,2),
    eligible_branches   VARCHAR(255)   -- comma-separated or normalize later if needed
);

-- ------------------------------------------------------------
-- DRIVE  (conducted by a COMPANY, managed by an ADMIN)
-- ------------------------------------------------------------
CREATE TABLE drive (
    drive_id        INT AUTO_INCREMENT PRIMARY KEY,
    company_id      INT NOT NULL,
    admin_id        INT NOT NULL,
    drive_date      DATE NOT NULL,
    job_role        VARCHAR(100),
    location        VARCHAR(100),
    rounds          INT DEFAULT 1,
    CONSTRAINT fk_drive_company
        FOREIGN KEY (company_id) REFERENCES company(company_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_drive_admin
        FOREIGN KEY (admin_id) REFERENCES admin(admin_id)
        ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- APPLICATION  (a STUDENT applies to a DRIVE)
-- ------------------------------------------------------------
CREATE TABLE application (
    application_id  INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT NOT NULL,
    drive_id        INT NOT NULL,
    status          VARCHAR(30) DEFAULT 'Applied',   -- Applied / In Progress / Rejected / Selected
    applied_date    DATE NOT NULL,
    CONSTRAINT fk_application_student
        FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_application_drive
        FOREIGN KEY (drive_id) REFERENCES drive(drive_id)
        ON DELETE CASCADE,
    CONSTRAINT uq_student_drive UNIQUE (student_id, drive_id)  -- one application per student per drive
);

-- ------------------------------------------------------------
-- ROUND_RESULT  (weak entity: identity depends on APPLICATION)
-- Composite primary key = application_id + round_name
-- ------------------------------------------------------------
CREATE TABLE round_result (
    application_id  INT NOT NULL,
    round_name      VARCHAR(50) NOT NULL,
    status          VARCHAR(30) DEFAULT 'Pending',   -- Pending / Cleared / Rejected
    remarks         TEXT,
    PRIMARY KEY (application_id, round_name),
    CONSTRAINT fk_round_application
        FOREIGN KEY (application_id) REFERENCES application(application_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- PLACEMENT_RECORD  (final outcome linking STUDENT + COMPANY)
-- ------------------------------------------------------------
CREATE TABLE placement_record (
    record_id       INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT NOT NULL UNIQUE,   -- 1:1 — one placement record per student
    company_id      INT NOT NULL,
    package          DECIMAL(10,2),
    date_of_offer   DATE,
    CONSTRAINT fk_placement_student
        FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_placement_company
        FOREIGN KEY (company_id) REFERENCES company(company_id)
        ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- PREDICTION  (ML model output per STUDENT)
-- ------------------------------------------------------------
CREATE TABLE prediction (
    prediction_id           INT AUTO_INCREMENT PRIMARY KEY,
    student_id              INT NOT NULL UNIQUE,   -- 1:1 — latest prediction per student
    placement_probability   DECIMAL(5,4),           -- e.g. 0.8745
    generated_on            DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_prediction_student
        FOREIGN KEY (student_id) REFERENCES student(student_id)
        ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Helpful indexes for common lookups
-- ------------------------------------------------------------
CREATE INDEX idx_application_status ON application(status);
CREATE INDEX idx_drive_company ON drive(company_id);
CREATE INDEX idx_student_branch ON student(branch);
