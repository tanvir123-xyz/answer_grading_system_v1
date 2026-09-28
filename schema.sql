-- =============================================================
-- Answer Grading System - Database Schema
-- =============================================================
--
-- This is your original schema with three small, explained changes:
--
-- 1. answers.question_id is now NOT NULL.
--    Every answer (reference or student) must belong to a question,
--    so it should never be left empty.
--
-- 2. marks_obtained and results.marks widened from DECIMAL(3,2) to
--    DECIMAL(4,2). DECIMAL(3,2) can only store up to 9.99, which is
--    too small if a question is worth 10 or more marks.
--
-- 3. ON DELETE CASCADE added to the foreign keys.
--    If you delete a question or a student while testing, their
--    related answers/results are cleaned up automatically instead of
--    blocking the delete with a foreign-key error.
--
-- Everything else (table names, column names, column meanings) is
-- exactly what you designed.
-- =============================================================

CREATE DATABASE IF NOT EXISTS answer_grading;
USE answer_grading;

DROP TABLE IF EXISTS results;
DROP TABLE IF EXISTS answers;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS questions;

-- ---------------------------------------------------------------
-- Students
-- ---------------------------------------------------------------
CREATE TABLE students (
    student_id   INT AUTO_INCREMENT PRIMARY KEY,
    roll_number  INT NOT NULL UNIQUE,
    student_name VARCHAR(100) NOT NULL,
    category     VARCHAR(20) NOT NULL   -- 'good', 'medium', or 'weak'
);

-- ---------------------------------------------------------------
-- Questions
-- ---------------------------------------------------------------
CREATE TABLE questions (
    question_id   INT AUTO_INCREMENT PRIMARY KEY,
    question_text TEXT NOT NULL,
    max_marks     INT NOT NULL
);

-- ---------------------------------------------------------------
-- Answers
-- Holds BOTH the teacher's reference answer (student_id = NULL,
-- answer_type = 'reference') AND every student's answer
-- (answer_type = 'student'). answer_text is NULL when a student
-- did not answer the question at all.
-- ---------------------------------------------------------------
CREATE TABLE answers (
    answer_id      INT AUTO_INCREMENT PRIMARY KEY,
    question_id    INT NOT NULL,
    student_id     INT NULL,
    answer_type    VARCHAR(20) NOT NULL,     -- 'reference' or 'student'
    answer_text    TEXT NULL,
    marks_obtained DECIMAL(4,2) NULL,

    FOREIGN KEY (question_id) REFERENCES questions(question_id)
        ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);

-- ---------------------------------------------------------------
-- Results
-- One row per (answer, algorithm) pair, added once you start
-- comparing student answers against the reference answer with
-- Jaccard / TF-IDF / Word2Vec / SBERT.
-- ---------------------------------------------------------------
CREATE TABLE results (
    result_id  INT AUTO_INCREMENT PRIMARY KEY,
    answer_id  INT NOT NULL,
    algorithm  VARCHAR(50) NOT NULL,
    similarity DECIMAL(5,2),
    marks      DECIMAL(4,2),
    grade      VARCHAR(5),

    FOREIGN KEY (answer_id) REFERENCES answers(answer_id)
        ON DELETE CASCADE
);
