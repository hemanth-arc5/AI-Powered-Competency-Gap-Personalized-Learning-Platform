"""Builds data/competencies.csv and data/questions.csv.

Edit the tables below, then run:  python scripts/build_dataset.py

Why a script? The CSV module handles quoting for us, so questions that contain
commas or quotes never corrupt the file.  Everything here is plain ASCII so the
files open correctly on any Windows / Linux / macOS machine.

Data contract (agreed with the team):
  competencies.csv : skill_id, role, skill_name, target_score, prerequisites
  questions.csv    : question_id, skill_id, difficulty, question, options,
                     correct_answer, explanation
  - options are separated by "|"  (so never use "|" inside an option)
  - correct_answer is the LETTER of the right option (A, B, C, D)
  - prerequisites are skill_ids separated by "|" (blank = none)
"""
import csv
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FRONTEND = "Frontend Developer"
ANALYST = "Data Analyst"

# (skill_id, role, skill_name, target_score, prerequisites)
COMPETENCIES = [
    # ---- Frontend Developer ------------------------------------------------
    ("FE_HTML",  FRONTEND, "HTML",                70, ""),
    ("FE_CSS",   FRONTEND, "CSS",                 75, "FE_HTML"),
    ("FE_JS",    FRONTEND, "JavaScript",          80, "FE_HTML"),
    ("FE_RESP",  FRONTEND, "Responsive Design",   70, "FE_CSS"),
    ("FE_GIT",   FRONTEND, "Git",                 65, ""),
    ("FE_REACT", FRONTEND, "React Basics",        70, "FE_JS"),
    # ---- Data Analyst ------------------------------------------------------
    ("DA_EXCEL",  ANALYST, "Excel",               70, ""),
    ("DA_SQL",    ANALYST, "SQL",                 80, ""),
    ("DA_STATS",  ANALYST, "Statistics",          75, ""),
    ("DA_VIZ",    ANALYST, "Data Visualization",  70, "DA_EXCEL|DA_STATS"),
    ("DA_PANDAS", ANALYST, "Python & Pandas",     65, ""),
    ("DA_CLEAN",  ANALYST, "Data Cleaning",       70, "DA_EXCEL"),
]

