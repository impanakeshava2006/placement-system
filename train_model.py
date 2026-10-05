import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
import joblib

# Load the synthetic data
df = pd.read_csv("training_data.csv")

X = df[["cgpa", "backlogs", "internships", "skills_count", "branch"]]
y = df["placed"]

# Split into train/test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Preprocessing: scale numeric columns, one-hot encode branch
preprocessor = ColumnTransformer(transformers=[
    ("num", StandardScaler(), ["cgpa", "backlogs", "internships", "skills_count"]),
    ("cat", OneHotEncoder(handle_unknown="ignore"), ["branch"])
])

# Full pipeline: preprocessing + logistic regression
model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression())
])

# Train
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

# Save the trained model to disk
joblib.dump(model, "placement_model.pkl")
print("\nModel saved as placement_model.pkl")
