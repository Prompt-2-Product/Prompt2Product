from app.services.llm.base import LLMClient

SYSTEM_PROMPT_ENHANCE = """You are a product requirements specialist.
Your job is to convert a short app idea into a single, rich, detailed sentence that describes the application.

Rules:
- Identify all key user roles (e.g. admin, seller, customer, student).
- For each role, describe their core actions and features.
- Be specific and concrete — mention real functionality, not vague terms.
- Output ONE sentence only. No bullet points, no headings, no explanation.

Examples:
Input: e-commerce platform
Output: Build a multi-vendor e-commerce platform where sellers can manage inventory and shipping, customers can browse, review products, and place orders with real-time tracking, and admins can handle disputes and refunds.

Input: fitness app
Output: Build an AI-powered fitness tracking application that integrates with smartwatches to track activities, provides personalized workout plans based on biometric data, and allows users to participate in community social challenges with leaderboards.

Input: library portal
Output: Build a library portal where students can search books, issue books, and view due dates.
"""


async def llm_enhance_prompt(llm: LLMClient, model: str, user_prompt: str) -> str:
    """
    Enriches the user's short prompt into a detailed description,
    then formats it into the TaskSpec prompt template.
    """
    enriched = await llm.chat(
        model=model,
        system=SYSTEM_PROMPT_ENHANCE,
        user=user_prompt
    )
    enriched = enriched.strip()

    return enriched
