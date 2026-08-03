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

        correct = random.randint(12, 20)
        avg_time = random.randint(35, 60)
        easy_correct = random.randint(6, 10)
        medium_correct = random.randint(3, 6)
        hard_correct = correct - easy_correct - medium_correct
        current_difficulty = random.choice(["Easy", "Medium"])
        streak = random.randint(2, 7)
        confidence = random.randint(35, 70)

    elif skill == "Intermediate":

        correct = random.randint(17, 26)
        avg_time = random.randint(22, 42)
        easy_correct = random.randint(8, 10)
        medium_correct = random.randint(7, 10)
        hard_correct = correct - easy_correct - medium_correct
        current_difficulty = random.choice(["Easy", "Medium", "Hard"])
        streak = random.randint(4, 10)
        confidence = random.randint(50, 85)

    else:

        correct = random.randint(22, 30)
        avg_time = random.randint(15, 32)
        easy_correct = 10
        medium_correct = random.randint(8, 10)
        hard_correct = correct - easy_correct - medium_correct
        current_difficulty = random.choice(["Medium", "Hard"])
        streak = random.randint(7, 15)
        confidence = random.randint(70, 100)

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

df.to_csv("datasets/student_performance.csv", index=False)

print("========================================")
print("Dataset Created Successfully")
print("File Name : student_performance.csv")
print("Rows :", len(df))
print("========================================")