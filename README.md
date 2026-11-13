# Student Performance Classifier

A machine learning web dashboard for predicting and analyzing student academic grade classifications based on demographic, behavioral, and academic engagement data.

Built with Python (Flask) and HTML/CSS/JavaScript with Chart.js.

---

## Project Overview

- **Dataset:** 2,392 student records (`Student_performance_data.csv`).
- **Target:** `GradeClass` (5 classes):
  - **Class 0:** Grade A (GPA $\ge 3.5$)
  - **Class 1:** Grade B ($3.0 \le \text{GPA} < 3.5$)
  - **Class 2:** Grade C ($2.5 \le \text{GPA} < 3.0$)
  - **Class 3:** Grade D ($2.0 \le \text{GPA} < 2.5$)
  - **Class 4:** Grade F ($\text{GPA} < 2.0$)
- **Feature Isolation:** `StudentID` (arbitrary identifier) and `GPA` (direct derivation of `GradeClass`) are dropped to eliminate data leakage.
- **Predictor Attributes (12):** Age, Gender, Ethnicity, ParentalEducation, StudyTimeWeekly, Absences, Tutoring, ParentalSupport, Extracurricular, Sports, Music, Volunteering.

---

## Machine Learning Pipeline

1. **Stratified Split:** 80% training (1,913 records) and 20% testing (479 records) with `random_state=42`, stratified on `GradeClass`.
2. **Feature Scaling:** `StandardScaler` fitted strictly on training data and applied to testing data and live user inputs.
3. **Cross-Validation:** 10-fold `StratifiedKFold` cross-validation on the training set.
4. **Classifier:** `DecisionTreeClassifier(random_state=42)`.
5. **Startup Caching:** The model and metrics are computed once at application boot and cached in memory.
6. **7 Key Evaluation Metrics:**
   - Accuracy
   - Cohen's Kappa
   - Macro Precision
   - Macro Recall
   - Macro F1 Score
   - Multiclass One-vs-Rest ROC-AUC
   - Matthews Correlation Coefficient (MCC)

---

## Dashboard Sections

1. **Overview:** Total student count, evaluated feature inventory, stat cards (Average GPA, Average Study Time, Average Absences), and target class distribution bar chart.
2. **Data Explorer:** Searchable, sortable, paginated table of student records with filtering by Gender, Tutoring, and Parental Support.
3. **Insights:** Visualizations showing GradeClass vs. Absences, GradeClass vs. Study Time, Pearson correlation matrix heatmap, and Decision Tree Gini feature importance.
4. **Model Performance:** Cards for all 7 metrics, confusion matrix heatmap (5x5), multiclass OvR ROC curves with AUC per class, and cross-validation score per fold.
5. **Predict:** Interactive form to input all 12 student attributes with quick sample presets, robust error handling, predicted grade letter, confidence score, and per-class probability bars.

---

## Design System

- **Primary Colors:**
  - Sidebar: Deep Navy (`#0B1F3A`)
  - Accent: Medium Blue (`#1F5FBF`)
  - Background: Light Blue-Grey (`#EEF3FA`)
  - Cards: White (`#FFFFFF`) with 1px border (`#D5DFEC`) and 6px radius
- **Typography:**
  - Headings: `IBM Plex Sans`
  - Body: `Inter`
  - Data / Monospace: `IBM Plex Mono`
- **Styling:** Hand-built analytics interface without gradients, glassmorphism, neon glows, or emojis.

---

## Directory Structure

```text
studentperformancedashboard/
├── app.py                      # Flask routes and API endpoints
├── model.py                    # ML pipeline, model training, caching & validation
├── Student_performance_data.csv# Dataset (2,392 records)
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation and run steps
├── templates/
│   ├── base.html               # Base layout with responsive sidebar
│   ├── overview.html           # Overview stat cards and distribution
│   ├── data.html               # Data explorer with table & filters
│   ├── insights.html           # Insights and correlation heatmap
│   ├── model.html              # 7 metrics, confusion matrix, ROC curve
│   └── predict.html            # Prediction input form & results
└── static/
    ├── css/
    │   └── style.css           # Custom styling
    └── js/
        ├── chart.umd.min.js    # Chart.js library (bundled locally)
        ├── main.js             # Mobile navigation drawer toggle
        ├── data_table.js       # Data explorer table search/sort/filter
        └── predict.js          # Prediction form handler & probability bars
```

---

## Installation & Running

### 1. Prerequisites
- Python 3.10+ (or virtual environment).

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

Open your browser and navigate to:
```
http://localhost:5000
```
