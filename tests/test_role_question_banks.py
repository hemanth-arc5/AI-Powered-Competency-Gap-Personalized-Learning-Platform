from pathlib import Path
from modules.scoring import load_competencies, load_role_question_bank, get_role_competencies

ROOT = Path(__file__).resolve().parents[1]

def test_every_role_has_a_dedicated_bank_and_three_difficulties():
    competencies = load_competencies(ROOT / 'data' / 'competencies.csv')
    roles = list(dict.fromkeys(row['role'] for row in competencies))
    assert len(roles) == 9
    for role in roles:
        bank = load_role_question_bank(ROOT / 'data' / 'questions', role)
        skill_ids = {row['skill_id'] for row in get_role_competencies(competencies, role)}
        assert bank
        assert {q['skill_id'] for q in bank} <= skill_ids
        assert {'easy', 'hard', 'advanced'} <= {q['difficulty'] for q in bank}
