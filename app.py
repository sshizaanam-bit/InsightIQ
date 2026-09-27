from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
import re
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


app = Flask(__name__)


# ==================================================
# CONFIGURATION
# ==================================================

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==================================================
# GLOBAL DATAFRAME
# ==================================================

df = None


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def clean_number(value):
    """Format numbers nicely for answers."""

    try:

        value = float(value)

        if value.is_integer():
            return f"{int(value):,}"

        return f"{value:,.2f}"

    except Exception:

        return str(value)


def find_matching_numeric_column(
    question,
    numeric_columns
):
    """
    Find a numerical column mentioned
    in the user's question.
    """

    question_lower = question.lower()

    # Exact column-name matching
    for column in numeric_columns:

        if str(column).lower() in question_lower:

            return column


    # Word-based matching
    for column in numeric_columns:

        words = re.findall(
            r"\b[a-zA-Z0-9]+\b",
            str(column).lower()
        )

        if any(
            word in question_lower
            for word in words
        ):

            return column


    return None


def find_matching_column(
    question,
    columns
):
    """
    Find any dataset column mentioned
    in the question.
    """

    question_lower = question.lower()


    # Exact column name
    for column in columns:

        if str(column).lower() in question_lower:

            return column


    # Partial word matching
    for column in columns:

        column_words = re.findall(
            r"\b[a-zA-Z0-9]+\b",
            str(column).lower()
        )

        for word in column_words:

            if (
                len(word) >= 3
                and word in question_lower
            ):

                return column


    return None


def get_numeric_columns():

    """Return numerical columns."""

    return df.select_dtypes(
        include="number"
    ).columns.tolist()


def get_categorical_columns():

    """Return categorical columns."""

    return df.select_dtypes(
        exclude="number"
    ).columns.tolist()


def detect_business_column(
    question,
    numeric_columns
):
    """
    Detect common business metrics such as
    sales, revenue, profit, income, cost,
    price, quantity, etc.
    """

    question_lower = question.lower()

    business_keywords = {

        "sales": [
            "sales",
            "sale"
        ],

        "revenue": [
            "revenue",
            "income"
        ],

        "profit": [
            "profit",
            "earnings"
        ],

        "cost": [
            "cost",
            "expense",
            "expenses"
        ],

        "price": [
            "price",
            "amount"
        ],

        "quantity": [
            "quantity",
            "qty",
            "units"
        ]

    }


    for metric, keywords in business_keywords.items():

        if any(
            word in question_lower
            for word in keywords
        ):

            for column in numeric_columns:

                column_lower = str(
                    column
                ).lower()

                if any(
                    word in column_lower
                    for word in keywords
                ):

                    return column


    return None


