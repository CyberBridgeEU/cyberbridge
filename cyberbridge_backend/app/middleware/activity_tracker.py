# middleware/activity_tracker.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..database.database import get_db
from ..models import models
import logging

logger = logging.getLogger(__name__)

class ActivityTrackerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track user activity by updating last_activity timestamp.
    Only updates if last update was more than 1 minute ago to reduce DB writes.
    """

    async def dispatch(self, request: Request, call_next):
        # Process the request first
        response = await call_next(request)

        # Try to extract user from request state (set by auth dependency)
        user = getattr(request.state, "user", None)

        if user and hasattr(user, 'id'):
            try:
                # Get database session
                db: Session = next(get_db())
                try:
                    # Check if we should update (only if last update was >1 minute ago)
                    db_user = db.query(models.User).filter(models.User.id == user.id).first()

                    if db_user:
                        now = datetime.utcnow()
                        should_update = False

                        if db_user.last_activity is None:
                            should_update = True
                        else:
                            # Only update if last activity was more than 1 minute ago
                            time_diff = now - db_user.last_activity
                            if time_diff.total_seconds() > 60:  # 60 seconds = 1 minute
                                should_update = True

                        if should_update:
                            db_user.last_activity = now
                            db.commit()
                            logger.debug(f"Updated last_activity for user {user.email}")

                finally:
                    db.close()

            except Exception as e:
                logger.error(f"Error updating user activity: {str(e)}")
                # Don't fail the request if activity tracking fails

        return response
