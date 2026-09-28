"""
Grading service - orchestrates running every algorithm on every student
answer for a question, converts each similarity score into marks and a
grade, and saves everything into the `results` table.

Kept separate from app.py and db.py so the "business logic" (how a
similarity score becomes marks/a grade) is in one obvious place.
"""

import db
import grading

ALGORITHMS = ["jaccard", "tfidf", "word2vec", "sbert"]


def similarity_to_marks_and_grade(similarity, max_marks):
    """
    Convert a 0.0-1.0 similarity score into marks (out of max_marks) and
    a letter grade, using fixed threshold bands. Feel free to tune the
    thresholds once you have real student data to compare against.
    """
    marks = round(similarity * max_marks, 2)

    if similarity >= 0.80:
        grade = "A"
    elif similarity >= 0.60:
        grade = "B"
    elif similarity >= 0.40:
        grade = "C"
    elif similarity >= 0.20:
        grade = "D"
    else:
        grade = "F"

    return marks, grade


def grade_question(question_id):
    """
    Run all four algorithms on every student answer for this question,
    save each result to the database, and return the results as a list
    of dicts ready to display in a template.

    Re-running this for the same question first clears any previous
    results for it, so grading is idempotent (no duplicate rows pile up
    if you click "Grade" twice).
    """
    questions = {q["question_id"]: q for q in db.get_all_questions()}
    question = questions.get(question_id)
    if question is None:
        raise ValueError("Question not found.")

    max_marks = question["max_marks"]

    reference = db.get_reference_answer(question_id)
    if reference is None:
        raise ValueError(
            "No reference answer has been added for this question yet."
        )
    reference_text = reference["answer_text"] or ""

    student_answers = db.get_student_answers(question_id)
    if not student_answers:
        raise ValueError("No student answers have been submitted for this question yet.")

    all_student_texts = [a["answer_text"] for a in student_answers if a["answer_text"]]

    db.clear_results_for_question(question_id)

    results_by_student = []

    for answer in student_answers:
        student_text = answer["answer_text"] or ""

        # --- Calculations are unchanged from before ---
        scores = {
            "jaccard": grading.jaccard_similarity(reference_text, student_text),
            "tfidf": grading.tfidf_similarity(reference_text, student_text),
            "word2vec": grading.word2vec_similarity(
                reference_text, student_text, corpus_texts=all_student_texts
            ),
            "sbert": grading.sbert_similarity(reference_text, student_text),
        }

        algorithm_results = {}

        for algorithm in ALGORITHMS:
            similarity = scores[algorithm]
            similarity_pct = round(similarity * 100, 2)
            marks, grade = similarity_to_marks_and_grade(similarity, max_marks)

            # Saving to the database is unchanged: still one row per
            # (answer, algorithm) in `results`, still includes grade.
            db.save_result(
                answer_id=answer["answer_id"],
                algorithm=algorithm,
                similarity=similarity_pct,
                marks=marks,
                grade=grade,
            )

            # grade is kept here too (backend data), the template just
            # doesn't render it.
            algorithm_results[algorithm] = {
                "similarity": similarity_pct,
                "marks": marks,
                "grade": grade,
            }

        # One entry per STUDENT, holding all four algorithms' results
        # nested inside it - this is what lets the results page show
        # one row per student instead of one row per algorithm.
        results_by_student.append(
            {
                "roll_number": answer["roll_number"],
                "student_name": answer["student_name"],
                "category": answer["category"],  # kept for backend use
                "answer_text": student_text if student_text else "(no answer)",
                "max_marks": max_marks,
                "algorithms": algorithm_results,
            }
        )

    results_by_student.sort(key=lambda row: row["roll_number"])

    return results_by_student
