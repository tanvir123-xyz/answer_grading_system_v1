"""
Database access module.

Every function here opens its own short-lived MySQL connection, does one
job, and closes the connection again afterwards. This keeps app.py free
of raw SQL, and makes each function easy to reuse later when you add the
grading algorithms (Jaccard, TF-IDF, Word2Vec, SBERT).
"""

import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_DATABASE_PASSWORD",   # <-- change this to your real MySQL password
    "database": "answer_grading",
}


def get_connection():
    """Open and return a new MySQL connection using the settings above."""
    return mysql.connector.connect(**DB_CONFIG)


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------
def add_question(question_text, max_marks):
    con = get_connection()
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT INTO questions (question_text, max_marks) VALUES (%s, %s)",
            (question_text, max_marks),
        )
        con.commit()
    finally:
        cur.close()
        con.close()


def get_all_questions():
    """Return every question as a list of dicts, for use in dropdowns."""
    con = get_connection()
    cur = con.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT question_id, question_text, max_marks "
            "FROM questions ORDER BY question_id"
        )
        return cur.fetchall()
    finally:
        cur.close()
        con.close()


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------
def add_student(roll_number, student_name, category):
    con = get_connection()
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT INTO students (roll_number, student_name, category) "
            "VALUES (%s, %s, %s)",
            (roll_number, student_name, category),
        )
        con.commit()
    finally:
        cur.close()
        con.close()


def roll_number_exists(roll_number):
    con = get_connection()
    cur = con.cursor()
    try:
        cur.execute(
            "SELECT student_id FROM students WHERE roll_number = %s",
            (roll_number,),
        )
        return cur.fetchone() is not None
    finally:
        cur.close()
        con.close()


def get_all_students():
    """Return every student as a list of dicts, for use in dropdowns."""
    con = get_connection()
    cur = con.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT student_id, roll_number, student_name, category "
            "FROM students ORDER BY roll_number"
        )
        return cur.fetchall()
    finally:
        cur.close()
        con.close()


# ---------------------------------------------------------------------------
# Answers (both reference answers and student answers live in this table,
# distinguished by the answer_type column)
# ---------------------------------------------------------------------------
def add_answer(question_id, student_id, answer_type, answer_text):
    con = get_connection()
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT INTO answers (question_id, student_id, answer_type, answer_text) "
            "VALUES (%s, %s, %s, %s)",
            (question_id, student_id, answer_type, answer_text),
        )
        con.commit()
    finally:
        cur.close()
        con.close()


def get_reference_answer(question_id):
    """Return the teacher's reference answer for a question, or None.

    You will use this once you start writing the grading algorithms:
    compare this text against each student answer from get_student_answers().
    """
    con = get_connection()
    cur = con.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT answer_id, answer_text FROM answers "
            "WHERE question_id = %s AND answer_type = 'reference' "
            "LIMIT 1",
            (question_id,),
        )
        return cur.fetchone()
    finally:
        cur.close()
        con.close()


def get_student_answers(question_id):
    """Return every student answer submitted for a given question."""
    con = get_connection()
    cur = con.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT a.answer_id, a.answer_text, a.marks_obtained, "
            "       s.student_id, s.roll_number, s.student_name, s.category "
            "FROM answers a "
            "JOIN students s ON a.student_id = s.student_id "
            "WHERE a.question_id = %s AND a.answer_type = 'student'",
            (question_id,),
        )
        return cur.fetchall()
    finally:
        cur.close()
        con.close()


# ---------------------------------------------------------------------------
# Results (one row per answer + algorithm, produced by grading_service.py)
# ---------------------------------------------------------------------------
def save_result(answer_id, algorithm, similarity, marks, grade):
    con = get_connection()
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT INTO results (answer_id, algorithm, similarity, marks, grade) "
            "VALUES (%s, %s, %s, %s, %s)",
            (answer_id, algorithm, similarity, marks, grade),
        )
        con.commit()
    finally:
        cur.close()
        con.close()


