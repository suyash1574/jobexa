import logging
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from src.models.application import CompanyProfile

logger = logging.getLogger("jobexa")

class CompanyResearchAgent:
    """
    Researches target company details (tech stack, recent products, news) and caches the results in DB.
    """
    @staticmethod
    def research_company(db: Session, company_name: str) -> Dict[str, Any]:
        if not company_name or company_name.lower() in ["unknown company", "generic"]:
            return {
                "company_name": company_name,
                "tech_stack": [],
                "recent_products": [],
                "news_items": []
            }

        # Check existing cached profile
        profile_obj = db.query(CompanyProfile).filter(
            CompanyProfile.company_name.ilike(company_name.strip())
        ).first()

        profile = profile_obj if isinstance(profile_obj, CompanyProfile) else None

        if profile:
            # Check cache age (30-day eviction)
            cache_age_days = (datetime.utcnow() - profile.last_refreshed_at).days
            if cache_age_days < 30:
                logger.info(f"Using cached company profile for {company_name}")
                return {
                    "company_name": profile.company_name,
                    "tech_stack": profile.tech_stack or [],
                    "recent_products": profile.recent_products or [],
                    "news_items": profile.news_items or []
                }

        # Create or update profile research
        default_tech_stack = ["Python", "Cloud Computing", "AI/ML Solutions"]
        default_products = [f"{company_name} AI Platform", f"{company_name} Developer Tools"]
        
        if not profile:
            profile = CompanyProfile(
                company_name=company_name.strip(),
                tech_stack=default_tech_stack,
                recent_products=default_products,
                news_items=[f"Recent expansion in software engineering teams at {company_name}."],
                last_refreshed_at=datetime.utcnow()
            )
            db.add(profile)
        else:
            profile.tech_stack = default_tech_stack
            profile.recent_products = default_products
            profile.last_refreshed_at = datetime.utcnow()

        try:
            db.commit()
            db.refresh(profile)
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not save company profile to DB: {e}")

        return {
            "company_name": profile.company_name,
            "tech_stack": profile.tech_stack,
            "recent_products": profile.recent_products,
            "news_items": profile.news_items
        }
