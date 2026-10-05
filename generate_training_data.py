import pandas as pd
import numpy as np

np.random.seed(42)

n_samples = 300

branches = ["CSE", "IT", "ECE", "Mechanical", "Civil"]

data = {
    "cgpa": np.round(np.random.uniform(5.5, 9.8, n_samples), 2),
    "backlogs": np.random.choice([0, 0, 0, 1, 1, 2, 3], n_samples),
    "internships": np.random.choice([0, 1, 1, 2], n_samples),
    "skills_count": np.random.randint(1, 8, n_samples),
    "branch": np.random.choice(branches, n_samples)
}

df = pd.DataFrame(data)

# Simple rule-based logic to generate realistic placement outcomes
# (higher cgpa, more internships/skills, fewer backlogs = more likely placed)
score = (
    (df["cgpa"] - 5.5) * 1.5
    + df["internships"] * 1.2
    + df["skills_count"] * 0.4
    - df["backlogs"] * 1.8
    + np.random.normal(0, 1.5, n_samples)  # randomness so it's not too perfect
)

df["placed"] = (score > score.median()).astype(int)

df.to_csv("training_data.csv", index=False)
print("Generated training_data.csv with", len(df), "rows")
print(df["placed"].value_counts())
