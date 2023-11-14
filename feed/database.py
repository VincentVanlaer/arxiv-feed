from typing import List, Tuple
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_
from feed.tables import ArXivUpdate, ArXivMetadata
from datetime import datetime
from sqlalchemy.orm import aliased

def get_announce_papers(first_day: datetime, last_day: datetime, archives: List[str], categories: List[str])->List[Tuple[ArXivUpdate, ArXivMetadata]]:
    result_limit = 15
    version_threshold = 4

    # Create an alias for ArXivMetadata table to distinguish between the two
    metadata_alias = aliased(ArXivMetadata)

    # Your modified query
    query_result = ArXivUpdate.query.join(metadata_alias, ArXivUpdate.document_id == metadata_alias.document_id).filter(
        or_(
            ArXivUpdate.category.in_(categories),
            ArXivUpdate.archive.in_(archives)
        ),
        and_(
            or_(
                ArXivUpdate.action != "replace",
                and_(
                    ArXivUpdate.action == "replace",
                    ArXivUpdate.version <= version_threshold
                )
            ),
            ArXivUpdate.action != "abs_only",
            ArXivUpdate.date >= first_day,
            ArXivUpdate.date <= last_day,  # Inclusive upper bound
            metadata_alias.is_current == 1  # dont display multiple version in a day TODO v4 and v5 in same day once version is fixed
        )
    ).add_entity(metadata_alias).limit(result_limit).all()

    #TODO any error handling?
    return query_result