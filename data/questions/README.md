# Role-specific assessment question banks

One CSV per role. File names use lowercase snake_case role names (for example `backend_developer.csv`).

Columns (exact headers): `question_id,skill_id,difficulty,question,options,correct_answer,explanation`.
- `question_id`: unique within the bank
- `skill_id`: must match a `skill_id` in `data/competencies.csv` for that role
- `difficulty`: `easy`, `hard`, or `advanced` (legacy `medium` is accepted by parser for backward compatibility)
- `options`: 2–8 choices separated by `|`
- `correct_answer`: option letter A–H

Each role bank should include questions at all three difficulty levels. The seven new role banks include one representative question at each level per competency. Replace these starter questions with validated role-specific assessment content before production use.
