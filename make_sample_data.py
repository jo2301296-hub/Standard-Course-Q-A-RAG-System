import os
import pandas as pd
from docx import Document
from fpdf import FPDF

DATA_DIR = "data"

COURSES = {
    "python": {
        "txt": ("python_basics.txt", """Python Basics

Python is a high-level, interpreted programming language known for its readable syntax. Variables in Python do not need a declared type; the type is decided at runtime. For example, x = 5 creates an integer and name = 'Ali' creates a string.

A list is an ordered, mutable collection written with square brackets, for example [1, 2, 3]. A tuple is an ordered, immutable collection written with parentheses. A dictionary stores key-value pairs inside curly braces, for example {'name': 'Ali', 'age': 20}. A set stores unique items with no order.

Control flow uses if, elif and else statements. Loops are written with for and while. The range() function generates a sequence of numbers and is commonly used in for loops."""),
        "csv": ("python_terms.csv", [
            {"term": "function", "definition": "A reusable block of code defined with the def keyword", "example": "def add(a, b): return a + b"},
            {"term": "list comprehension", "definition": "A short syntax to build a list from an iterable", "example": "[x*x for x in range(5)]"},
            {"term": "lambda", "definition": "An anonymous one-line function", "example": "lambda x: x + 1"},
            {"term": "decorator", "definition": "A function that wraps another function to extend its behavior", "example": "@my_decorator"},
            {"term": "virtual environment", "definition": "An isolated Python environment with its own installed packages", "example": "python -m venv venv"},
            {"term": "pip", "definition": "The package installer for Python", "example": "pip install pandas"},
        ]),
        "docx": ("python_oop.docx", [
            ("Classes and Objects", "A class is a blueprint for creating objects. An object is an instance of a class. A class is defined with the class keyword, and the __init__ method is the constructor that runs when a new object is created. The first parameter of every instance method is self, which refers to the current object."),
            ("Inheritance", "Inheritance lets a child class reuse the attributes and methods of a parent class. In Python the parent class is written in parentheses after the child class name. The super() function gives access to the parent class methods."),
            ("Encapsulation and Polymorphism", "Encapsulation means hiding internal data; by convention an attribute that starts with an underscore is treated as private. Polymorphism means different classes can provide their own version of the same method name."),
        ]),
        "pdf": ("python_files_errors.pdf", [
            ("File Handling", "Use the open() function to work with files. The modes are r for reading, w for writing (which overwrites the file) and a for appending. The with statement closes the file automatically, so it is the recommended way: with open('data.txt') as f: text = f.read()."),
            ("Exception Handling", "Errors are handled with try and except blocks. Code that might fail goes in try, and the except block runs if an error occurs. The finally block always runs. Use raise to throw an exception manually. Common exceptions are ValueError, TypeError, KeyError and FileNotFoundError."),
        ]),
    },
    "machine_learning": {
        "txt": ("ml_intro.txt", """Introduction to Machine Learning

Machine learning is a field of artificial intelligence where models learn patterns from data instead of being explicitly programmed.

In supervised learning the training data has labels and the model learns to predict them. Classification predicts categories and regression predicts continuous numbers. In unsupervised learning there are no labels and the model finds structure on its own, for example clusters; K-Means is a common clustering algorithm. Reinforcement learning trains an agent using rewards and penalties.

Overfitting happens when a model learns the training data too well, including its noise, and performs poorly on new data. Underfitting happens when a model is too simple to capture the pattern in the data."""),
        "csv": ("ml_metrics.csv", [
            {"metric": "accuracy", "used_for": "classification", "definition": "Share of all predictions that are correct", "formula": "(TP+TN)/(TP+TN+FP+FN)"},
            {"metric": "precision", "used_for": "classification", "definition": "Share of predicted positives that are truly positive", "formula": "TP/(TP+FP)"},
            {"metric": "recall", "used_for": "classification", "definition": "Share of actual positives that the model found", "formula": "TP/(TP+FN)"},
            {"metric": "f1-score", "used_for": "classification", "definition": "Harmonic mean of precision and recall", "formula": "2*P*R/(P+R)"},
            {"metric": "MSE", "used_for": "regression", "definition": "Average of the squared errors", "formula": "mean((y - y_pred)^2)"},
            {"metric": "R2", "used_for": "regression", "definition": "Share of the variance explained by the model", "formula": "1 - SS_res/SS_tot"},
        ]),
        "docx": ("ml_evaluation.docx", [
            ("Train/Test Split", "The dataset is split into a training set used to fit the model and a test set used to evaluate it on unseen data. A common split is 80 percent training and 20 percent testing. The test set must never be used during training."),
            ("Cross-Validation", "In k-fold cross-validation the data is divided into k equal parts. The model is trained k times, each time using a different part as the validation set and the remaining parts for training. The final score is the average of the k results, which gives a more reliable estimate than a single split."),
            ("Data Preprocessing", "Before training, data is cleaned by handling missing values and removing duplicates. Numeric features are often scaled using standardization or min-max normalization. Categorical features are converted to numbers using one-hot encoding."),
        ]),
        "pdf": ("ml_optimization.pdf", [
            ("Gradient Descent", "Gradient descent is an optimization algorithm that minimizes a loss function by repeatedly moving the model parameters in the direction opposite to the gradient. The learning rate controls the step size. If it is too large the training may diverge, and if it is too small the training is very slow."),
            ("Regularization", "Regularization reduces overfitting by penalizing large weights. L1 regularization (Lasso) adds the absolute values of the weights to the loss and can shrink some weights to exactly zero. L2 regularization (Ridge) adds the squared weights and shrinks them smoothly. Dropout randomly turns off neurons during training in neural networks."),
        ]),
    },
    "databases": {
        "txt": ("db_intro.txt", """Introduction to Databases

A database is an organized collection of data. A relational database stores data in tables made of rows and columns. Each row is a record and each column is an attribute.

A primary key uniquely identifies each row in a table and cannot be null. A foreign key is a column that references the primary key of another table and is used to link tables together.

SQL (Structured Query Language) is the standard language for working with relational databases. It is used to create tables, insert data, query data, update data and delete data."""),
        "csv": ("sql_commands.csv", [
            {"command": "SELECT", "purpose": "Read rows from a table", "example": "SELECT name FROM students;"},
            {"command": "INSERT", "purpose": "Add a new row to a table", "example": "INSERT INTO students (name) VALUES ('Ali');"},
            {"command": "UPDATE", "purpose": "Change existing rows", "example": "UPDATE students SET name = 'Omar' WHERE id = 1;"},
            {"command": "DELETE", "purpose": "Remove rows from a table", "example": "DELETE FROM students WHERE id = 1;"},
            {"command": "JOIN", "purpose": "Combine rows from two tables using a related column", "example": "SELECT * FROM a JOIN b ON a.id = b.a_id;"},
            {"command": "GROUP BY", "purpose": "Group rows so aggregate functions can be applied", "example": "SELECT dept, COUNT(*) FROM emp GROUP BY dept;"},
        ]),
        "docx": ("db_normalization.docx", [
            ("First Normal Form (1NF)", "A table is in 1NF when every column holds atomic values, meaning no repeating groups and no lists inside a single cell. Each row must be unique."),
            ("Second Normal Form (2NF)", "A table is in 2NF when it is in 1NF and every non-key column depends on the whole primary key, not just a part of it. This matters for tables with composite keys."),
            ("Third Normal Form (3NF)", "A table is in 3NF when it is in 2NF and no non-key column depends on another non-key column. This removes transitive dependencies and reduces data redundancy."),
        ]),
        "pdf": ("db_transactions.pdf", [
            ("Transactions and ACID", "A transaction is a group of database operations that must succeed or fail together. ACID stands for Atomicity (all or nothing), Consistency (the database moves from one valid state to another), Isolation (concurrent transactions do not interfere) and Durability (committed changes survive failures). COMMIT saves a transaction and ROLLBACK cancels it."),
            ("Indexes", "An index is a data structure, usually a B-tree, that speeds up searching on a column. Queries with WHERE or JOIN on an indexed column are much faster. The cost is extra storage and slower INSERT, UPDATE and DELETE operations because the index must be maintained."),
        ]),
    },
}


def write_pdf(path, sections):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    for title, body in sections:
        pdf.add_page()                      # كل قسم في صفحة عشان نجرب رقم الصفحة
        pdf.set_font("Helvetica", "B", 16)
        pdf.multi_cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 12)
        pdf.multi_cell(0, 7, body, new_x="LMARGIN", new_y="NEXT")
    pdf.output(path)


def write_docx(path, sections):
    doc = Document()
    for title, body in sections:
        doc.add_heading(title, level=1)
        doc.add_paragraph(body)
    doc.save(path)


def main():
    for course, files in COURSES.items():
        folder = os.path.join(DATA_DIR, course)
        os.makedirs(folder, exist_ok=True)

        name, text = files["txt"]
        with open(os.path.join(folder, name), "w", encoding="utf-8") as f:
            f.write(text)

        name, rows = files["csv"]
        pd.DataFrame(rows).to_csv(os.path.join(folder, name), index=False)

        name, sections = files["docx"]
        write_docx(os.path.join(folder, name), sections)

        name, sections = files["pdf"]
        write_pdf(os.path.join(folder, name), sections)

        print(f"Created sample data for: {course}")


if __name__ == "__main__":
    main()