def answer_groupby_question(question):

    """
    Handle questions such as:

    Which product has the highest sales?
    Which category has the lowest revenue?
    Show top 5 products by sales.
    """

    numeric_columns = get_numeric_columns()

    categorical_columns = get_categorical_columns()


    if (
        not numeric_columns
        or not categorical_columns
    ):

        return None


    question_lower = question.lower()


    # Find numerical metric
    numeric_column = find_matching_numeric_column(
        question,
        numeric_columns
    )


    if numeric_column is None:

        numeric_column = detect_business_column(
            question,
            numeric_columns
        )


    if numeric_column is None:

        return None


    # Find categorical column
    category_column = find_matching_column(
        question,
        categorical_columns
    )


    # Common category names
    if category_column is None:

        common_category_words = [

            "product",
            "category",
            "customer",
            "region",
            "city",
            "country",
            "department",
            "employee",
            "segment",
            "brand"

        ]


        for column in categorical_columns:

            column_lower = str(
                column
            ).lower()

            if any(
                word in column_lower
                for word in common_category_words
            ):

                category_column = column

                break


    if category_column is None:

        return None


    # Group data
    grouped = (

        df.groupby(category_column)[numeric_column]

        .sum()

        .sort_values(
            ascending=False
        )

    )


    grouped = grouped.dropna()


    if grouped.empty:

        return None


    # TOP / HIGHEST
    if (
        "highest" in question_lower
        or "top" in question_lower
        or "best" in question_lower
        or "largest" in question_lower
        or "maximum" in question_lower
    ):

        top_match = re.search(
            r"top\s+(\d+)",
            question_lower
        )


        limit = 5


        if top_match:

            limit = int(
                top_match.group(1)
            )


        results = grouped.head(limit)


        if limit == 1:

            category = results.index[0]

            value = results.iloc[0]


            return (

                f"{category_column} '{category}' "
                f"has the highest total "
                f"{numeric_column}, with "
                f"{clean_number(value)}."

            )


        result_text = []


        for index, value in results.items():

            result_text.append(

                f"{index}: "
                f"{clean_number(value)}"

            )


        return (

            f"Top {limit} "
            f"{category_column} values by "
            f"{numeric_column}: "

            + "; ".join(result_text)

            + "."

        )


    # LOWEST / BOTTOM
    if (
        "lowest" in question_lower
        or "bottom" in question_lower
        or "worst" in question_lower
        or "smallest" in question_lower
        or "minimum" in question_lower
    ):

        bottom_match = re.search(
            r"bottom\s+(\d+)",
            question_lower
        )


        limit = 5


        if bottom_match:

            limit = int(
                bottom_match.group(1)
            )


        results = (
            grouped
            .sort_values()
            .head(limit)
        )


        if limit == 1:

            category = results.index[0]

            value = results.iloc[0]


            return (

                f"{category_column} '{category}' "
                f"has the lowest total "
                f"{numeric_column}, with "
                f"{clean_number(value)}."

            )


        result_text = []


        for index, value in results.items():

            result_text.append(

                f"{index}: "
                f"{clean_number(value)}"

            )


        return (

            f"Bottom {limit} "
            f"{category_column} values by "
            f"{numeric_column}: "

            + "; ".join(result_text)

            + "."

        )


    return None


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        title="Home"
    )


# ==================================================
# UPLOAD
# ==================================================

