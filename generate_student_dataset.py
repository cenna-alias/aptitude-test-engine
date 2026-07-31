import random
import pandas as pd

students = []

NUM_STUDENTS = 5000

for student_id in range(1, NUM_STUDENTS + 1):

    questions_attempted = 30

    skill = random.choices(
        ["Beginner", "Intermediate", "Advanced"],
        weights=[30, 40, 30]
    )[0]

    if skill == "Beginner":

        correct = random.randint(10, 18)
        avg_time = random.randint(38, 60)
        easy_correct = random.randint(6, 10)
        medium_correct = random.randint(3, 6)
        hard_correct = correct - easy_correct - medium_correct
        current_difficulty = "Easy"
        streak = random.randint(2, 5)
        confidence = random.randint(40, 60)

    elif skill == "Intermediate":

        correct = random.randint(19, 24)
        avg_time = random.randint(25, 38)
        easy_correct = random.randint(8, 10)
        medium_correct = random.randint(7, 10)
        hard_correct = correct - easy_correct - medium_correct
        current_difficulty = "Medium"
        streak = random.randint(5, 9)
        confidence = random.randint(61, 80)

    else:

        correct = random.randint(25, 30)
        avg_time = random.randint(15, 25)
        easy_correct = 10
        medium_correct = random.randint(8, 10)
        hard_correct = correct - easy_correct - medium_correct
        current_difficulty = "Hard"
        streak = random.randint(8, 15)
        confidence = random.randint(81, 100)

    if hard_correct < 0:
        hard_correct = 0

    wrong = questions_attempted - correct

    easy_wrong = max(0, 10 - easy_correct)
    medium_wrong = max(0, 10 - medium_correct)
    hard_wrong = wrong - easy_wrong - medium_wrong

    if hard_wrong < 0:
        hard_wrong = 0

    accuracy = round((correct / questions_attempted) * 100, 2)

    final_score = (
        easy_correct * 1 +
        medium_correct * 2 +
        hard_correct * 3
    )

    students.append([
        student_id,
        questions_attempted,
        correct,
        wrong,
        accuracy,
        avg_time,
        easy_correct,
        medium_correct,
        hard_correct,
        easy_wrong,
        medium_wrong,
        hard_wrong,
        current_difficulty,
        streak,
        confidence,
        final_score,
        skill
    ])

columns = [
    "StudentID",
    "QuestionsAttempted",
    "CorrectAnswers",
    "WrongAnswers",
    "Accuracy",
    "AverageResponseTime",
    "EasyCorrect",
    "MediumCorrect",
    "HardCorrect",
    "EasyWrong",
    "MediumWrong",
    "HardWrong",
    "CurrentDifficulty",
    "LongestCorrectStreak",
    "ConfidenceScore",
    "FinalScore",
    "SkillLevel"
]

df = pd.DataFrame(students, columns=columns)

df.to_csv("student_performance.csv", index=False)

print("========================================")
print("Dataset Created Successfully")
print("File Name : student_performance.csv")
print("Rows :", len(df))
print("========================================")