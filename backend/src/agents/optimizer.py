import logging
from typing import Dict, Any, List, Optional
from src.services.pdf_compiler import compile_markdown_to_pdf

logger = logging.getLogger("jobexa")

class ResumeOptimizerAgent:
    """
    Identifies missing skills from a job description and suggests or compiles an optimized Markdown resume variant.
    """
    @staticmethod
    def optimize_resume(
        base_markdown: str,
        required_skills: List[str],
        job_title: str
    ) -> Dict[str, Any]:
        """
        Analyzes base markdown resume against required skills, inserts missing relevant skills/projects,
        and returns optimized markdown and missing skills list.
        """
        missing_skills = []
        base_lower = base_markdown.lower()

        for skill in required_skills:
            if skill.lower() not in base_lower:
                missing_skills.append(skill)

        optimized_markdown = base_markdown
        if missing_skills:
            skills_section = f"\n\n### Targeted Skills for {job_title}\n- " + "\n- ".join(missing_skills)
            optimized_markdown += skills_section

        try:
            pdf_path = compile_markdown_to_pdf(optimized_markdown)
        except Exception as e:
            logger.warning(f"Failed to compile optimized PDF variant: {e}")
            pdf_path = None

        return {
            "missing_skills": missing_skills,
            "optimized_markdown": optimized_markdown,
            "compiled_pdf_path": pdf_path
        }
