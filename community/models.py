# ============================================================
# COMMUNITY - MODELS
# ============================================================
# FILE PURPOSE:
# This file defines the database structure for the Community app.
#
# DJANGO FRAMEWORK:
#
# User
#   ↓
# urls.py
#   ↓
# community/views.py
#   ↓
# community/models.py          ← THIS FILE / MODEL LAYER
#   ↓
# Django ORM
#   ↓
# PostgreSQL / Neon
#   ↓
# community/views.py
#   ↓
# templates/community/*.html
#   ↓
# Browser
#
# PROGRAMMING LANGUAGE CONCEPTS USED:
#
# imports
# classes
# inheritance
# variables / constants
# attributes
# methods
# parameters
# return values
# lists
# tuples
# strings
# f-strings
# Boolean expressions
# conditionals
# object relationships
# method overriding
# *args and **kwargs
# Django ORM
# database indexes
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

# ============================================================
# 1. IMPORTS
# Programming concept: modules and imports
# ============================================================

from django.conf import settings  # Imports Django project settings so the model can use the configured custom User model.
from django.db import models  # Imports Django ORM model classes and database field types.
from django.utils import timezone  # Imports Django's timezone-aware date/time utilities.

# ============================================================
# 2. COMMUNITY POST MODEL
# Programming concepts:
# - class
# - inheritance
# - class attributes
# - tuples
# - lists
# - object relationships
# ============================================================

class CommunityPost(models.Model):  # Defines CommunityPost and inherits Django database behaviour from models.Model.
    """
    Stores trading-related posts created by MarketPulse users.

    Users can publish:

    - Market observations
    - Trading warnings
    - Strategy discussions
    - Risk-management notes
    - General stock-market updates
    """

    # --------------------------------------------------------
    # 2.1 POST TYPE CHOICES
    # Programming concept: constant-like class variable
    # --------------------------------------------------------

    POST_TYPE_CHOICES = [  # Stores the allowed post categories as a Python list.
        (  # Starts the first tuple containing database value and human-readable label.
            "UPDATE",  # Database value stored for a market update.
            "Market Update",  # Friendly value displayed to the user.
        ),  # Ends the UPDATE tuple.
        (  # Starts the trading warning tuple.
            "WARNING",  # Database value stored for a warning.
            "Trading Warning",  # Friendly label displayed to the user.
        ),  # Ends the WARNING tuple.
        (  # Starts the trading idea tuple.
            "IDEA",  # Database value stored for a trading idea.
            "Trading Idea",  # Friendly label displayed to the user.
        ),  # Ends the IDEA tuple.
        (  # Starts the risk alert tuple.
            "RISK",  # Database value stored for a risk alert.
            "Risk Alert",  # Friendly label displayed to the user.
        ),  # Ends the RISK tuple.
        (  # Starts the discussion tuple.
            "DISCUSSION",  # Database value stored for a discussion.
            "Discussion",  # Friendly label displayed to the user.
        ),  # Ends the DISCUSSION tuple.
    ]  # Ends the list of available post types.

    # --------------------------------------------------------
    # 2.2 USER WHO CREATED THE POST
    # Programming concept: object relationship / ForeignKey
    # --------------------------------------------------------

    author = models.ForeignKey(  # Creates a many-posts-to-one-user database relationship.
        settings.AUTH_USER_MODEL,  # Uses the custom User model configured in Django settings.
        on_delete=models.CASCADE,  # Deletes this user's posts if the user itself is deleted.
        related_name="community_posts",  # Allows user.community_posts to retrieve this user's posts.
    )  # Finishes the author ForeignKey definition.

    # --------------------------------------------------------
    # 2.3 POST CATEGORY
    # Programming concept: string field + validation choices
    # --------------------------------------------------------

    post_type = models.CharField(  # Creates a database column containing a short string.
        max_length=20,  # Limits the stored string to 20 characters.
        choices=POST_TYPE_CHOICES,  # Restricts normal Django form choices to the categories defined above.
        default="UPDATE",  # Uses UPDATE when no other post type is supplied.
    )  # Finishes the post_type field.

    # --------------------------------------------------------
    # 2.4 OPTIONAL TICKER / ASSET SYMBOL
    # Programming concept: field configuration
    # --------------------------------------------------------

    ticker = models.CharField(  # Creates a short text database column for a ticker symbol.
        max_length=15,  # Allows a maximum of 15 characters.
        blank=True,  # Allows Django validation/forms to accept an empty ticker.
        help_text=(  # Starts a multi-line Python string expression used as help text.
            "Optional stock or asset ticker, "  # First part of the help message.
            "for example AAPL or MSFT."  # Second part; adjacent strings are automatically joined by Python.
        ),  # Ends the help_text expression.
    )  # Finishes the ticker field.

    # --------------------------------------------------------
    # 2.5 MAIN POST CONTENT
    # Programming concept: text value / attribute
    # --------------------------------------------------------

    content = models.TextField(  # Creates a database text field for the main community post.
        max_length=1500,  # Restricts the expected post length to 1500 characters.
    )  # Finishes the content field.

    # --------------------------------------------------------
    # 2.6 TIMESTAMPS
    # Programming concept: automatic object state
    # --------------------------------------------------------

    created_at = models.DateTimeField(  # Creates a date/time field for when the post was created.
        auto_now_add=True,  # Django automatically sets this once when the object is first created.
    )  # Finishes created_at.

    updated_at = models.DateTimeField(  # Creates a date/time field for the latest update.
        auto_now=True,  # Django updates this timestamp whenever the object is saved.
    )  # Finishes updated_at.

    # --------------------------------------------------------
    # 2.7 MODEL CONFIGURATION
    # Programming concept: nested class
    # --------------------------------------------------------

    class Meta:  # Defines extra configuration for the CommunityPost model.
        ordering = [  # Sets the model's default database ordering.
            "-created_at",  # Minus means newest CommunityPost records appear first.
        ]  # Ends the ordering list.

    # --------------------------------------------------------
    # 2.8 HUMAN-READABLE REPRESENTATION
    # Programming concepts:
    # - method
    # - self
    # - return value
    # - f-string
    # --------------------------------------------------------

    def __str__(self):  # Defines how a CommunityPost object is represented as readable text.
        return (  # Returns the constructed string to Python/Django.
            f"{self.author} - "  # Inserts the object's author into an f-string.
            f"{self.get_post_type_display()}"  # Uses Django's generated method to show the friendly choice label.
        )  # Ends the returned string expression.

