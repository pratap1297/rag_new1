"""
LLMQueryEnhancer
Uses the system's llm_client to produce rewritten and expanded versions of a user query.
Turned on via env var ENABLE_LLM_QUERY_ENHANCER=true or config flag.
"""
import os
import logging
from typing import List, Tuple, Dict, Any, Optional

import json

class LLMQueryEnhancer:
    """Generate query variants with an LLM for improved retrieval."""

    def __init__(self, llm_client, max_variants: int = 3):
        self.llm_client = llm_client
        self.max_variants = max_variants or 3
        self.enabled = bool(llm_client)
        self.last_filters: Optional[Dict[str, Any]] = None
        if not self.enabled:
            logging.warning("LLM client not available – LLMQueryEnhancer disabled")

    # Public API expected by QueryEngine
    def enhance_query(self, query: str, context: Optional[Dict[str, Any]] = None):
        """Return a dict with original and variants (minimal contract)."""
        variants, filters = self._generate_variants_and_filters(query)
        self.last_filters = filters
        return {
            'original_query': query,
            'variants': variants
        }

    def get_all_query_variants(self, enhanced: Dict[str, Any]) -> List[Tuple[str, float]]:
        variants = [(enhanced['original_query'], 1.0)]
        for i, variant in enumerate(enhanced.get('variants', [])):
            # confidence 0.9 for first, decays
            variants.append((variant, max(0.5, 0.9 - 0.1 * i)))
        return variants

    # Compatibility helpers so QueryEngine can call .get_enhancer_info()
    def get_enhancer_info(self) -> Dict[str, Any]:
        return {
            'enhancer_type': 'llm',
            'max_variants': self.max_variants,
            'enabled': self.enabled
        }

    # Internal
    def _generate_variants_and_filters(self, query: str):
        if not self.enabled:
            return []
        prompt = (
            "Rewrite the following user question into concise search queries for retrieval. "
            "After the variants, output **one line** containing only a JSON object describing what to count, with keys: 'entity' (e.g., router, incident, building) and optional further filters such as 'building'. "
            "Limit to {} variants.\n\nUser question: {}".format(self.max_variants, query)
        )
        try:
            raw = self.llm_client.generate(prompt)
            lines = [l.strip() for l in raw.split("\n") if l.strip()]
            filters = None
            # Try parse last line as JSON
            if lines:
                try:
                    possible_json = lines[-1]
                    filters = json.loads(possible_json)
                    lines = lines[:-1]  # remove json line from variants
                except json.JSONDecodeError:
                    filters = None
            return lines[: self.max_variants], filters
        except Exception as e:
            logging.warning(f"LLMQueryEnhancer failed: {e}")
            return [], None
