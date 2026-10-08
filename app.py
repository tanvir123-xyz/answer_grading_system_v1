"""
Main Flask application for the NLP-based Answer Grading System.

This file only contains ROUTES (the "controller" layer). All actual
database work lives in db.py, so this file stays short and easy to read.
Nothing here is hardcoded: question IDs and student IDs are always
loaded from MySQL and chosen by the user through dropdowns.
"""

from flask import Flask, render_template, request, redirect, url_for, flash

import db
import grading_service

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # needed for flash() messages


# ---------------------------------------------------------------------------
# Home page - lets the user choose what they want to add
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("home.html")


# ---------------------------------------------------------------------------
# Add Question
# ---------------------------------------------------------------------------
@app.route("/add-question", methods=["GET", "POST"])
def add_question():
    if request.method == "POST":
        question_text = request.form.get("question_text", "").strip()
        max_marks = request.form.get("max_marks", "").strip()

        if not question_text or not max_marks:
            flash("Question text and maximum marks are both required.", "error")
            return redirect(url_for("add_question"))

        try:
            max_marks = int(max_marks)
        except ValueError:
            flash("Maximum marks must be a whole number.", "error")
            return redirect(url_for("add_question"))

        db.add_question(question_text, max_marks)
        flash("Question added successfully!", "success")
        return redirect(url_for("add_question"))

    return render_template("add_question.html")


# ---------------------------------------------------------------------------
# Add Student
# ---------------------------------------------------------------------------
@app.route("/add-student", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        roll_number = request.form.get("roll_number", "").strip()
        student_name = request.form.get("student_name", "").strip()
        category = request.form.get("category", "").strip()

        if not roll_number or not student_name or not category:
            flash("Roll number, name and category are all required.", "error")
            return redirect(url_for("add_student"))

        try:
            roll_number = int(roll_number)
        except ValueError:
            flash("Roll number must be a whole number.", "error")
            return redirect(url_for("add_student"))

        if db.roll_number_exists(roll_number):
            flash("A student with that roll number already exists.", "error")
            return redirect(url_for("add_student"))

        db.add_student(roll_number, student_name, category)
        flash("Student added successfully!", "success")
        return redirect(url_for("add_student"))

    return render_template("add_student.html")


# ---------------------------------------------------------------------------
# Add Reference Answer (teacher's model answer - not linked to a student)
# ---------------------------------------------------------------------------
@app.route("/add-reference-answer", methods=["GET", "POST"])
def add_reference_answer():
    if request.method == "POST":
        question_id = request.form.get("question_id", "").strip()
        answer_text = request.form.get("answer_text", "").strip()

        if not question_id:
            flash("Please select a question.", "error")
            return redirect(url_for("add_reference_answer"))

        if not answer_text:
            flash("Reference answer text cannot be empty.", "error")
            return redirect(url_for("add_reference_answer"))

        db.add_answer(
            question_id=int(question_id),
            student_id=None,
            answer_type="reference",
            answer_text=answer_text,
        )
        flash("Reference answer added successfully!", "success")
        return redirect(url_for("add_reference_answer"))

    questions = db.get_all_questions()
    return render_template("add_reference_answer.html", questions=questions)


# ---------------------------------------------------------------------------
# Add Student Answer
# ---------------------------------------------------------------------------
@app.route("/add-student-answer", methods=["GET", "POST"])
def add_student_answer():
    if request.method == "POST":
        question_id = request.form.get("question_id", "").strip()
        student_id = request.form.get("student_id", "").strip()
        answer_text = request.form.get("answer_text", "").strip()

        if not question_id or not student_id:
            flash("Please select both a question and a student.", "error")
            return redirect(url_for("add_student_answer"))

        # An empty answer is allowed - it means the student did not answer.
        # We store that as NULL rather than an empty string.
        answer_text_to_store = answer_text if answer_text else None

        db.add_answer(
            question_id=int(question_id),
            student_id=int(student_id),
            answer_type="student",
            answer_text=answer_text_to_store,
        )
        flash("Student answer saved successfully!", "success")
        return redirect(url_for("add_student_answer"))

    questions = db.get_all_questions()
    students = db.get_all_students()
    return render_template(
        "add_student_answer.html", questions=questions, students=students
    )


# ---------------------------------------------------------------------------
# Grade Answers - runs all 4 algorithms on every student answer for a
# chosen question, saves the results, and shows a comparison table.
# ---------------------------------------------------------------------------
@app.route("/grade-answers", methods=["GET", "POST"])
def grade_answers():
    questions = db.get_all_questions()

    if request.method == "POST":
        question_id = request.form.get("question_id", "").strip()

        if not question_id:
            flash("Please select a question.", "error")
            return redirect(url_for("grade_answers"))

        question_id = int(question_id)

        try:
            results = grading_service.grade_question(question_id)
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("grade_answers"))

        question = next(
            (q for q in questions if q["question_id"] == question_id), None
        )
        return render_template(
            "grade_results.html", results=results, question=question
        )

    return render_template("grade_answers.html", questions=questions)