@app.route(
    "/upload",
    methods=["GET", "POST"]
)
def upload():

    global df


    if request.method == "POST":

        file = request.files.get(
            "dataset"
        )


        if (
            file is None
            or file.filename == ""
        ):

            return render_template(
                "upload.html",
                title="Upload",
                error=(
                    "Please select a "
                    "CSV or Excel file."
                )
            )


        filename = file.filename


        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )


        file.save(filepath)


        try:

            if filename.lower().endswith(
                ".csv"
            ):

                df = pd.read_csv(
                    filepath
                )


            elif filename.lower().endswith(
                (".xlsx", ".xls")
            ):

                df = pd.read_excel(
                    filepath
                )


            else:

                return render_template(
                    "upload.html",
                    title="Upload",
                    error=(
                        "Unsupported "
                        "file format."
                    )
                )


        except Exception as e:

            return render_template(
                "upload.html",
                title="Upload",
                error=(
                    f"Error reading file: {e}"
                )
            )


        rows = df.shape[0]

        columns = df.shape[1]


        preview = df.head(10).to_html(

            classes=(
                "table table-dark "
                "table-hover "
                "table-bordered"
            ),

            index=False

        )


        return render_template(

            "upload.html",

            title="Upload",

            success=True,

            filename=filename,

            rows=rows,

            columns=columns,

            filetype=(
                filename
                .split(".")[-1]
                .upper()
            ),

            preview=preview

        )


    return render_template(

        "upload.html",

        title="Upload"

    )


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/dashboard")
def dashboard():

    global df


    if df is None:

        return render_template(

            "dashboard.html",

            title="Dashboard",

            nodata=True

        )


    # ----------------------------------------------
    # Basic information
    # ----------------------------------------------

    rows = df.shape[0]

    columns = df.shape[1]


    missing_values = int(

        df.isnull()
        .sum()
        .sum()

    )


    duplicate_rows = int(

        df.duplicated()
        .sum()

    )


    # ----------------------------------------------
    # Numerical columns
    # ----------------------------------------------

    numeric_columns = (

        df.select_dtypes(
            include="number"
        )
        .columns
        .tolist()

    )


    # ----------------------------------------------
    # Categorical columns
    # ----------------------------------------------

    categorical_columns = (

        df.select_dtypes(
            exclude="number"
        )
        .columns
        .tolist()

    )


    # ----------------------------------------------
    # Numerical summary
    # ----------------------------------------------

    numeric_data = []


    for column in numeric_columns:

        series = df[column].dropna()


        if len(series) == 0:

            continue


        numeric_data.append({

            "name": column,

            "average": round(
                float(series.mean()),
                2
            ),

            "minimum": round(
                float(series.min()),
                2
            ),

            "maximum": round(
                float(series.max()),
                2
            ),

            "total": round(
                float(series.sum()),
                2
            )

        })
            # ----------------------------------------------
    # SMART BUSINESS METRICS
    # ----------------------------------------------

    smart_metrics = []

    if numeric_data:

        # Highest average numerical column
        highest_average = max(
            numeric_data,
            key=lambda x: x["average"]
        )

        # Highest total numerical column
        highest_total = max(
            numeric_data,
            key=lambda x: x["total"]
        )

        # Highest maximum value
        highest_value = max(
            numeric_data,
            key=lambda x: x["maximum"]
        )

        # Lowest minimum value
        lowest_value = min(
            numeric_data,
            key=lambda x: x["minimum"]
        )

        smart_metrics = [
            {
                "title": "Highest Average",
                "value": highest_average["average"],
                "column": highest_average["name"],
                "icon": "bi-graph-up-arrow"
            },
            {
                "title": "Highest Total",
                "value": highest_total["total"],
                "column": highest_total["name"],
                "icon": "bi-bar-chart-line-fill"
            },
            {
                "title": "Highest Value",
                "value": highest_value["maximum"],
                "column": highest_value["name"],
                "icon": "bi-trophy-fill"
            },
            {
                "title": "Lowest Value",
                "value": lowest_value["minimum"],
                "column": lowest_value["name"],
                "icon": "bi-graph-down-arrow"
            }
        ]


    # ----------------------------------------------
    # Numerical chart
    # ----------------------------------------------

    numeric_chart_labels = []

    numeric_chart_values = []


    for item in numeric_data:

        numeric_chart_labels.append(
            item["name"]
        )

        numeric_chart_values.append(
            item["average"]
        )


    # ----------------------------------------------
    # Category chart
    # ----------------------------------------------

    category_column = None

    category_labels = []

    category_values = []


    if categorical_columns:

        category_column = (
            categorical_columns[0]
        )


        counts = (

            df[category_column]

            .dropna()

            .astype(str)

            .value_counts()

            .head(10)

        )


        category_labels = (
            counts.index.tolist()
        )

        category_values = (
            counts.values.tolist()
        )


    # ----------------------------------------------
    # Automatic Insights
    # ----------------------------------------------

    insights = []


    if rows > 0:

        insights.append(

            f"Your dataset contains "
            f"{rows:,} records across "
            f"{columns} columns."

        )


    if missing_values == 0:

        insights.append(

            "No missing values were "
            "detected in the uploaded "
            "dataset."

        )

    else:

        insights.append(

            f"The dataset contains "
            f"{missing_values:,} "
            f"missing values."

        )


    if duplicate_rows == 0:

        insights.append(

            "No duplicate rows were "
            "detected."

        )

    else:

        insights.append(

            f"{duplicate_rows:,} "
            f"duplicate rows were "
            f"detected."

        )


    if numeric_data:

        highest_average = max(

            numeric_data,

            key=lambda x: x["average"]

        )


        insights.append(

            f"{highest_average['name']} "
            f"has the highest average "
            f"value among the numerical "
            f"columns."

        )


    if (
        category_column
        and category_labels
    ):

        insights.append(

            f"'{category_labels[0]}' "
            f"is the most frequently "
            f"occurring value in "
            f"{category_column}."

        )


    # ----------------------------------------------
    # Render dashboard
    # ----------------------------------------------

    return render_template(

        "dashboard.html",

        title="Dashboard",

        rows=rows,

        columns=columns,

        missing_values=missing_values,

        duplicate_rows=duplicate_rows,

        numeric_columns=numeric_columns,

        categorical_columns=categorical_columns,

        numeric_data=numeric_data,

        numeric_chart_labels=(
            numeric_chart_labels
        ),

        numeric_chart_values=(
            numeric_chart_values
        ),

        category_column=category_column,

        category_labels=category_labels,

        category_values=category_values,
                smart_metrics=smart_metrics,

        insights=insights,

        nodata=False

    )


# ==================================================
# ASK INSIGHTIQ
# ==================================================

