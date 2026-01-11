"""
Question detection utility for determining if a message is asking for information
"""
import re


class QuestionDetector:
    """Detects if a message is a question requiring state reading"""

    # Turkish question words and patterns
    QUESTION_WORDS = [
        "kaç", "nedir", "ne", "nasıl", "hangi", "kim", "nerede",
        "ne zaman", "niçin", "niye", "neden"
    ]

    QUESTION_PATTERNS = [
        r'\?',  # Question mark
        r'(açık mı|kapalı mı|var mı|yok mu|çalışıyor mu|çalışmıyor mu)',
        r'(kaç|ne kadar|hangi|nasıl)\s+\w+',
        r'\w+\s+(nedir|ne|kaç)',
    ]

    STATE_QUERY_PATTERNS = [
        r'(açık mı|kapalı mı)',
        r'(durumu|durum|state)',
        r'(kaç|ne kadar)\s+\w+',
        r'\w+\s+(nedir|ne)',
    ]

    @classmethod
    def is_question(cls, message: str) -> bool:
        """Check if message is a question"""
        message_lower = message.lower().strip()

        # Check for question mark
        if '?' in message:
            return True

        # Check for question words
        for word in cls.QUESTION_WORDS:
            if word in message_lower:
                return True

        # Check for question patterns
        for pattern in cls.QUESTION_PATTERNS:
            if re.search(pattern, message_lower):
                return True

        return False

    @classmethod
    def is_state_query(cls, message: str) -> bool:
        """Check if message is asking about entity state"""
        message_lower = message.lower().strip()

        # Check for state query patterns
        for pattern in cls.STATE_QUERY_PATTERNS:
            if re.search(pattern, message_lower):
                return True

        # Check for common state questions
        state_indicators = [
            "açık mı", "kapalı mı", "çalışıyor mu", "çalışmıyor mu",
            "kaç derece", "kaç %", "ne kadar", "durumu nedir",
            "durum", "state", "değeri", "değer"
        ]

        for indicator in state_indicators:
            if indicator in message_lower:
                return True

        return False

    @classmethod
    def requires_state_read(cls, message: str) -> bool:
        """Determine if message requires reading entity state"""
        return cls.is_question(message) and cls.is_state_query(message)
