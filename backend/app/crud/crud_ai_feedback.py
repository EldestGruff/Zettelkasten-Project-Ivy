# backend/app/crud/crud_ai_feedback.py
from sqlalchemy.orm import Session
from app.models.ai_feedback import AICategorizationFeedback # Ensure this model exists
from app.schemas.ai_feedback import AICategorizationFeedbackCreate
# from app.models.enums import MemoryTypeEnum # Not directly used here, but good to be aware of

def log_categorization_feedback(db: Session, *, feedback_in: AICategorizationFeedbackCreate) -> AICategorizationFeedback:
    """
    Logs feedback on AI categorization.
    """
    was_correct: bool | None = None # Python 3.10+ union type hint
    if feedback_in.ai_suggested_type is not None and feedback_in.user_chosen_type is not None:
        was_correct = (feedback_in.ai_suggested_type == feedback_in.user_chosen_type)

    db_feedback = AICategorizationFeedback(
        note_id=feedback_in.note_id,
        note_content_snippet=feedback_in.note_content_snippet[:500] if feedback_in.note_content_snippet else None,
        prompt_used=feedback_in.prompt_used,
        ai_suggested_type=feedback_in.ai_suggested_type,
        ai_reasoning=feedback_in.ai_reasoning,
        user_chosen_type=feedback_in.user_chosen_type,
        was_suggestion_correct=was_correct,
        user_comment=feedback_in.user_comment
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback