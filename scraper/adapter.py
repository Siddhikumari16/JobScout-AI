from abc import ABC, abstractmethod
from typing import List, Dict, Any


class SourceAdapter(ABC):
    """Abstract adapter that returns normalized job records.

    Normalized record shape (matching scraper/schemas/job_schema.json):
    {
      "title": str | None,
      "skills": List[str],
      "experience_years": int | None,
      "location": str | None,
      "summary": str
    }
    """

    @abstractmethod
    def fetch(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch raw jobs from the source and return normalized records."""