# ---------------------------------------------------------------------------
# Manage Data - list everything, with Edit / Delete buttons
# ---------------------------------------------------------------------------
@app.route("/manage")
def manage():
    all_answers = db.get_all_answers()
    return render_template(
        "manage.html",
        questions=db.get_all_questions(),
        students=db.get_all_students(),
        reference_answers=[a for a in all_answers if a["answer_type"] == "reference"],
        student_answers=[a for a in all_answers if a["answer_type"] == "student"],
    )


# ---------------------------------------------------------------------------
# Edit Question (text and maximum marks)
# ---------------------------------------------------------------------------
@app.route("/edit-question/<int:question_id>", methods=["GET", "POST"])
def edit_question(question_id):
    question = db.get_question(question_id)
    if question is None:
        flash("That question no longer exists.", "error")
        return redirect(url_for("manage"))

    if request.method == "POST":
        question_text = request.form.get("question_text", "").strip()
        max_marks = request.form.get("max_marks", "").strip()

        if not question_text or not max_marks:
            flash("Question text and maximum marks are both required.", "error")
            return redirect(url_for("edit_question", question_id=question_id))

        try:
            max_marks = int(max_marks)
        except ValueError:
            flash("Maximum marks must be a whole number.", "error")
            return redirect(url_for("edit_question", question_id=question_id))

        marks_changed = max_marks != question["max_marks"]
        db.update_question(question_id, question_text, max_marks)

        if marks_changed:
            # Saved marks were calculated from the old maximum, so they are
            # outdated now. The user just needs to click "Run Grading" again.
            db.clear_results_for_question(question_id)
            flash(
                "Question updated. Maximum marks changed, so its old grading "
                "results were cleared - run Grade Answers again.",
                "success",
            )
        else:
            flash("Question updated successfully!", "success")
        return redirect(url_for("manage"))

    return render_template("edit_question.html", question=question)


# ---------------------------------------------------------------------------
# Edit Student (roll number, name, category)
# ---------------------------------------------------------------------------
@app.route("/edit-student/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    student = db.get_student(student_id)
    if student is None:
        flash("That student no longer exists.", "error")
        return redirect(url_for("manage"))

    if request.method == "POST":
        roll_number = request.form.get("roll_number", "").strip()
        student_name = request.form.get("student_name", "").strip()
        category = request.form.get("category", "").strip()

        if not roll_number or not student_name or not category:
            flash("Roll number, name and category are all required.", "error")
            return redirect(url_for("edit_student", student_id=student_id))

        try:
            roll_number = int(roll_number)
        except ValueError:
            flash("Roll number must be a whole number.", "error")
            return redirect(url_for("edit_student", student_id=student_id))

        if db.roll_number_taken_by_other(roll_number, student_id):
            flash("Another student already has that roll number.", "error")
            return redirect(url_for("edit_student", student_id=student_id))

        db.update_student(student_id, roll_number, student_name, category)
        flash("Student updated successfully!", "success")
        return redirect(url_for("manage"))

    return render_template("edit_student.html", student=student)


# ---------------------------------------------------------------------------
# Edit Answer (works for both reference answers and student answers)
# ---------------------------------------------------------------------------
@app.route("/edit-answer/<int:answer_id>", methods=["GET", "POST"])
def edit_answer(answer_id):
    answer = db.get_answer(answer_id)
    if answer is None:
        flash("That answer no longer exists.", "error")
        return redirect(url_for("manage"))

    is_reference = answer["answer_type"] == "reference"

    if request.method == "POST":
        answer_text = request.form.get("answer_text", "").strip()

        if is_reference and not answer_text:
            flash("Reference answer text cannot be empty.", "error")
            return redirect(url_for("edit_answer", answer_id=answer_id))

        # A student answer may be blank (unanswered) - stored as NULL.
        db.update_answer(answer_id, answer_text if answer_text else None)

        # Saved grading results are outdated after an edit.
        if is_reference:
            # The reference answer affects every student of this question.
            db.clear_results_for_question(answer["question_id"])
        else:
            db.clear_results_for_answer(answer_id)

        flash(
            "Answer updated. Its old grading results were cleared - run "
            "Grade Answers again for this question.",
            "success",
        )
        return redirect(url_for("manage"))

    return render_template("edit_answer.html", answer=answer, is_reference=is_reference)


# ---------------------------------------------------------------------------
# Delete routes (POST only, so a link or page refresh can never delete)
# ---------------------------------------------------------------------------
@app.route("/delete-question/<int:question_id>", methods=["POST"])
def delete_question(question_id):
    db.delete_question(question_id)
    flash("Question deleted (along with its answers and results).", "success")
    return redirect(url_for("manage"))


@app.route("/delete-student/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    db.delete_student(student_id)
    flash("Student deleted (along with their answers and results).", "success")
    return redirect(url_for("manage"))


@app.route("/delete-answer/<int:answer_id>", methods=["POST"])
def delete_answer(answer_id):
    db.delete_answer(answer_id)
    flash("Answer deleted.", "success")
    return redirect(url_for("manage"))


if __name__ == "__main__":
    app.run(debug=True)
