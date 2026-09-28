-- =============================================================
-- Optional sample data - run this AFTER schema.sql if you want
-- some rows to test with right away instead of typing everything
-- through the web forms.
-- =============================================================

USE answer_grading;

INSERT INTO questions (question_text, max_marks) VALUES
('What is the difference between supervised and unsupervised learning?', 10),
('Explain the concept of overfitting in machine learning.', 10);

INSERT INTO students (roll_number, student_name, category) VALUES
(1, 'Aisha Khan', 'good'),
(2, 'Ravi Sharma', 'medium'),
(3, 'Tom Lee', 'weak');

-- Reference (teacher) answers: student_id is NULL, answer_type is 'reference'
INSERT INTO answers (question_id, student_id, answer_type, answer_text) VALUES
(1, NULL, 'reference',
 'Supervised learning uses labeled data to train a model, while unsupervised learning finds patterns in unlabeled data.'),
(2, NULL, 'reference',
 'Overfitting happens when a model learns the training data too well, including its noise, and performs poorly on new data.');

-- Student answers, including one unanswered question (answer_text = NULL)
INSERT INTO answers (question_id, student_id, answer_type, answer_text) VALUES
(1, 1, 'student', 'Supervised learning uses labeled data; unsupervised learning uses unlabeled data to find patterns.'),
(1, 2, 'student', 'Supervised learning has labels, unsupervised does not.'),
(1, 3, 'student', NULL),
(2, 1, 'student', 'Overfitting is when a model memorizes the training data and does badly on unseen data.'),
(2, 2, 'student', 'It is when the model is too complex.'),
(2, 3, 'student', NULL);
