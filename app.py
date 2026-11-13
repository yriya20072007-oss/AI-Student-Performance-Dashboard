# app.py
# Flask web server for the Student Performance Classifier dashboard.
# Serves the Overview, Data Explorer, Insights, Model Performance, and Predict sections.

import os
from flask import Flask, render_template, request, jsonify
import model

app = Flask(__name__)

# Train model once at startup and cache all results
print("Loading dataset and training student performance classifier...")
cached_bundle = model.train_and_cache_model()
print("Model ready and cached.")


@app.context_processor
def inject_global_data():
    # Makes common grade mappings and bundle metadata available in all templates
    return {
        "GRADE_MAPPING": model.GRADE_MAPPING,
        "FEATURE_NAMES": model.FEATURE_NAMES,
    }


@app.route("/")
def overview():
    # Overview page: stat cards, feature count, and class distribution
    bundle = model.get_cached_bundle()
    return render_template(
        "overview.html",
        active_page="overview",
        stats=bundle["overview_stats"],
    )


@app.route("/data")
def data_explorer():
    # Data explorer page: searchable, sortable, paginated table with filters
    bundle = model.get_cached_bundle()
    return render_template(
        "data.html",
        active_page="data",
        records=bundle["explorer_data"],
        total_count=len(bundle["explorer_data"]),
    )


@app.route("/insights")
def insights():
    # Insights page: grade vs absences, grade vs study time, correlation heatmap, feature importance
    bundle = model.get_cached_bundle()
    return render_template(
        "insights.html",
        active_page="insights",
        insights=bundle["insights_charts"],
        feature_importance=bundle["feature_importance"],
        correlation_matrix=bundle["correlation_matrix"],
    )


@app.route("/model")
def model_performance():
    # Model performance page: 7 metrics, confusion matrix, ROC curve, and 10-fold CV
    bundle = model.get_cached_bundle()
    return render_template(
        "model.html",
        active_page="model",
        metrics=bundle["metrics"],
        confusion_matrix=bundle["confusion_matrix"],
        roc_data=bundle["roc_data"],
        cv_summary=bundle["cv_summary"],
        train_size=bundle["train_size"],
        test_size=bundle["test_size"],
    )


@app.route("/predict")
def predict_page():
    # Prediction page: interactive form for student details
    return render_template(
        "predict.html",
        active_page="predict",
    )


@app.route("/api/predict", methods=["POST"])
def api_predict():
    # JSON API endpoint to validate input and return predicted grade class
    try:
        if request.is_json:
            form_data = request.get_json()
        else:
            form_data = request.form.to_dict()

        clean_values, errors = model.validate_input(form_data)
        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        result = model.predict_student(clean_values)
        return jsonify({"success": True, "result": result, "input": clean_values})
    except Exception as e:
        return jsonify({"success": False, "errors": {"general": str(e)}}), 500


@app.route("/api/data", methods=["GET"])
def api_data():
    # API endpoint to fetch filtered and paginated records for the Data Explorer
    bundle = model.get_cached_bundle()
    records = bundle["explorer_data"]

    # Filter by gender
    gender_filter = request.args.get("gender")
    if gender_filter is not None and gender_filter != "":
        try:
            g_val = int(gender_filter)
            records = [r for r in records if r["Gender"] == g_val]
        except ValueError:
            pass

    # Filter by tutoring
    tutoring_filter = request.args.get("tutoring")
    if tutoring_filter is not None and tutoring_filter != "":
        try:
            t_val = int(tutoring_filter)
            records = [r for r in records if r["Tutoring"] == t_val]
        except ValueError:
            pass

    # Filter by parental support
    support_filter = request.args.get("parental_support")
    if support_filter is not None and support_filter != "":
        try:
            s_val = int(support_filter)
            records = [r for r in records if r["ParentalSupport"] == s_val]
        except ValueError:
            pass

    # Free text search across all columns
    search = request.args.get("search", "").strip().lower()
    if search:
        records = [
            r for r in records
            if any(search in str(v).lower() for v in r.values())
        ]

    total_filtered = len(records)

    # Sorting
    sort_by = request.args.get("sort_by", "StudentID")
    sort_dir = request.args.get("sort_dir", "asc")
    if records and sort_by in records[0]:
        reverse = (sort_dir.lower() == "desc")
        records.sort(key=lambda x: x[sort_by], reverse=reverse)

    # Pagination
    try:
        page = max(1, int(request.args.get("page", 1)))
        page_size = max(5, min(100, int(request.args.get("page_size", 25))))
    except ValueError:
        page = 1
        page_size = 25

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_records = records[start_idx:end_idx]

    return jsonify({
        "total": total_filtered,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total_filtered + page_size - 1) // page_size),
        "data": page_records,
    })


if __name__ == "__main__":
    # Run development server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
