# ============================================================
# COMMUNITY - MODELS
# ============================================================

from django.conf import settings
from django.db import models


# ============================================================
# COMMUNITY POST
# ============================================================

class CommunityPost(models.Model):
    """
    Stores trading-related posts created by MarketPulse users.

    Users can publish:
    - Market observations
    - Trading warnings
    - Strategy discussions
    - Risk-management notes
    - General stock-market updates
    """

    POST_TYPE_CHOICES = [
        ("UPDATE", "Market Update"),
        ("WARNING", "Trading Warning"),
        ("IDEA", "Trading Idea"),
        ("RISK", "Risk Alert"),
        ("DISCUSSION", "Discussion"),
    ]


    # --------------------------------------------------------
    # User who created the post
    # --------------------------------------------------------

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
    )


    # --------------------------------------------------------
    # Post category
    # --------------------------------------------------------

    post_type = models.CharField(
        max_length=20,
        choices=POST_TYPE_CHOICES,
        default="UPDATE",
    )




    # --------------------------------------------------------
    # Optional ticker
    # --------------------------------------------------------

    ticker = models.CharField(
        max_length=15,
        blank=True,
        help_text="Optional stock or asset ticker, for example AAPL or MSFT.",
    )


    # --------------------------------------------------------
    # Main content
    # --------------------------------------------------------

    content = models.TextField(
        max_length=1500,
    )


    # --------------------------------------------------------
    # Timestamps
    # --------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )


    # --------------------------------------------------------
    # Ordering
    # --------------------------------------------------------

    class Meta:

        ordering = [
            "-created_at",
        ]


    # --------------------------------------------------------
    # Display name
    # --------------------------------------------------------

    def __str__(self):

        return f"{self.author} - {self.get_post_type_display()}"
    
    
    
    # ============================================================
# PRIVATE MESSAGE
# ============================================================

class PrivateMessage(models.Model):
    """
    Stores private messages exchanged between MarketPulse users.
    """

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_marketpulse_messages",
    )


    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_marketpulse_messages",
    )


    subject = models.CharField(
        max_length=150,
    )


    body = models.TextField(
        max_length=3000,
    )


    created_at = models.DateTimeField(
        auto_now_add=True,
    )


    is_read = models.BooleanField(
        default=False,
    )


    class Meta:

        ordering = [
            "-created_at",
        ]


    def __str__(self):

        return f"{self.sender} → {self.recipient}: {self.subject}"