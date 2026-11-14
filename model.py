# model.py
# Machine learning pipeline for student performance classification.
# Follows the notebook methodology: train-test split, standard scaling, decision tree classifier,
# stratified 10-fold cross validation, and multiclass performance metrics.

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, label_binarize
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    matthews_corrcoef,
    confusion_matrix,
    roc_curve,
)

# Grade labels corresponding to GradeClass 0 to 4
GRADE_MAPPING = {
    0: {"letter": "A", "label": "Grade A (Class 0)", "desc": "Excellent"},
    1: {"letter": "B", "label": "Grade B (Class 1)", "desc": "Good"},
    2: {"letter": "C", "label": "Grade C (Class 2)", "desc": "Satisfactory"},
    3: {"letter": "D", "label": "Grade D (Class 3)", "desc": "Needs Improvement"},
    4: {"letter": "F", "label": "Grade F (Class 4)", "desc": "Fail"},
}

# The 12 feature columns used for prediction
FEATURE_NAMES = [
    "Age",
    "Gender",
    "Ethnicity",
    "ParentalEducation",
    "StudyTimeWeekly",
    "Absences",
    "Tutoring",
    "ParentalSupport",
    "Extracurricular",
    "Sports",
    "Music",
    "Volunteering",
]

# Validation rules for student input
FEATURE_CONSTRAINTS = {
    "Age": {"type": int, "min": 15, "max": 18, "label": "Age"},
    "Gender": {"type": int, "min": 0, "max": 1, "label": "Gender (0: Female, 1: Male)"},
    "Ethnicity": {"type": int, "min": 0, "max": 3, "label": "Ethnicity"},
    "ParentalEducation": {"type": int, "min": 0, "max": 4, "label": "Parental Education"},
    "StudyTimeWeekly": {"type": float, "min": 0.0, "max": 20.0, "label": "Weekly Study Time"},
    "Absences": {"type": int, "min": 0, "max": 30, "label": "Absences"},
    "Tutoring": {"type": int, "min": 0, "max": 1, "label": "Tutoring"},
    "ParentalSupport": {"type": int, "min": 0, "max": 4, "label": "Parental Support"},
    "Extracurricular": {"type": int, "min": 0, "max": 1, "label": "Extracurricular Activities"},
    "Sports": {"type": int, "min": 0, "max": 1, "label": "Sports"},
    "Music": {"type": int, "min": 0, "max": 1, "label": "Music"},
    "Volunteering": {"type": int, "min": 0, "max": 1, "label": "Volunteering"},
}

# Global cache for trained model and precomputed analytics
_model_cache = None


