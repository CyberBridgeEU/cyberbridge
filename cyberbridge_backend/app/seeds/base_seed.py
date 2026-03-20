# app/seeds/base_seed.py
import logging
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BaseSeed(ABC):
    """Base class for all seed classes"""

    def __init__(self, db: Session):
        self.db = db
        self.skip_wire_connections = False

    @abstractmethod
    def seed(self) -> dict:
        """
        Execute the seeding logic.
        Returns a dictionary with created entities for reference by other seeds.
        """
        pass

    def get_or_create(self, model_class, filter_kwargs, create_kwargs=None):
        """
        Get an existing record or create a new one.
        Note: Does NOT commit - relies on caller to manage transactions

        Args:
            model_class: SQLAlchemy model class
            filter_kwargs: Dictionary of fields to filter by
            create_kwargs: Dictionary of fields to create with (defaults to filter_kwargs)

        Returns:
            Tuple of (instance, created_boolean)
        """
        if create_kwargs is None:
            create_kwargs = filter_kwargs

        instance = self.db.query(model_class).filter_by(**filter_kwargs).first()

        if instance:
            logger.info(f"{model_class.__name__} already exists: {filter_kwargs}")
            return instance, False
        else:
            # Special handling for Framework models to ensure 'Other' scope type is always included
            if model_class.__name__ == 'Framework':
                import json
                allowed_scope_types_list = []

                # If allowed_scope_types is provided, parse it
                if 'allowed_scope_types' in create_kwargs:
                    if isinstance(create_kwargs['allowed_scope_types'], str):
                        try:
                            allowed_scope_types_list = json.loads(create_kwargs['allowed_scope_types'])
                        except:
                            allowed_scope_types_list = []
                    elif isinstance(create_kwargs['allowed_scope_types'], list):
                        allowed_scope_types_list = create_kwargs['allowed_scope_types']

                # Ensure 'Other' is always included
                if 'Other' not in allowed_scope_types_list:
                    allowed_scope_types_list.append('Other')

                # Update the create_kwargs with the modified list (as JSON string)
                create_kwargs = create_kwargs.copy()  # Don't mutate the original dict
                create_kwargs['allowed_scope_types'] = json.dumps(allowed_scope_types_list)

                # Set default scope_selection_mode if not provided
                if 'scope_selection_mode' not in create_kwargs:
                    create_kwargs['scope_selection_mode'] = 'optional'

            instance = model_class(**create_kwargs)
            self.db.add(instance)
            self.db.flush()  # Flush instead of commit to get ID
            logger.info(f"Created {model_class.__name__}: {create_kwargs}")
            return instance, True
