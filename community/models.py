# ============================================================
# COMMUNITY - MODELS
# ============================================================

"""
MarketPulse Community models.

This application contains two related social features:

1. CommunityPost
       ↓
   Public MarketPulse community posts.

2. Conversation / PrivateMessage
       ↓
   Private user-to-user messaging.


PRIVATE MESSAGING ARCHITECTURE:

User
    ↓
Conversation
    ↓
Participants
    ↓
PrivateMessage
    ↓
PrivateMessage
    ↓
PrivateMessage


MIGRATION STRATEGY:

The original MarketPulse messaging system stored every
PrivateMessage independently using:

    sender
    recipient
    subject
    body
    created_at
    is_read

The new messaging architecture introduces Conversation so
multiple messages between users can be displayed as one
continuous chat thread.

For the first migration:

    Conversation
        ↓
    is added as a new model

and:

    PrivateMessage.conversation
        ↓
    is temporarily nullable

This allows existing messages to remain in the database.

The original recipient and subject fields are also retained
during this migration phase so existing views, templates and
stored data are not destroyed while the new conversation
workflow is introduced.

After existing PrivateMessage rows have been assigned to
Conversation objects and the new messaging workflow has been
tested, the data model can be simplified further.

============================================================
"""


from django.conf import settings
from django.db import models
from django.utils import timezone


# ============================================================
# 1. COMMUNITY POST
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

        (
            "UPDATE",
            "Market Update",
        ),

        (
            "WARNING",
            "Trading Warning",
        ),

        (
            "IDEA",
            "Trading Idea",
        ),

        (
            "RISK",
            "Risk Alert",
        ),

        (
            "DISCUSSION",
            "Discussion",
        ),

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
    # Optional ticker / asset symbol
    # --------------------------------------------------------

    ticker = models.CharField(
        max_length=15,
        blank=True,
        help_text=(
            "Optional stock or asset ticker, "
            "for example AAPL or MSFT."
        ),
    )


    # --------------------------------------------------------
    # Main post content
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
    # Model configuration
    # --------------------------------------------------------

    class Meta:

        ordering = [
            "-created_at",
        ]


    # --------------------------------------------------------
    # Human-readable representation
    # --------------------------------------------------------

    def __str__(self):

        return (
            f"{self.author} - "
            f"{self.get_post_type_display()}"
        )


# ============================================================
# 2. PRIVATE CONVERSATION
# ============================================================

class Conversation(models.Model):
    """
    Represents a private MarketPulse conversation.

    A Conversation groups several PrivateMessage records
    into one continuous discussion.

    Current intended use:

        User1 ↔ User2

    Example:

        Conversation
            ↓
        User1: Hello
            ↓
        User2: Hi
            ↓
        User1: What do you think about AAPL?
            ↓
        User2: I am reviewing the historical data.

    A ManyToMany relationship is used for participants.

    The current MarketPulse user interface uses one-to-one
    conversations, but this structure keeps the database
    flexible enough for possible future multi-user threads.
    """


    # --------------------------------------------------------
    # Conversation participants
    # --------------------------------------------------------

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="marketpulse_conversations",
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
    # Model configuration
    # --------------------------------------------------------

    class Meta:

        ordering = [
            "-updated_at",
        ]


    # --------------------------------------------------------
    # Human-readable representation
    # --------------------------------------------------------

    def __str__(self):

        if not self.pk:

            return (
                "Unsaved MarketPulse Conversation"
            )


        participant_names = list(
            self.participants
            .order_by(
                "username"
            )
            .values_list(
                "username",
                flat=True,
            )
        )


        if participant_names:

            return (
                "Conversation: "
                +
                " ↔ ".join(
                    participant_names
                )
            )


        return (
            f"Conversation {self.pk}"
        )


    # --------------------------------------------------------
    # Return participant other than supplied user
    # --------------------------------------------------------

    def get_other_participant(
        self,
        user,
    ):
        """
        Return the other participant in a one-to-one
        conversation.

        If no other participant exists, return None.
        """

        if not user or not getattr(
            user,
            "pk",
            None,
        ):

            return None


        return (
            self.participants
            .exclude(
                pk=user.pk
            )
            .order_by(
                "username"
            )
            .first()
        )


    # --------------------------------------------------------
    # Return most recent message
    # --------------------------------------------------------

    def get_last_message(self):
        """
        Return the newest PrivateMessage belonging to this
        conversation.
        """

        return (
            self.messages
            .order_by(
                "-created_at"
            )
            .first()
        )


    # --------------------------------------------------------
    # Update conversation activity time
    # --------------------------------------------------------

    def touch(self):
        """
        Move the conversation to the most recently active
        position.

        This is useful when a new message is created.
        """

        self.updated_at = timezone.now()

        self.save(
            update_fields=[
                "updated_at",
            ]
        )