def find_dataset_path():
    # Helper to find dataset file in common locations
    candidates = [
        "Student_performance_data.csv",
        "Student_performance_data _ (1).csv",
        os.path.join(os.path.dirname(__file__), "Student_performance_data.csv"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Could not find Student_performance_data.csv")


def train_and_cache_model():
    # Trains the model once at startup and caches all metrics and chart data.
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    csv_path = find_dataset_path()
    df = pd.read_csv(csv_path)

    # Ensure clean data types
    df["GradeClass"] = df["GradeClass"].astype(int)

    # Features and target: drop StudentID and GPA as required
    X = df[FEATURE_NAMES]
    y = df["GradeClass"]

    # 80/20 stratified split like notebook
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Fit scaler on training set only
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 10-fold Stratified K-Fold cross validation
    cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    cv_model = DecisionTreeClassifier(random_state=42)
    cv_scores = cross_val_score(cv_model, X_train_scaled, y_train, cv=cv, scoring="accuracy")

    # Train final decision tree model
    clf = DecisionTreeClassifier(random_state=42)
    clf.fit(X_train_scaled, y_train)

    # Predictions on test set
    y_pred = clf.predict(X_test_scaled)
    y_prob_all = clf.predict_proba(X_test_scaled)

    # Calculate 7 evaluation metrics
    acc = float(accuracy_score(y_test, y_pred))
    kappa = float(cohen_kappa_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, average="macro"))
    rec = float(recall_score(y_test, y_pred, average="macro"))
    f1 = float(f1_score(y_test, y_pred, average="macro"))
    auc = float(roc_auc_score(y_test, y_prob_all, multi_class="ovr", average="macro"))
    mcc = float(matthews_corrcoef(y_test, y_pred))

    metrics = {
        "accuracy": acc,
        "kappa": kappa,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": auc,
        "mcc": mcc,
    }

    # Confusion matrix (5x5)
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2, 3, 4])
    cm_list = cm.tolist()

    # Multiclass One-vs-Rest ROC curve data
    y_test_bin = label_binarize(y_test, classes=[0, 1, 2, 3, 4])
    roc_data = {}
    for i in range(5):
        fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_prob_all[:, i])
        class_auc = float(roc_auc_score(y_test_bin[:, i], y_prob_all[:, i]))
        # Reduce points smoothly for web chart rendering
        step = max(1, len(fpr) // 30)
        roc_data[str(i)] = {
            "label": f"Class {i} ({GRADE_MAPPING[i]['letter']})",
            "auc": round(class_auc, 4),
            "points": [{"x": round(float(f), 4), "y": round(float(t), 4)} for f, t in zip(fpr[::step], tpr[::step])]
        }
        # Ensure (1, 1) end point is always present
        if roc_data[str(i)]["points"][-1]["x"] != 1.0:
            roc_data[str(i)]["points"].append({"x": 1.0, "y": 1.0})

    # Feature importances
    feature_importance = [
        {"feature": name, "importance": round(float(imp), 4)}
        for name, imp in sorted(zip(FEATURE_NAMES, clf.feature_importances_), key=lambda x: x[1], reverse=True)
    ]

    # Cross validation fold data
    cv_fold_scores = [round(float(s), 4) for s in cv_scores]
    cv_summary = {
        "folds": cv_fold_scores,
        "mean": round(float(cv_scores.mean()), 4),
        "std": round(float(cv_scores.std()), 4),
    }

    # Overview statistics
    class_counts = df["GradeClass"].value_counts().sort_index().to_dict()
    total_students = int(len(df))
    class_distribution = [
        {
            "class_id": i,
            "grade": GRADE_MAPPING[i]["letter"],
            "count": int(class_counts.get(i, 0)),
            "percentage": round((class_counts.get(i, 0) / total_students) * 100, 1),
        }
        for i in range(5)
    ]

    overview_stats = {
        "total_students": total_students,
        "num_features": len(FEATURE_NAMES),
        "avg_gpa": round(float(df["GPA"].mean()), 2),
        "avg_study_time": round(float(df["StudyTimeWeekly"].mean()), 2),
        "avg_absences": round(float(df["Absences"].mean()), 2),
        "class_distribution": class_distribution,
    }

    # Insights: Absences and Study Time vs GradeClass
    absences_by_grade = (
        df.groupby("GradeClass")["Absences"].mean().sort_index().round(2).to_dict()
    )
    study_by_grade = (
        df.groupby("GradeClass")["StudyTimeWeekly"].mean().sort_index().round(2).to_dict()
    )

    insights_charts = {
        "grade_vs_absences": [
            {"grade": f"Class {i} ({GRADE_MAPPING[i]['letter']})", "mean": absences_by_grade.get(i, 0.0)}
            for i in range(5)
        ],
        "grade_vs_study_time": [
            {"grade": f"Class {i} ({GRADE_MAPPING[i]['letter']})", "mean": study_by_grade.get(i, 0.0)}
            for i in range(5)
        ],
    }

    # Correlation matrix for numerical features
    corr_cols = [
        "Age",
        "StudyTimeWeekly",
        "Absences",
        "Tutoring",
        "ParentalSupport",
        "Extracurricular",
        "Sports",
        "Music",
        "Volunteering",
        "GPA",
        "GradeClass",
    ]
    corr_df = df[corr_cols].corr().round(3)
    correlation_matrix = {
        "columns": corr_cols,
        "matrix": corr_df.values.tolist(),
    }

    # Data explorer records
    explorer_data = df.to_dict(orient="records")

    _model_cache = {
        "model": clf,
        "scaler": scaler,
        "metrics": metrics,
        "confusion_matrix": cm_list,
        "roc_data": roc_data,
        "feature_importance": feature_importance,
        "cv_summary": cv_summary,
        "overview_stats": overview_stats,
        "insights_charts": insights_charts,
        "correlation_matrix": correlation_matrix,
        "explorer_data": explorer_data,
        "test_size": len(y_test),
        "train_size": len(y_train),
    }

    return _model_cache


def get_cached_bundle():
    # Helper to access cached model bundle
    if _model_cache is None:
        return train_and_cache_model()
    return _model_cache


def validate_input(form_data):
    # Validates input form fields, checks types, missing values, and ranges.
    clean_values = {}
    errors = {}

    for feature, rules in FEATURE_CONSTRAINTS.items():
        val = form_data.get(feature)
        if val is None or str(val).strip() == "":
            errors[feature] = f"{rules['label']} is required."
            continue

        try:
            if rules["type"] == int:
                # Handle cases like "1.0" or "1"
                num_val = int(round(float(val)))
            else:
                num_val = float(val)

            if num_val < rules["min"] or num_val > rules["max"]:
                errors[feature] = f"{rules['label']} must be between {rules['min']} and {rules['max']}."
            else:
                clean_values[feature] = num_val
        except (ValueError, TypeError):
            errors[feature] = f"{rules['label']} must be a valid number."

    return clean_values, errors


def predict_student(student_dict):
    # Predicts GradeClass for a single student dictionary of 12 features.
    bundle = get_cached_bundle()
    model = bundle["model"]
    scaler = bundle["scaler"]

    # Build DataFrame with feature names to match StandardScaler
    row_df = pd.DataFrame([[student_dict[col] for col in FEATURE_NAMES]], columns=FEATURE_NAMES)
    row_scaled = scaler.transform(row_df)

    pred_class = int(model.predict(row_scaled)[0])
    probs = model.predict_proba(row_scaled)[0]

    prob_breakdown = [
        {
            "class_id": i,
            "grade": GRADE_MAPPING[i]["letter"],
            "label": GRADE_MAPPING[i]["label"],
            "probability": round(float(probs[i]) * 100, 1),
            "is_predicted": (i == pred_class),
        }
        for i in range(5)
    ]

    confidence = round(float(probs[pred_class]) * 100, 1)

    return {
        "predicted_class": pred_class,
        "grade_letter": GRADE_MAPPING[pred_class]["letter"],
        "grade_label": GRADE_MAPPING[pred_class]["label"],
        "description": GRADE_MAPPING[pred_class]["desc"],
        "confidence": confidence,
        "probabilities": prob_breakdown,
    }
