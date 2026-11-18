"""Shared read queries that are cached."""
from config import Config
from models import ExaminationRubric
from utils.cache import remember


def rubric_dict(r):
    return {"id": r.id, "examination_id": r.examination_id, "criterion_name": r.criterion_name,
            "max_marks": r.max_marks, "weightage": r.weightage, "description": r.description}


def exam_rubrics(exam_id):
    """Rubric criteria of an exam. Used by admin, examiner and student screens, so cached for 10 min."""
    def build():
        rows = ExaminationRubric.query.filter_by(examination_id=exam_id).order_by(ExaminationRubric.id).all()
        return [rubric_dict(r) for r in rows]
    return remember(f"rubrics:{exam_id}", Config.CACHE_TTL_LONG, build)
