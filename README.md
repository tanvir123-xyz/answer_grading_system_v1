# NLP-Based Answer Grading System

> **Work in progress.** The current version supports data entry and automatic grading with four NLP algorithms. More features are planned (see [Roadmap](#roadmap)).

A Flask web application that automatically grades student answers by comparing them with a teacher's reference answer. Each answer is scored with four different similarity algorithms, so their results can be compared side by side.

## Features

- Add questions with maximum marks
- Add students (roll number, name, category: good / medium / weak)
- Add a reference (teacher) answer for each question
- Add student answers, including **unanswered questions** (stored as `NULL`)
- Dropdowns are loaded dynamically from MySQL, so no IDs are hardcoded
- Grade all student answers for a question with four algorithms:
  - Jaccard similarity
  - TF-IDF with cosine similarity
  - Word2Vec
  - SBERT (Sentence-BERT)
- **Manage Data** page: edit questions (text and marks), students, reference answers and student answers, or delete any entry
- Results page with one row per student, showing similarity and marks for each algorithm
- "View Answer" toggle to read each student's full answer without cluttering the table
- All results are saved in the database (including a letter grade per algorithm)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | MySQL |
| NLP / ML | scikit-learn, gensim, sentence-transformers, NumPy |

## Project Structure

```
answer_grading_system/
├── app.py                     # Flask routes
├── db.py                      # All MySQL queries and connection handling
├── grading.py                 # The four similarity algorithms
├── grading_service.py         # Runs algorithms, computes marks/grades, saves results
├── requirements.txt           # Python dependencies
├── schema.sql                 # Creates the database and tables
├── sample_data.sql            # Optional sample data for quick testing
├── templates/
│   ├── base.html              # Shared layout
│   ├── home.html              # Main menu
│   ├── add_question.html
│   ├── add_student.html
│   ├── add_reference_answer.html
│   ├── add_student_answer.html
│   ├── grade_answers.html     # Choose a question to grade
│   ├── grade_results.html     # Algorithm comparison table
│   ├── manage.html            # List of all data with Edit / Delete buttons
│   ├── edit_question.html
│   ├── edit_student.html
│   └── edit_answer.html       # Used for both reference and student answers
└── static/
    ├── css/style.css
    └── js/script.js
```

## Database Schema

The database is named `answer_grading` and has four tables:

- **students**: `student_id`, `roll_number` (unique), `student_name`, `category`
- **questions**: `question_id`, `question_text`, `max_marks`
- **answers**: `answer_id`, `question_id`, `student_id`, `answer_type` (`reference` or `student`), `answer_text`, `marks_obtained`
- **results**: `result_id`, `answer_id`, `algorithm`, `similarity`, `marks`, `grade`

Reference answers are stored in `answers` with `student_id = NULL` and `answer_type = 'reference'`. The full SQL is in `schema.sql`.

## Getting Started

### Prerequisites

- Python 3.9 or newer
- MySQL Server installed and running

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Create the database

```bash
mysql -u root -p < schema.sql
```

Optionally load sample data:

```bash
mysql -u root -p answer_grading < sample_data.sql
```

### 3. Create a virtual environment and install dependencies

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

> **Note:** `sentence-transformers` installs PyTorch, which is a large download and can take several minutes. The first time you run grading, SBERT also downloads its pretrained model (`all-MiniLM-L6-v2`, about 90 MB), so an internet connection is needed once.

### 4. Configure the database password

Open `db.py` and replace the placeholder with your own MySQL password:

```python
"password": "MY_PASSWORD",
```

Do not commit your real password to a public repository.

### 5. Run the app

```bash
python app.py
```

Open `http://127.0.0.1:5000/` in your browser.

## How to Use

1. **Add Question**: enter the question text and maximum marks.
2. **Add Student**: enter roll number, name and category.
3. **Add Reference Answer**: pick a question and enter the teacher's model answer.
4. **Add Student Answer**: pick a question and a student, then enter the answer. Leave it blank if the student did not answer.
5. **Grade Answers**: pick a question and click **Run Grading**. The results page shows every student's similarity and marks for all four algorithms.

A question needs one reference answer and at least one student answer before it can be graded.

6. **Manage Data**: fix mistakes. Edit any question, student or answer, or delete entries. Editing an answer, or changing a question's maximum marks, clears the old grading results for it, so click **Run Grading** again afterwards.

## How Grading Works

For each student answer, the system compares it with the question's reference answer using four algorithms. Each returns a similarity score between 0 and 1:

| Algorithm | Idea |
|-----------|------|
| Jaccard | Overlap of unique words between the two answers |
| TF-IDF | Cosine similarity between TF-IDF word-weight vectors |
| Word2Vec | Cosine similarity between averaged word vectors, using a small model trained on the answers for that question |
| SBERT | Cosine similarity between pretrained sentence embeddings |

The similarity is then converted into marks and a grade:

- **Marks** = similarity × maximum marks
- **Grade**: A (≥ 0.80), B (≥ 0.60), C (≥ 0.40), D (≥ 0.20), F (below 0.20)

An unanswered question scores 0 on every algorithm. Re-grading a question replaces its previous results instead of duplicating them.

## Known Limitations

- Word2Vec is trained on a very small corpus (the answers for one question), so its scores are less reliable than SBERT's.
- Marks are directly proportional to similarity, and the grade thresholds are fixed starting values that have not been tuned against real teacher marks.
- There is no login system; anyone with access to the app can add data and run grading.
- Deleting a question or student also deletes all of its answers and saved results (a confirmation prompt appears first).

## Roadmap

- Dashboard comparing the algorithms across all questions and students
- Teacher override for automatically calculated marks
- Combining the four algorithms into a single final score
- Tuning grade thresholds against teacher-assigned marks
- Environment-variable configuration for database credentials

## License

Educational project. Add a license of your choice if you plan to share or reuse the code.
