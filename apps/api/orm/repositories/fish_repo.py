"""
Fish Species Repository for fish knowledge management
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from ..repository import BaseRepository
from ...models.fish import FishSpecies, FishKnowledge, FishSeasonActivity


class FishSpeciesRepository(BaseRepository[FishSpecies]):
    """Repository for FishSpecies with specialized queries"""

    def __init__(self, session: Session):
        super().__init__(session, FishSpecies)

    def get_by_name(self, name_cn: str) -> Optional[FishSpecies]:
        """
        Get fish species by Chinese name

        Args:
            name_cn: Chinese name

        Returns:
            FishSpecies instance or None if not found
        """
        return (
            self.session.query(FishSpecies)
            .filter(FishSpecies.name_cn == name_cn)
            .first()
        )

    def search_by_name(self, keyword: str, limit: int = 20) -> List[FishSpecies]:
        """
        Search fish species by name (partial match)

        Args:
            keyword: Keyword to search for
            limit: Maximum number of results

        Returns:
            List of matching fish species
        """
        return (
            self.session.query(FishSpecies)
            .filter(
                (FishSpecies.name_cn.like(f"%{keyword}%")) |
                (FishSpecies.name_en.like(f"%{keyword}%")) |
                (FishSpecies.scientific_name.like(f"%{keyword}%"))
            )
            .limit(limit)
            .all()
        )

    def get_with_knowledge(self, species_id: int) -> Optional[FishSpecies]:
        """
        Get fish species with all knowledge preloaded

        Args:
            species_id: Species ID

        Returns:
            FishSpecies instance with knowledge loaded
        """
        return (
            self.session.query(FishSpecies)
            .options(
                joinedload(FishSpecies.knowledge),
                joinedload(FishSpecies.season_activity)
            )
            .filter(FishSpecies.species_id == species_id)
            .first()
        )

    def get_by_category(
        self,
        category: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[FishSpecies]:
        """
        Get fish species by category

        Args:
            category: Fish category
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of fish species
        """
        return (
            self.session.query(FishSpecies)
            .filter(FishSpecies.category == category)
            .offset(offset)
            .limit(limit)
            .all()
        )


class FishKnowledgeRepository(BaseRepository[FishKnowledge]):
    """Repository for FishKnowledge"""

    def __init__(self, session: Session):
        super().__init__(session, FishKnowledge)

    def get_by_species(
        self,
        species_id: int,
        topic: Optional[str] = None
    ) -> List[FishKnowledge]:
        """
        Get knowledge for a species with optional topic filter

        Args:
            species_id: Species ID
            topic: Optional topic filter

        Returns:
            List of knowledge entries
        """
        query = (
            self.session.query(FishKnowledge)
            .filter(FishKnowledge.species_id == species_id)
        )

        if topic:
            query = query.filter(FishKnowledge.topic == topic)

        return query.all()

    def search_by_tags(
        self,
        tags: str,
        limit: int = 50
    ) -> List[FishKnowledge]:
        """
        Search knowledge by tags

        Args:
            tags: Tag to search for
            limit: Maximum number of results

        Returns:
            List of knowledge entries
        """
        return (
            self.session.query(FishKnowledge)
            .filter(FishKnowledge.tags.like(f"%{tags}%"))
            .limit(limit)
            .all()
        )


class FishSeasonActivityRepository(BaseRepository[FishSeasonActivity]):
    """Repository for FishSeasonActivity"""

    def __init__(self, session: Session):
        super().__init__(session, FishSeasonActivity)

    def get_by_species_and_season(
        self,
        species_id: int,
        season: str
    ) -> Optional[FishSeasonActivity]:
        """
        Get season activity for a species

        Args:
            species_id: Species ID
            season: Season (spring/summer/fall/winter)

        Returns:
            FishSeasonActivity instance or None
        """
        return (
            self.session.query(FishSeasonActivity)
            .filter(
                FishSeasonActivity.species_id == species_id,
                FishSeasonActivity.season == season
            )
            .first()
        )

    def get_by_species(self, species_id: int) -> List[FishSeasonActivity]:
        """
        Get all season activities for a species

        Args:
            species_id: Species ID

        Returns:
            List of season activities
        """
        return (
            self.session.query(FishSeasonActivity)
            .filter(FishSeasonActivity.species_id == species_id)
            .order_by(FishSeasonActivity.season)
            .all()
        )

    def get_high_activity_species(self, season: str) -> List[FishSeasonActivity]:
        """
        Get species with high activity for a given season

        Args:
            season: Season (spring/summer/fall/winter)

        Returns:
            List of high-activity season entries
        """
        return (
            self.session.query(FishSeasonActivity)
            .options(joinedload(FishSeasonActivity.species))
            .filter(
                FishSeasonActivity.season == season,
                FishSeasonActivity.activity_level == "高"
            )
            .all()
        )