# ============================================================
# 3. PRIVATE CONVERSATION MODEL
# Programming concepts:
# - class
# - inheritance
# - ManyToMany relationships
# - methods
# - conditionals
# - lists
# - QuerySets
# ============================================================

class Conversation(models.Model):  # Defines a database model representing one private conversation.
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
    # 3.1 CONVERSATION PARTICIPANTS
    # Programming concept: many-to-many object relationship
    # --------------------------------------------------------

    participants = models.ManyToManyField(  # Allows multiple users to belong to a Conversation.
        settings.AUTH_USER_MODEL,  # Connects participants to the project's configured User model.
        related_name="marketpulse_conversations",  # Allows a user to access their conversations through this reverse name.
    )  # Finishes the ManyToMany relationship.

    # --------------------------------------------------------
    # 3.2 TIMESTAMPS
    # --------------------------------------------------------

    created_at = models.DateTimeField(  # Stores when the Conversation was originally created.
        auto_now_add=True,  # Automatically records the creation date/time once.
    )  # Finishes created_at.

    updated_at = models.DateTimeField(  # Stores when the Conversation was most recently active.
        auto_now=True,  # Automatically updates when the Conversation object itself is saved.
    )  # Finishes updated_at.

    # --------------------------------------------------------
    # 3.3 MODEL CONFIGURATION
    # Programming concept: nested Meta class
    # --------------------------------------------------------

    class Meta:  # Holds Django metadata for Conversation.
        ordering = [  # Defines default ordering for Conversation QuerySets.
            "-updated_at",  # Shows the most recently active conversations first.
        ]  # Ends the ordering list.

    # --------------------------------------------------------
    # 3.4 HUMAN-READABLE REPRESENTATION
    # Programming concepts:
    # - special method
    # - conditionals
    # - local variables
    # - lists
    # - QuerySet methods
    # - return
    # --------------------------------------------------------

    def __str__(self):  # Defines the readable string representation of a Conversation.
        if not self.pk:  # Checks whether this object has not yet received a database primary key.
            return (  # Immediately returns a label for an unsaved object.
                "Unsaved MarketPulse Conversation"  # Text used when the Conversation is not yet in the database.
            )  # Ends the return expression.

        participant_names = list(  # Creates a normal Python list containing participant usernames.
            self.participants  # Starts with the participants ManyToMany manager.
            .order_by(  # Sorts the participants before retrieving their usernames.
                "username"  # Sorts alphabetically by username.
            )  # Finishes order_by().
            .values_list(  # Retrieves only selected database field values rather than complete User objects.
                "username",  # Requests the username field.
                flat=True,  # Returns a flat sequence rather than one-element tuples.
            )  # Finishes values_list().
        )  # Converts the QuerySet result into a Python list.

        if participant_names:  # Checks whether at least one participant name exists.
            return (  # Returns a readable conversation description.
                "Conversation: "  # Adds text before the participant names.
                +  # Uses Python string concatenation.
                " ↔ ".join(  # Joins usernames together with the conversation arrow symbol.
                    participant_names  # Supplies the list of usernames to join().
                )  # Finishes join().
            )  # Finishes the return expression.

        return (  # Fallback return when there are no participant names.
            f"Conversation {self.pk}"  # Uses an f-string containing the database primary key.
        )  # Ends the fallback return.

    # --------------------------------------------------------
    # 3.5 RETURN PARTICIPANT OTHER THAN SUPPLIED USER
    # Programming concepts:
    # - method parameter
    # - Boolean logic
    # - getattr()
    # - QuerySet filtering
    # --------------------------------------------------------

    def get_other_participant(  # Defines a custom method for locating the other user.
        self,  # Refers to the current Conversation object.
        user,  # Receives the User object that should be excluded.
    ):  # Ends the method signature.
        """
        Return the other participant in a one-to-one
        conversation.

        If no other participant exists, return None.
        """

        if not user or not getattr(  # Checks that a valid saved user was supplied.
            user,  # Object whose attribute Python will inspect.
            "pk",  # Looks for the user's primary-key attribute.
            None,  # Returns None instead of raising an error if the attribute does not exist.
        ):  # Ends the condition.
            return None  # Stops the method and returns no participant.

        return (  # Returns the resulting User object.
            self.participants  # Starts with all participants in this Conversation.
            .exclude(  # Removes one or more matching records.
                pk=user.pk  # Removes the supplied user's database record.
            )  # Finishes exclude().
            .order_by(  # Sorts remaining participants.
                "username"  # Sorts alphabetically by username.
            )  # Finishes order_by().
            .first()  # Returns the first User object or None if no object exists.
        )  # Ends the return expression.

    # --------------------------------------------------------
    # 3.6 RETURN MOST RECENT MESSAGE
    # Programming concepts:
    # - method
    # - reverse relationship
    # - method chaining
    # --------------------------------------------------------

    def get_last_message(self):  # Defines a helper method that finds the latest message.
        """
        Return the newest PrivateMessage belonging to this
        conversation.
        """

        return (  # Returns the most recent PrivateMessage object.
            self.messages  # Uses related_name="messages" from PrivateMessage.conversation.
            .order_by(  # Changes the ordering of the related messages.
                "-created_at"  # Minus means newest timestamp first.
            )  # Finishes order_by().
            .first()  # Returns the first/newest message or None.
        )  # Ends the return expression.

    # --------------------------------------------------------
    # 3.7 UPDATE CONVERSATION ACTIVITY TIME
    # Programming concepts:
    # - state mutation
    # - method call
    # - keyword argument
    # --------------------------------------------------------

    def touch(self):  # Defines a helper method for marking the Conversation as recently active.
        """
        Move the conversation to the most recently active
        position.

        This is useful when a new message is created.
        """

        self.updated_at = timezone.now()  # Changes the object's updated_at attribute to the current timezone-aware time.
        self.save(  # Saves the changed Conversation object to the database.
            update_fields=[  # Tells Django that only the listed database field needs updating.
                "updated_at",  # Specifies that updated_at is the field being saved.
            ]  # Ends the list.
        )  # Finishes the save() call.