# Each question: (difficulty, question, correct_option, [three wrong options], explanation)
# 5 questions per skill: 2 easy, 2 medium, 1 hard.
# The position of the correct option is shuffled with a fixed seed so the
# answer letter is spread over A-D but the file is identical on every run.
QUESTIONS = {
    "FE_HTML": [
        ("easy", "Which HTML element represents the top-level (largest) heading of a page section?",
         "<h1>", ["<h6>", "<head>", "<header>"],
         "<h1> is the highest-level heading. <h6> is the smallest, <head> holds page metadata and <header> is a sectioning container."),
        ("easy", "Which attribute gives an image alternative text for screen readers and for when the image fails to load?",
         "alt", ["title", "src", "href"],
         "The alt attribute is the text alternative of an <img>. src is the file location, href is for links."),
        ("medium", "Which element is the most appropriate for a block of main navigation links?",
         "<nav>", ["<section>", "<menu>", "<div class=\"nav\">"],
         "<nav> is the semantic landmark for major navigation; screen readers can jump straight to it."),
        ("medium", "What does the for attribute of a <label> do?",
         "Links the label to the form control whose id has the same value",
         ["Sets the font used by the label", "Names the field that is sent to the server", "Marks the field as required"],
         "label for=\"x\" connects to the control with id=\"x\", so clicking the label focuses the control and assistive technology reads it."),
        ("hard", "Which statement about the defer and async attributes of <script> is correct?",
         "defer runs scripts in order after the document is parsed; async runs each script as soon as it downloads, in no guaranteed order",
         ["async guarantees execution order; defer does not", "Both pause HTML parsing until the script has finished running", "defer only works for inline scripts"],
         "Both download in parallel with parsing. defer preserves order and waits for the parse to finish; async executes immediately on arrival."),
    ],
    "FE_CSS": [
        ("easy", "Which CSS property changes the colour of text?",
         "color", ["font-color", "text-color", "foreground"],
         "color sets the foreground (text) colour. The other names are not valid CSS properties."),
        ("easy", "Which selector targets every element that has the class \"card\"?",
         ".card", ["#card", "card", "*card"],
         "A dot selects by class. # selects by id, and a bare name selects an element type."),
        ("medium", "In the CSS box model, what is the order of the layers from the inside to the outside?",
         "content, padding, border, margin", ["content, border, padding, margin", "margin, border, padding, content", "padding, content, margin, border"],
         "Content sits in the middle, then padding, then the border, and margin is the outermost space."),
        ("medium", "Which declaration turns an element into a flex container for one-dimensional layout of its children?",
         "display: flex", ["display: block", "display: inline", "position: flex"],
         "display: flex enables the flexbox layout model on the element's children."),
        ("hard", "Rule 1 \".a .b { color: red; }\" appears before rule 2 \".b.c { color: blue; }\". A <span class=\"b c\"> sits inside <div class=\"a\">. What colour is the span's text?",
         "Blue", ["Red", "Black (the default colour)", "Neither; the CSS is invalid"],
         "Both selectors have the same specificity (two classes). When specificity ties, the rule declared later wins, so blue."),
    ],
    "FE_JS": [
        ("easy", "Which keyword declares a block-scoped variable that can be reassigned?",
         "let", ["const", "static", "final"],
         "let is block-scoped and reassignable. const cannot be reassigned. static and final are not JavaScript variable keywords."),
        ("easy", "What does typeof \"hello\" evaluate to?",
         "\"string\"", ["\"text\"", "\"char\"", "\"word\""],
         "JavaScript has a single string type; typeof returns the string \"string\"."),
        ("medium", "Which array method returns a NEW array containing only the elements that pass a test?",
         "filter", ["map", "forEach", "reduce"],
         "filter keeps elements for which the callback returns true. map transforms every element, forEach returns nothing, reduce collapses to one value."),
        ("medium", "How does === differ from == in JavaScript?",
         "=== compares value and type without type coercion; == converts types before comparing",
         ["=== assigns a value; == compares", "=== compares only object references", "They behave identically"],
         "Strict equality (===) never coerces, so 5 === \"5\" is false while 5 == \"5\" is true."),
        ("hard", "What is logged by: for (var i = 0; i < 3; i++) { setTimeout(() => console.log(i), 0); }",
         "3 3 3", ["0 1 2", "0 0 0", "2 2 2"],
         "var is function-scoped, so all callbacks share one i. They run after the loop ends, when i is 3. Using let would log 0 1 2."),
    ],
    "FE_RESP": [
        ("easy", "Which meta tag is essential so a page scales correctly on mobile browsers?",
         "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
         ["<meta charset=\"utf-8\">", "<meta name=\"responsive\" content=\"true\">", "<meta http-equiv=\"refresh\" content=\"30\">"],
         "The viewport meta tag tells mobile browsers to use the device width instead of a zoomed-out desktop width."),
        ("easy", "Which CSS at-rule applies styles only when a condition such as screen width is met?",
         "@media", ["@import", "@keyframes", "@font-face"],
         "@media defines media queries. @import loads a stylesheet, @keyframes defines animations, @font-face loads fonts."),
        ("medium", "Which CSS unit is relative to the width of the viewport?",
         "vw", ["px", "pt", "em"],
         "1vw equals 1% of the viewport width. px and pt are absolute units; em is relative to font size."),
        ("medium", "What does a mobile-first approach mean?",
         "Write base styles for small screens, then enhance for larger screens with min-width media queries",
         ["Design only for phones and ignore desktops", "Write desktop styles first and shrink them with max-width queries", "Hide all content on large screens"],
         "Mobile-first starts with the smallest layout and adds complexity as space increases."),
        ("hard", "Which declaration creates as many columns of at least 200px as fit in the row and stretches them to fill it?",
         "grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));",
         ["grid-template-columns: 200px 200px;", "grid-template-columns: repeat(3, 200px);", "grid-auto-flow: column 200px;"],
         "repeat(auto-fit, minmax(200px, 1fr)) lets the grid decide how many columns fit while each is at least 200px."),
    ],
    "FE_GIT": [
        ("easy", "Which command creates a local copy of an existing remote repository?",
         "git clone", ["git init", "git commit", "git branch"],
         "git clone downloads the repository and its history. git init creates a brand-new empty repository."),
        ("easy", "Which command records the staged changes as a new commit with a message?",
         "git commit -m \"message\"", ["git add -m \"message\"", "git push -m \"message\"", "git save \"message\""],
         "git commit -m creates the commit. git add stages files; git push uploads commits."),
        ("medium", "What does git add . do?",
         "Stages new and modified files in the current directory for the next commit",
         ["Commits all changes immediately", "Uploads the files to GitHub", "Deletes untracked files"],
         "Staging prepares changes for a commit; it does not commit or upload anything."),
        ("medium", "Two teammates edit the same line of a file on different branches and you merge them. What happens?",
         "Git reports a merge conflict; you edit the file to resolve it and then commit",
         ["Git silently keeps the newer commit", "Git deletes one of the branches", "The merge succeeds and keeps both versions automatically"],
         "Git cannot decide which edit is correct, so it marks the conflict and waits for a human to resolve it."),
        ("hard", "What is the difference between git fetch and git pull?",
         "fetch downloads remote changes without merging them; pull is a fetch followed by a merge into the current branch",
         ["pull only downloads; fetch merges and pushes", "They are exactly the same command", "fetch uploads local commits; pull deletes them"],
         "fetch is the safe look-before-you-merge step. pull = fetch + merge (or rebase)."),
    ],
    "FE_REACT": [
        ("easy", "What is a React component?",
         "A reusable piece of UI, usually a function that returns JSX", ["A database table", "A CSS file", "A server route"],
         "Components are the building blocks of a React interface."),
        ("easy", "What does JSX stand for?",
         "JavaScript XML, a syntax extension that looks like HTML", ["Java Syntax Extension", "JSON Exchange", "JavaScript Extra"],
         "JSX lets you write markup inside JavaScript; tools compile it into normal JavaScript calls."),
        ("medium", "Which hook adds local state to a function component?",
         "useState", ["useEffect", "useRef", "useContext"],
         "useState returns the current value and a setter. useEffect is for side effects."),
        ("medium", "How does a parent component pass data down to a child component?",
         "Through props", ["Through a global variable only", "By calling useState inside the child", "Through CSS variables"],
         "Props are the inputs of a component and flow from parent to child."),
        ("hard", "When does useEffect(() => { ... }, []) with an empty dependency array run?",
         "Once, after the first render (mount)", ["After every render", "Only when the component unmounts", "Never"],
         "An empty dependency array means there is nothing to re-trigger it, so it runs once after mounting."),
    ],
    "DA_EXCEL": [
        ("easy", "Which function adds up the numbers in a range of cells?",
         "SUM", ["COUNT", "ADD", "TOTALIZE"],
         "=SUM(A1:A10) adds the values. COUNT counts numeric cells; ADD and TOTALIZE are not Excel functions."),
        ("easy", "What does =AVERAGE(B2:B10) return?",
         "The arithmetic mean of the values in B2 to B10", ["The sum of the values", "The middle value (median)", "The largest value"],
         "AVERAGE adds the numbers and divides by how many there are."),
        ("medium", "What does the absolute reference $A$1 do when a formula is copied to another cell?",
         "It keeps pointing at cell A1", ["It shifts to follow the new row and column", "It converts the value to text", "It deletes the original cell"],
         "The dollar signs lock the column and the row so the reference does not move."),
        ("medium", "Which Excel feature summarises a large table by dragging fields into rows, columns and values?",
         "PivotTable", ["Goal Seek", "Data Validation", "Conditional Formatting"],
         "PivotTables aggregate (sum, count, average) data by categories without writing formulas."),
        ("hard", "Column B holds Region and column C holds Sales. Which formula totals the sales for the East region only?",
         "=SUMIF(B:B,\"East\",C:C)", ["=SUMIF(C:C,\"East\",B:B)", "=COUNTIF(B:B,\"East\")", "=SUM(B:B,\"East\")"],
         "SUMIF(range_to_test, criterion, range_to_add). The first range holds the criterion column, the last the numbers to sum."),
    ],
    "DA_SQL": [
        ("easy", "Which SQL statement retrieves rows from a table?",
         "SELECT", ["GET", "FETCH", "OPEN"],
         "SELECT is the query statement used to read data."),
        ("easy", "Which clause filters rows before they are returned?",
         "WHERE", ["ORDER BY", "LIMIT", "AS"],
         "WHERE keeps only the rows that satisfy a condition. ORDER BY sorts and LIMIT caps the row count."),
        ("medium", "Which query returns the number of orders per customer?",
         "SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id;",
         ["SELECT customer_id, COUNT(*) FROM orders WHERE customer_id;", "SELECT COUNT(customer_id) FROM orders ORDER BY customer_id;", "SELECT customer_id FROM orders HAVING COUNT;"],
         "GROUP BY creates one group per customer and COUNT(*) counts the rows in each group."),
        ("medium", "What does an INNER JOIN between two tables return?",
         "Only the rows that have matching values in both tables", ["All rows from the left table only", "All rows from both tables, matched or not", "Every possible pairing of rows (cross product)"],
         "INNER JOIN drops rows without a match. LEFT JOIN would keep every left-table row."),
        ("hard", "What is the difference between WHERE and HAVING?",
         "WHERE filters rows before grouping; HAVING filters groups after aggregation",
         ["HAVING filters rows before grouping; WHERE filters groups", "They are identical", "WHERE works only on text columns"],
         "Aggregates such as COUNT(*) are only known after grouping, so conditions on them belong in HAVING."),
    ],
    "DA_STATS": [
        ("easy", "What is the mean of the values 2, 4, 6 and 8?",
         "5", ["4", "6", "20"],
         "Sum = 20 and there are 4 values, so mean = 20 / 4 = 5."),
        ("easy", "What is the median of 2, 3, 3, 9, 13?",
         "3", ["6", "9", "5"],
         "The values are already sorted and the middle (3rd) value is 3. The mean would be 6."),
        ("medium", "What does the standard deviation measure?",
         "How spread out the values are around the mean", ["The most frequent value", "The middle value of the data", "The number of observations"],
         "A small standard deviation means the values cluster near the mean; a large one means they are spread out."),
        ("medium", "A correlation coefficient of -0.9 between two variables indicates:",
         "A strong negative linear relationship", ["A weak positive relationship", "No relationship", "Proof that one variable causes the other"],
         "The sign gives direction and the size (close to 1) gives strength. Correlation alone does not prove causation."),
        ("hard", "In a hypothesis test with significance level 0.05 you obtain p = 0.03. What is the correct conclusion?",
         "Reject the null hypothesis; the result is statistically significant at the 5% level",
         ["The null hypothesis has a 97% chance of being true", "The alternative hypothesis has a 3% chance of being true", "Accept the null hypothesis"],
         "p < alpha, so the data would be unlikely if the null were true. A p-value is not the probability that a hypothesis is true."),
    ],
    "DA_VIZ": [
        ("easy", "Which chart type is best for showing how a value changes over time?",
         "Line chart", ["Pie chart", "Histogram of the dates", "Treemap"],
         "Lines connect ordered points and make trends easy to see."),
        ("easy", "Which chart type is best for comparing a value across several categories?",
         "Bar chart", ["Line chart", "Scatter plot", "Radar chart with 20 axes"],
         "Bar lengths are easy to compare against a common baseline."),
        ("medium", "Which chart best shows the relationship between two numeric variables, such as height and weight?",
         "Scatter plot", ["Pie chart", "Stacked bar chart", "Donut chart"],
         "Each point plots one observation on both axes, so patterns and correlation become visible."),
        ("medium", "Why can a bar chart whose y-axis starts at 90 instead of 0 be misleading?",
         "It exaggerates the visual difference between bars", ["It hides the category names", "It makes the bars look identical", "It converts the chart into a line chart"],
         "Bar length should be proportional to the value, so a truncated axis makes small differences look large."),
        ("hard", "You want to see the distribution of exam scores and spot skew and outliers. Which chart is most suitable?",
         "Histogram", ["Pie chart", "Stacked bar chart", "Line chart of the row numbers"],
         "A histogram bins a numeric variable and shows its shape; a box plot would also work."),
    ],
    "DA_PANDAS": [
        ("easy", "Which function reads a CSV file into a pandas DataFrame?",
         "pd.read_csv()", ["pd.open_csv()", "pd.load_table_csv()", "pd.DataFrame.read()"],
         "pandas provides read_csv for CSV files."),
        ("easy", "Which method shows the first five rows of a DataFrame df?",
         "df.head()", ["df.top()", "df.first_rows()", "df.peek()"],
         "head() returns the first 5 rows by default; head(10) returns 10."),
        ("medium", "Which expression selects the rows of df where the column age is greater than 30?",
         "df[df[\"age\"] > 30]", ["df.select(age > 30)", "df.where(\"age\", 30)", "df[\"age\"] > 30 = True"],
         "The inner comparison creates a Boolean mask and indexing with it keeps the True rows."),
        ("medium", "Which expression gives the average salary for each department?",
         "df.groupby(\"dept\")[\"salary\"].mean()", ["df.mean(\"dept\", \"salary\")", "df[\"salary\"].groupby().dept", "df.average(\"salary\", by=\"dept\")"],
         "groupby splits the data by department, then mean() is applied to the salary column of each group."),
        ("hard", "What does df.merge(other, on=\"id\", how=\"left\") do?",
         "Keeps every row of df and adds matching columns from other, using NaN where there is no match",
         ["Keeps only the rows that exist in both tables", "Stacks other underneath df", "Deletes rows of df that have no match"],
         "A left merge preserves all rows of the left DataFrame, like SQL LEFT JOIN."),
    ],
    "DA_CLEAN": [
        ("easy", "Which of these is a data-quality problem that cleaning should address?",
         "Duplicate rows", ["Consistent date formats", "Correct data types", "Unique customer IDs"],
         "Duplicated records inflate counts and totals. The other options describe good data."),
        ("easy", "Which pandas method removes exact duplicate rows?",
         "df.drop_duplicates()", ["df.dropna()", "df.fillna(0)", "df.sort_values()"],
         "drop_duplicates removes repeated rows. dropna removes missing values and fillna replaces them."),
        ("medium", "A numeric column is stored as text such as \"1,200\". What is the best fix?",
         "Remove the thousands separator and convert the column to a numeric type", ["Leave it as text and sort it", "Delete the column", "Replace every value with 0"],
         "Calculations need numbers, so strip the formatting characters and convert the type."),
        ("medium", "About 2% of the age values are missing and age is needed for the analysis. What is a sensible approach?",
         "Choose a justified method (for example fill with the median or drop those rows) and document it",
         ["Delete the whole dataset", "Replace every missing age with 0", "Ignore it and hope the charts look fine"],
         "Any treatment changes the results, so choose it deliberately and record the decision."),
        ("hard", "An income column has one value of 9,999,999 while almost all other values are below 100,000. What should you do first?",
         "Investigate whether it is an entry error, a placeholder code or a genuine outlier before deciding how to treat it",
         ["Delete it immediately", "Replace it with the mean", "Do nothing because outliers never matter"],
         "The right treatment (correct, cap, remove or keep) depends on why the value exists."),
    ],
}


def build_rows():
    rng = random.Random(42)  # fixed seed -> identical files on every run
    question_rows = []
    for skill_id, items in QUESTIONS.items():
        for number, (difficulty, text, correct, wrong, explanation) in enumerate(items, start=1):
            options = list(wrong)
            position = rng.randrange(4)
            options.insert(position, correct)
            question_rows.append({
                "question_id": f"{skill_id}_Q{number:02d}",
                "skill_id": skill_id,
                "difficulty": difficulty,
                "question": text,
                "options": "|".join(options),
                "correct_answer": "ABCD"[position],
                "explanation": explanation,
            })
    return question_rows


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "competencies.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["skill_id", "role", "skill_name", "target_score", "prerequisites"])
        writer.writerows(COMPETENCIES)

    rows = build_rows()
    fields = ["question_id", "skill_id", "difficulty", "question", "options", "correct_answer", "explanation"]
    with open(DATA_DIR / "questions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(COMPETENCIES)} competencies and {len(rows)} questions to {DATA_DIR}")


if __name__ == "__main__":
    main()
