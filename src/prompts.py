"""Vocabulary-aware prompt builders for LLM handoff points.

Each function constructs a prompt that includes the receiver's identity
(its vocabulary) so the LLM can interpret through that lens.
"""

from typing import List, Optional


def scoped_lookup_prompt(
    receiver_name: str,
    symbol_name: str,
    local_vocab: List[str],
    global_def: Optional[str] = None,
) -> str:
    """Build prompt for scoped symbol lookup interpretation."""
    gdef = global_def or "no global definition"
    return (
        f"You are {receiver_name}, whose vocabulary is {local_vocab}.\n"
        f"What does {symbol_name} mean to you?\n"
        f"Global definition: {gdef}\n"
        f"Respond in 1-2 sentences, using only concepts from your vocabulary."
    )


def message_prompt(
    receiver_name: str,
    local_vocab: List[str],
    message_content: str,
) -> str:
    """Build prompt for message handling interpretation."""
    return (
        f"You are {receiver_name}. Your vocabulary: {local_vocab}.\n"
        f"Respond to: {message_content}\n"
        f"Stay within your vocabulary. Constraint is character."
    )


def collision_prompt(
    sender_name: str,
    sender_vocab: List[str],
    target_name: str,
    target_vocab: List[str],
    symbol_name: str,
) -> str:
    """Build prompt for collision synthesis between two receivers."""
    return (
        f"Namespace collision on {symbol_name}.\n"
        f"{sender_name} vocabulary: {sender_vocab}\n"
        f"{target_name} vocabulary: {target_vocab}\n"
        f"Both hold {symbol_name} natively but with different meaning.\n"
        f"Voice both perspectives, then synthesize what neither could say alone."
    )