# ============================================================
# 3. PRIVATE MESSAGE
# ============================================================

class PrivateMessage(models.Model):
    """
    Stores an individual private message exchanged between
    MarketPulse users.

    New architecture:

        Conversation
            ↓
        PrivateMessage
            ↓
        PrivateMessage
            ↓
        PrivateMessage

    During the migration phase:

    - conversation is nullable
    - recipient remains
    - subject remains

    This protects existing MarketPulse messages while the
    original email-style Inbox is migrated to the new
    conversation-style interface.
    """


    # --------------------------------------------------------
    # Conversation / chat thread
    # --------------------------------------------------------

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",

        # ----------------------------------------------------
        # TEMPORARY MIGRATION SETTINGS
        # ----------------------------------------------------
        #
        # Existing PrivateMessage records were created before
        # Conversation existed.
        #
        # Therefore the first schema migration must allow
        # conversation to be NULL.
        #
        # After old messages have been assigned to
        # conversations, this can eventually become required.
        #
        null=True,
        blank=True,
    )


    # --------------------------------------------------------
    # User who sent the message
    # --------------------------------------------------------

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_marketpulse_messages",
    )


    # --------------------------------------------------------
    # Recipient
    # --------------------------------------------------------
    #
    # Retained during migration for compatibility with:
    #
    # - existing database rows
    # - current Home message preview
    # - old compose-message workflow
    # - migration of historical messages
    #
    # --------------------------------------------------------

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_marketpulse_messages",
    )


    # --------------------------------------------------------
    # Subject
    # --------------------------------------------------------
    #
    # Retained temporarily for compatibility with the
    # original email-style messaging system.
    #
    # The future chat interface does not need the user to
    # enter a new subject for every reply.
    #
    # --------------------------------------------------------

    subject = models.CharField(
        max_length=150,
    )


    # --------------------------------------------------------
    # Message body
    # --------------------------------------------------------

    body = models.TextField(
        max_length=3000,
    )


    # --------------------------------------------------------
    # Message timestamp
    # --------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True,
    )


    # --------------------------------------------------------
    # Read / unread state
    # --------------------------------------------------------

    is_read = models.BooleanField(
        default=False,
    )


    # --------------------------------------------------------
    # Model configuration
    # --------------------------------------------------------

    class Meta:

        # Keep newest-first as the default because existing
        # MarketPulse views may rely on recent messages being
        # returned first.
        #
        # The new conversation-detail view will explicitly use:
        #
        # .order_by("created_at")
        #
        # so chat messages appear oldest → newest.
        ordering = [
            "-created_at",
        ]


        indexes = [

            # ------------------------------------------------
            # Fast conversation-history lookup
            # ------------------------------------------------

            models.Index(
                fields=[
                    "conversation",
                    "created_at",
                ],
                name="community_conv_date_idx",
            ),


            # ------------------------------------------------
            # Fast unread-message lookup
            # ------------------------------------------------

            models.Index(
                fields=[
                    "recipient",
                    "is_read",
                ],
                name="community_unread_idx",
            ),

        ]


    # --------------------------------------------------------
    # Human-readable representation
    # --------------------------------------------------------

    def __str__(self):

        return (
            f"{self.sender} → "
            f"{self.recipient}: "
            f"{self.subject}"
        )


    # --------------------------------------------------------
    # Save message and update conversation activity
    # --------------------------------------------------------

    def save(
        self,
        *args,
        **kwargs,
    ):
        """
        Save the PrivateMessage.

        When a NEW message belongs to a conversation,
        update that Conversation's updated_at timestamp.

        This ensures the most recently active conversation
        appears first in the Inbox.

        Marking an existing message as read does NOT move the
        conversation back to the top.
        """

        is_new_message = (
            self._state.adding
        )


        super().save(
            *args,
            **kwargs,
        )


        if (
            is_new_message
            and
            self.conversation_id
        ):

            Conversation.objects.filter(
                pk=self.conversation_id
            ).update(
                updated_at=timezone.now()
            )