def clear_results_for_question(question_id):
    """Delete any existing results for every answer to this question, so
    re-grading doesn't leave old/duplicate rows behind."""
    con = get_connection()
    cur = con.cursor()
    try:
        cur.execute(
            "DELETE r FROM results r "
            "JOIN answers a ON r.answer_id = a.answer_id "
            "WHERE a.question_id = %s",
            (question_id,),
        )
        con.commit()
    finally:
        cur.close()
        con.close()


# ---------------------------------------------------------------------------
# Edit / delete support (used by the Manage Data pages)
# ---------------------------------------------------------------------------
def _run_write(query, params):
    """Run one INSERT/UPDATE/DELETE statement and commit it."""
    con = get_connection()
    cur = con.cursor()
    try:
        cur.execute(query, params)
        con.commit()
    finally:
        cur.close()
        con.close()


def _fetch_one(query, params):
    con = get_connection()
    cur = con.cursor(dictionary=True)
    try:
        cur.execute(query, params)
        return cur.fetchone()
    finally:
        cur.close()
        con.close()


# ----- Questions -----
def get_question(question_id):
    return _fetch_one(
        "SELECT question_id, question_text, max_marks FROM questions "
        "WHERE question_id = %s",
        (question_id,),
    )


def update_question(question_id, question_text, max_marks):
    _run_write(
        "UPDATE questions SET question_text = %s, max_marks = %s "
        "WHERE question_id = %s",
        (question_text, max_marks, question_id),
    )


def delete_question(question_id):
    # ON DELETE CASCADE removes this question's answers and results too.
    _run_write("DELETE FROM questions WHERE question_id = %s", (question_id,))


# ----- Students -----
def get_student(student_id):
    return _fetch_one(
        "SELECT student_id, roll_number, student_name, category FROM students "
        "WHERE student_id = %s",
        (student_id,),
    )


def roll_number_taken_by_other(roll_number, student_id):
    """True if a DIFFERENT student already uses this roll number."""
    row = _fetch_one(
        "SELECT student_id FROM students "
        "WHERE roll_number = %s AND student_id <> %s",
        (roll_number, student_id),
    )
    return row is not None


def update_student(student_id, roll_number, student_name, category):
    _run_write(
        "UPDATE students SET roll_number = %s, student_name = %s, category = %s "
        "WHERE student_id = %s",
        (roll_number, student_name, category, student_id),
    )


def delete_student(student_id):
    # ON DELETE CASCADE removes this student's answers and results too.
    _run_write("DELETE FROM students WHERE student_id = %s", (student_id,))


# ----- Answers (reference and student) -----
def get_answer(answer_id):
    """One answer plus the context needed to show it on the edit page."""
    return _fetch_one(
        "SELECT a.answer_id, a.question_id, a.answer_type, a.answer_text, "
        "       q.question_text, s.roll_number, s.student_name "
        "FROM answers a "
        "JOIN questions q ON a.question_id = q.question_id "
        "LEFT JOIN students s ON a.student_id = s.student_id "
        "WHERE a.answer_id = %s",
        (answer_id,),
    )


def get_all_answers():
    """Every answer (reference first, then students) for the Manage page."""
    con = get_connection()
    cur = con.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT a.answer_id, a.question_id, a.answer_type, a.answer_text, "
            "       s.roll_number, s.student_name "
            "FROM answers a "
            "LEFT JOIN students s ON a.student_id = s.student_id "
            "ORDER BY a.question_id, a.answer_type, s.roll_number"
        )
        return cur.fetchall()
    finally:
        cur.close()
        con.close()


def update_answer(answer_id, answer_text):
    _run_write(
        "UPDATE answers SET answer_text = %s WHERE answer_id = %s",
        (answer_text, answer_id),
    )


def delete_answer(answer_id):
    # ON DELETE CASCADE removes this answer's saved results too.
    _run_write("DELETE FROM answers WHERE answer_id = %s", (answer_id,))


def clear_results_for_answer(answer_id):
    """Remove saved results for one answer (they are outdated after an edit)."""
    _run_write("DELETE FROM results WHERE answer_id = %s", (answer_id,))
