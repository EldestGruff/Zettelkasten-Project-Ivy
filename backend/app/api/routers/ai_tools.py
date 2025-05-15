# backend/app/api/routers/ai_tools.py
from fastapi import APIRouter, HTTPException, status, Depends
from app.api.deps import DbSession
from app.schemas import AICategorizationFeedbackCreate, AICategorizationFeedbackRead # Ensure schemas exist
from app import crud # Ensure crud.ai_feedback exists and has log_categorization_feedback

router = APIRouter(
    prefix="/ai-tools",
    tags=["AI Tools"],
    responses={500: {"description": "Internal server error"}},
)

@router.post(
    "/categorization-feedback",
    response_model=AICategorizationFeedbackRead,
    status_code=status.HTTP_201_CREATED
)
async def submit_categorization_feedback(
    feedback_data: AICategorizationFeedbackCreate,
    db: DbSession
):
    """
    Submit feedback on AI memory type categorization for a note.
    """
    try:
        # Make sure crud.ai_feedback module and its function are correctly imported/available via `crud`
        logged_feedback = crud.ai_feedback.log_categorization_feedback(db=db, feedback_in=feedback_data)
        return logged_feedback
    except Exception as e:
        print(f"Error logging AI feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log AI categorization feedback."
        )