@app.route(
    "/ask",
    methods=["POST"]
)
def ask():

    global df


    # ----------------------------------------------
    # Check dataset
    # ----------------------------------------------

    if df is None:

        return jsonify({

            "answer":
                "Please upload a "
                "dataset first."

        })


    # ----------------------------------------------
    # Get question
    # ----------------------------------------------

    question = request.form.get(

        "question",

        ""

    ).strip().lower()


    if not question:

        return jsonify({

            "answer":
                "Please enter a question."

        })


    numeric_columns = (
        get_numeric_columns()
    )


    categorical_columns = (
        get_categorical_columns()
    )


    # ==================================================
    # DATASET SIZE
    # ==================================================

    if (

        "how many rows" in question

        or "number of rows" in question

        or "total records" in question

        or "how many records" in question

        or "how many entries" in question

    ):

        return jsonify({

            "answer":

                f"Your dataset contains "
                f"{len(df):,} records."

        })


    # ==================================================
    # NUMBER OF COLUMNS
    # ==================================================

    if (

        "how many columns" in question

        or "number of columns" in question

    ):

        return jsonify({

            "answer":

                f"Your dataset contains "
                f"{len(df.columns):,} "
                f"columns."

        })


    # ==================================================
    # COLUMN NAMES
    # ==================================================

    if (

        "columns" in question

        and (

            "what" in question

            or "which" in question

            or "list" in question

            or "name" in question

        )

    ):

        column_list = ", ".join(

            df.columns
            .astype(str)
            .tolist()

        )


        return jsonify({

            "answer":

                f"The columns in your "
                f"dataset are: "
                f"{column_list}."

        })


    # ==================================================
    # MISSING VALUES
    # ==================================================

    if (

        "missing" in question

        or "null" in question

        or "empty values" in question

    ):

        missing = int(

            df.isnull()
            .sum()
            .sum()

        )


        if missing == 0:

            answer = (

                "There are no missing "
                "values in your dataset."

            )

        else:

            answer = (

                f"Your dataset contains "
                f"{missing:,} missing "
                f"values."

            )


        return jsonify({

            "answer": answer

        })


    # ==================================================
    # DUPLICATES
    # ==================================================

    if (

        "duplicate" in question

        or "duplicates" in question

    ):

        duplicates = int(

            df.duplicated()
            .sum()

        )


        return jsonify({

            "answer":

                f"Your dataset contains "
                f"{duplicates:,} "
                f"duplicate rows."

        })


    # ==================================================
    # UNIQUE VALUES
    # ==================================================

    if (

        "unique" in question

        or "distinct" in question

    ):

        column = find_matching_column(

            question,

            df.columns.tolist()

        )


        if column:

            unique_count = (
                df[column]
                .nunique(
                    dropna=True
                )
            )


            return jsonify({

                "answer":

                    f"{column} contains "
                    f"{unique_count:,} "
                    f"unique values."

            })


        return jsonify({

            "answer":

                "Please mention the "
                "column name you want "
                "to check for unique "
                "values."

        })


    # ==================================================
    # GROUP-BY BUSINESS QUESTIONS
    # ==================================================

    group_answer = (
        answer_groupby_question(
            question
        )
    )


    if group_answer:

        return jsonify({

            "answer": group_answer

        })


    # ==================================================
    # AVERAGE / MEAN
    # ==================================================

    if (

        "average" in question

        or "mean" in question

    ):

        column = (
            find_matching_numeric_column(
                question,
                numeric_columns
            )
        )


        if column:

            value = (
                df[column]
                .dropna()
                .mean()
            )


            return jsonify({

                "answer":

                    f"The average value "
                    f"of {column} is "
                    f"{clean_number(value)}."

            })


        if numeric_columns:

            averages = {}


            for column in numeric_columns:

                averages[column] = (

                    df[column]
                    .dropna()
                    .mean()

                )


            best_column = max(

                averages,

                key=averages.get

            )


            return jsonify({

                "answer":

                    f"The highest average "
                    f"among the numerical "
                    f"columns is "
                    f"{best_column}, "
                    f"with an average value "
                    f"of "
                    f"{clean_number(averages[best_column])}."

            })


        return jsonify({

            "answer":

                "There are no numerical "
                "columns available for "
                "average calculations."

        })


    # ==================================================
    # MEDIAN
    # ==================================================

    if "median" in question:

        column = (
            find_matching_numeric_column(
                question,
                numeric_columns
            )
        )


        if column:

            value = (
                df[column]
                .dropna()
                .median()
            )


            return jsonify({

                "answer":

                    f"The median value "
                    f"of {column} is "
                    f"{clean_number(value)}."

            })


        if numeric_columns:

            column = (
                numeric_columns[0]
            )


            value = (
                df[column]
                .dropna()
                .median()
            )


            return jsonify({

                "answer":

                    f"The median value "
                    f"of {column} is "
                    f"{clean_number(value)}."

            })


    # ==================================================
    # HIGHEST / MAXIMUM
    # ==================================================

    if (

        "highest" in question

        or "maximum" in question

        or "max" in question

        or "largest" in question

    ):

        column = (
            find_matching_numeric_column(
                question,
                numeric_columns
            )
        )


        if column:

            value = df[column].max()


            return jsonify({

                "answer":

                    f"The highest value "
                    f"in {column} is "
                    f"{clean_number(value)}."

            })


        if numeric_columns:

            results = {}


            for column in numeric_columns:

                results[column] = (
                    df[column].max()
                )


            best_column = max(

                results,

                key=results.get

            )


            return jsonify({

                "answer":

                    f"The highest value "
                    f"among your numerical "
                    f"columns is "
                    f"{clean_number(results[best_column])}, "
                    f"found in {best_column}."

            })


    # ==================================================
    # LOWEST / MINIMUM
    # ==================================================

    if (

        "lowest" in question

        or "minimum" in question

        or "min" in question

        or "smallest" in question

    ):

        column = (
            find_matching_numeric_column(
                question,
                numeric_columns
            )
        )


        if column:

            value = df[column].min()


            return jsonify({

                "answer":

                    f"The lowest value "
                    f"in {column} is "
                    f"{clean_number(value)}."

            })


        if numeric_columns:

            results = {}


            for column in numeric_columns:

                results[column] = (
                    df[column].min()
                )


            lowest_column = min(

                results,

                key=results.get

            )


            return jsonify({

                "answer":

                    f"The lowest value "
                    f"among your numerical "
                    f"columns is "
                    f"{clean_number(results[lowest_column])}, "
                    f"found in {lowest_column}."

            })


    # ==================================================
    # TOTAL / SUM
    # ==================================================

    if (

        "total" in question

        or "sum" in question

        or "overall" in question

    ):

        column = (
            find_matching_numeric_column(
                question,
                numeric_columns
            )
        )


        if column:

            value = df[column].sum()


            return jsonify({

                "answer":

                    f"The total of "
                    f"{column} is "
                    f"{clean_number(value)}."

            })


        business_column = (
            detect_business_column(
                question,
                numeric_columns
            )
        )


        if business_column:

            value = (
                df[business_column]
                .sum()
            )


            return jsonify({

                "answer":

                    f"The total "
                    f"{business_column} "
                    f"is "
                    f"{clean_number(value)}."

            })


        if numeric_columns:

            column = (
                numeric_columns[0]
            )


            value = df[column].sum()


            return jsonify({

                "answer":

                    f"The total of "
                    f"{column} is "
                    f"{clean_number(value)}."

            })


    # ==================================================
    # MOST FREQUENT CATEGORY
    # ==================================================

    if (

        "most frequent" in question

        or "most common" in question

        or "occurs most" in question

        or "appears most" in question

    ):

        column = find_matching_column(

            question,

            categorical_columns

        )


        if (
            column is None
            and categorical_columns
        ):

            column = (
                categorical_columns[0]
            )


        if column:

            counts = (

                df[column]

                .dropna()

                .astype(str)

                .value_counts()

            )


            if not counts.empty:

                value = counts.index[0]

                count = counts.iloc[0]


                return jsonify({

                    "answer":

                        f"'{value}' is "
                        f"the most frequently "
                        f"occurring value in "
                        f"{column}, appearing "
                        f"{count:,} times."

                })


    # ==================================================
    # TOP 5 NUMERICAL VALUES
    # ==================================================

    if (

        "top 5" in question

        or "top five" in question

        or "highest 5" in question

    ):

        column = (
            find_matching_numeric_column(
                question,
                numeric_columns
            )
        )


        if (
            column is None
            and numeric_columns
        ):

            column = (
                numeric_columns[0]
            )


        if column:

            values = (

                df[column]

                .dropna()

                .sort_values(
                    ascending=False
                )

                .head(5)

                .tolist()

            )


            formatted = ", ".join(

                clean_number(value)

                for value in values

            )


            return jsonify({

                "answer":

                    f"The top 5 values "
                    f"in {column} are: "
                    f"{formatted}."

            })


    # ==================================================
    # BOTTOM 5 NUMERICAL VALUES
    # ==================================================

    if (

        "bottom 5" in question

        or "bottom five" in question

        or "lowest 5" in question

    ):

        column = (
            find_matching_numeric_column(
                question,
                numeric_columns
            )
        )


        if (
            column is None
            and numeric_columns
        ):

            column = (
                numeric_columns[0]
            )


        if column:

            values = (

                df[column]

                .dropna()

                .sort_values()

                .head(5)

                .tolist()

            )


            formatted = ", ".join(

                clean_number(value)

                for value in values

            )


            return jsonify({

                "answer":

                    f"The bottom 5 values "
                    f"in {column} are: "
                    f"{formatted}."

            })


    # ==================================================
    # DATASET SHAPE
    # ==================================================

    if (

        "shape" in question

        or "size of dataset" in question

    ):

        return jsonify({

            "answer":

                f"Your dataset has "
                f"{len(df):,} rows and "
                f"{len(df.columns):,} "
                f"columns."

        })


    # ==================================================
    # FALLBACK
    # ==================================================

    return jsonify({

        "answer":

            "I couldn't understand "
            "that question yet. Try "
            "asking about rows, "
            "columns, missing values, "
            "duplicates, averages, "
            "median, highest values, "
            "lowest values, totals, "
            "unique values, top 5 "
            "values, bottom 5 values, "
            "or category performance."

    })


# ==================================================
# ==================================================
# REPORTS
# ==================================================

@app.route("/reports")
def reports():

    global df

    # ----------------------------------------------
    # No dataset uploaded
    # ----------------------------------------------

    if df is None:

        return render_template(
            "report.html",
            title="Reports",
            nodata=True
        )

    # ----------------------------------------------
    # Basic dataset information
    # ----------------------------------------------

    rows = df.shape[0]

    columns = df.shape[1]

    missing_values = int(
        df.isnull().sum().sum()
    )

    duplicate_rows = int(
        df.duplicated().sum()
    )

    # ----------------------------------------------
    # Numerical columns
    # ----------------------------------------------

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    # ----------------------------------------------
    # Categorical columns
    # ----------------------------------------------

    categorical_columns = df.select_dtypes(
        exclude="number"
    ).columns.tolist()

    # ----------------------------------------------
    # Numerical analysis
    # ----------------------------------------------

    numeric_data = []

    for column in numeric_columns:

        series = df[column].dropna()

        if len(series) == 0:
            continue

        numeric_data.append({

            "name": str(column),

            "average": round(
                float(series.mean()),
                2
            ),

            "minimum": round(
                float(series.min()),
                2
            ),

            "maximum": round(
                float(series.max()),
                2
            ),

            "total": round(
                float(series.sum()),
                2
            )

        })

    # ----------------------------------------------
    # Automatic insights
    # ----------------------------------------------

    insights = []

    if rows > 0:

        insights.append(
            f"Your dataset contains "
            f"{rows:,} records across "
            f"{columns} columns."
        )

    if missing_values == 0:

        insights.append(
            "No missing values were detected "
            "in the uploaded dataset."
        )

    else:

        insights.append(
            f"The dataset contains "
            f"{missing_values:,} missing values."
        )

    if duplicate_rows == 0:

        insights.append(
            "No duplicate rows were detected."
        )

    else:

        insights.append(
            f"{duplicate_rows:,} duplicate rows "
            f"were detected."
        )

    highest_average = None

    if numeric_data:

        highest_average = max(
            numeric_data,
            key=lambda x: x["average"]
        )

        insights.append(
            f"{highest_average['name']} has the "
            f"highest average value among the "
            f"numerical columns."
        )

    category_column = None
    category_top_value = None
    category_top_count = None

    if categorical_columns:

        category_column = categorical_columns[0]

        counts = (
            df[category_column]
            .dropna()
            .astype(str)
            .value_counts()
        )

        if not counts.empty:

            category_top_value = counts.index[0]

            category_top_count = int(
                counts.iloc[0]
            )

            insights.append(
                f"'{category_top_value}' is the "
                f"most frequently occurring value "
                f"in {category_column}."
            )

    return render_template(

        "report.html",

        title="Reports",

        nodata=False,

        rows=rows,

        columns=columns,

        missing_values=missing_values,

        duplicate_rows=duplicate_rows,

        numeric_columns=numeric_columns,

        categorical_columns=categorical_columns,

        numeric_data=numeric_data,

        insights=insights,

        highest_average=highest_average,

        category_column=category_column,

        category_top_value=category_top_value,

        category_top_count=category_top_count

    )
    # ==================================================