# ============================================================
# 4. PRIVATE MESSAGE MODEL
# Programming concepts:
# - class and inheritance
# - ForeignKey relationships
# - Boolean values
# - database indexing
# - method overriding
# - *args / **kwargs
# - conditional logic
# ============================================================

class PrivateMessage(models.Model):  # Defines each individual message as a Django database model.
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
    # 4.1 CONVERSATION / CHAT THREAD
    # Programming concept: ForeignKey relationship
    # --------------------------------------------------------

    conversation = models.ForeignKey(  # Links each PrivateMessage to one Conversation.
        Conversation,  # References the Conversation model defined above.
        on_delete=models.CASCADE,  # Deletes related messages if their Conversation is deleted.
        related_name="messages",  # Allows conversation.messages to retrieve its PrivateMessage records.

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
        null=True,  # Allows the database value to temporarily be NULL.
        blank=True,  # Allows Django forms/validation to temporarily accept an empty Conversation.
    )  # Finishes the conversation ForeignKey.

    # --------------------------------------------------------
    # 4.2 USER WHO SENT THE MESSAGE
    # --------------------------------------------------------

    sender = models.ForeignKey(  # Creates a relationship from each message to its sending User.
        settings.AUTH_USER_MODEL,  # Uses MarketPulse's configured custom User model.
        on_delete=models.CASCADE,  # Deletes sent messages if their User is deleted.
        related_name="sent_marketpulse_messages",  # Allows user.sent_marketpulse_messages to retrieve sent messages.
    )  # Finishes the sender relationship.

    # --------------------------------------------------------
    # 4.3 RECIPIENT
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

    recipient = models.ForeignKey(  # Creates a relationship from a message to the receiving User.
        settings.AUTH_USER_MODEL,  # Uses MarketPulse's configured User model.
        on_delete=models.CASCADE,  # Deletes received messages if their User is deleted.
        related_name="received_marketpulse_messages",  # Allows a User to retrieve messages received by them.
    )  # Finishes the recipient relationship.

    # --------------------------------------------------------
    # 4.4 SUBJECT
    # --------------------------------------------------------
    #
    # Retained temporarily for compatibility with the
    # original email-style messaging system.
    #
    # The future chat interface does not need the user to
    # enter a new subject for every reply.
    #
    # --------------------------------------------------------

    subject = models.CharField(  # Stores the message subject as a short string.
        max_length=150,  # Limits the subject to 150 characters.
    )  # Finishes the subject field.

    # --------------------------------------------------------
    # 4.5 MESSAGE BODY
    # --------------------------------------------------------

    body = models.TextField(  # Stores the main text content of the private message.
        max_length=3000,  # Limits message body length to 3000 characters.
    )  # Finishes the body field.

    # --------------------------------------------------------
    # 4.6 MESSAGE TIMESTAMP
    # --------------------------------------------------------

    created_at = models.DateTimeField(  # Stores when the PrivateMessage was created.
        auto_now_add=True,  # Django automatically sets the timestamp when the message is first created.
    )  # Finishes created_at.

    # --------------------------------------------------------
    # 4.7 READ / UNREAD STATE
    # Programming concept: Boolean value
    # --------------------------------------------------------

    is_read = models.BooleanField(  # Creates a True/False database field.
        default=False,  # New messages begin as unread.
    )  # Finishes the is_read field.

    # --------------------------------------------------------
    # 4.8 MODEL CONFIGURATION
    # Programming concepts:
    # - nested class
    # - list
    # - database indexes
    # --------------------------------------------------------

    class Meta:  # Defines database/model configuration for PrivateMessage.

        # Keep newest-first as the default because existing
        # MarketPulse views may rely on recent messages being
        # returned first.
        #
        # The new conversation-detail view will explicitly use:
        #
        # .order_by("created_at")
        #
        # so chat messages appear oldest → newest.
        ordering = [  # Defines the default order of PrivateMessage query results.
            "-created_at",  # Returns newest messages first by default.
        ]  # Ends the ordering list.

        indexes = [  # Creates explicit database indexes for frequently queried fields.

            # ------------------------------------------------
            # Fast conversation-history lookup
            # ------------------------------------------------

            models.Index(  # Creates the first database index.
                fields=[  # Lists the database columns included in this index.
                    "conversation",  # Indexes the Conversation foreign-key column.
                    "created_at",  # Also indexes creation time for efficient ordered history lookup.
                ],  # Ends the fields list.
                name="community_conv_date_idx",  # Gives this database index an explicit name.
            ),  # Finishes the conversation/date index.

            # ------------------------------------------------
            # Fast unread-message lookup
            # ------------------------------------------------

            models.Index(  # Creates another database index.
                fields=[  # Lists the database columns included in this index.
                    "recipient",  # Indexes the message recipient.
                    "is_read",  # Also indexes whether the message has been read.
                ],  # Ends the fields list.
                name="community_unread_idx",  # Gives the unread-message index an explicit database name.
            ),  # Finishes the recipient/read index.

        ]  # Ends the indexes list.

    # --------------------------------------------------------
    # 4.9 HUMAN-READABLE REPRESENTATION
    # Programming concepts:
    # - special method
    # - f-strings
    # - return value
    # --------------------------------------------------------

    def __str__(self):  # Defines the readable representation of a PrivateMessage object.
        return (  # Returns one combined string.
            f"{self.sender} → "  # Inserts the sender using an f-string.
            f"{self.recipient}: "  # Inserts the recipient.
            f"{self.subject}"  # Inserts the message subject.
        )  # Finishes the returned string.

    # --------------------------------------------------------
    # 4.10 SAVE MESSAGE AND UPDATE CONVERSATION ACTIVITY
    # Programming concepts:
    # - method overriding
    # - *args
    # - **kwargs
    # - object state
    # - superclass method
    # - Boolean condition
    # - database update
    # --------------------------------------------------------

    def save(  # Overrides Django's normal models.Model.save() method.
        self,  # Refers to the current PrivateMessage object.
        *args,  # Collects additional positional arguments supplied to save().
        **kwargs,  # Collects additional named/keyword arguments supplied to save().
    ):  # Ends the method definition.
        """
        Save the PrivateMessage.

        When a NEW message belongs to a conversation,
        update that Conversation's updated_at timestamp.

        This ensures the most recently active conversation
        appears first in the Inbox.

        Marking an existing message as read does NOT move the
        conversation back to the top.
        """

        is_new_message = (  # Stores whether Django considers this object new.
            self._state.adding  # Django's internal model state is True while the object is being inserted.
        )  # Ends the Boolean expression.

        super().save(  # Calls the original Django models.Model.save() implementation.
            *args,  # Passes all positional arguments to Django's original save method.
            **kwargs,  # Passes all keyword arguments to Django's original save method.
        )  # Completes the normal database save.

        if (  # Begins a conditional statement.
            is_new_message  # First condition: this must be a newly created message.
            and  # Boolean AND means both conditions must be true.
            self.conversation_id  # Second condition: the message must belong to a Conversation.
        ):  # Ends the condition.

            Conversation.objects.filter(  # Creates a QuerySet containing the matching Conversation.
                pk=self.conversation_id  # Finds the Conversation using its primary key.
            ).update(  # Performs a direct database update on the matching Conversation.
                updated_at=timezone.now()  # Moves its activity timestamp to the current time.
            )  # Finishes the database update.