# DOWNLOAD REPORT AS PDF
# ==================================================

@app.route("/download-report")
def download_report():

    global df

    if df is None:
        return "Please upload a dataset first.", 400

    rows = df.shape[0]
    columns = df.shape[1]

    missing_values = int(
        df.isnull().sum().sum()
    )

    duplicate_rows = int(
        df.duplicated().sum()
    )

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    numeric_data = []

    for column in numeric_columns:

        series = df[column].dropna()

        if len(series) == 0:
            continue

        numeric_data.append({
            "name": str(column),
            "average": round(float(series.mean()), 2),
            "minimum": round(float(series.min()), 2),
            "maximum": round(float(series.max()), 2),
            "total": round(float(series.sum()), 2)
        })

    insights = []

    insights.append(
        f"The dataset contains "
        f"{rows:,} records across "
        f"{columns} columns."
    )

    if missing_values == 0:

        insights.append(
            "No missing values were detected "
            "in the dataset."
        )

    else:

        insights.append(
            f"The dataset contains "
            f"{missing_values:,} missing values."
        )

    if duplicate_rows == 0:

        insights.append(
            "No duplicate rows were detected."
        )

    else:

        insights.append(
            f"{duplicate_rows:,} duplicate rows "
            f"were detected."
        )

    if numeric_data:

        highest_average = max(
            numeric_data,
            key=lambda x: x["average"]
        )

        insights.append(
            f"{highest_average['name']} has the "
            f"highest average value among the "
            f"numerical columns."
        )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=24,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontSize=16,
        leading=20,
        spaceBefore=15,
        spaceAfter=10
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        spaceAfter=8
    )

    story = []

    story.append(
        Paragraph(
            "InsightIQ",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Business Analytics Report",
            heading_style
        )
    )

    story.append(
        Paragraph(
            "Generated by InsightIQ",
            body_style
        )
    )

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            "Dataset Summary",
            heading_style
        )
    )

    summary_data = [
        ["Metric", "Value"],
        ["Total Records", f"{rows:,}"],
        ["Total Columns", f"{columns:,}"],
        ["Missing Values", f"{missing_values:,}"],
        ["Duplicate Rows", f"{duplicate_rows:,}"]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            3.5 * inch,
            2.5 * inch
        ]
    )

    summary_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#6d28d9")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                8
            )

        ])
    )

    story.append(summary_table)

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "Numerical Analysis",
            heading_style
        )
    )

    if numeric_data:

        table_data = [[
            "Column",
            "Average",
            "Minimum",
            "Maximum",
            "Total"
        ]]

        for item in numeric_data:

            table_data.append([
                item["name"],
                f"{item['average']:,.2f}",
                f"{item['minimum']:,.2f}",
                f"{item['maximum']:,.2f}",
                f"{item['total']:,.2f}"
            ])

        analysis_table = Table(
            table_data,
            repeatRows=1,
            colWidths=[
                1.7 * inch,
                1.0 * inch,
                1.0 * inch,
                1.0 * inch,
                1.0 * inch
            ]
        )

        analysis_table.setStyle(
            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#6d28d9")
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )

            ])
        )

        story.append(analysis_table)

    else:

        story.append(
            Paragraph(
                "No numerical columns were detected.",
                body_style
            )
        )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "Key Insights",
            heading_style
        )
    )

    for index, insight in enumerate(
        insights,
        start=1
    ):

        story.append(
            Paragraph(
                f"<b>{index}.</b> {insight}",
                body_style
            )
        )

    story.append(
        Spacer(1, 20)
    )

    story.append(
        Paragraph(
            "InsightIQ — Turning raw data into "
            "meaningful business insights.",
            body_style
        )
    )
    document.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="InsightIQ_Business_Report.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)
    
       