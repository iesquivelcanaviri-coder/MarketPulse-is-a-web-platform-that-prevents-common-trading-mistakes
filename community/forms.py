# ============================================================
# COMMUNITY - FORMS
# ============================================================
#
# Framework mapping:
#
# Community Feed
#     ↓
# CommunityPostForm
#     ↓
# CommunityPost
#
#
# Private Messaging
#     ↓
# NewConversationForm
#     ↓
# Conversation
#     ↓
# First PrivateMessage
#
#
# Existing Conversation
#     ↓
# MessageReplyForm
#     ↓
# PrivateMessage
#
#
# IMPORTANT:
#
# Private messaging now follows a conversation/thread model.
#
# A user selects the recipient only when starting a new
# conversation.
#
# Replies do NOT ask for:
#
# - recipient
# - subject
#
# because those details are already represented by the
# existing conversation.
#
# ============================================================


from django import forms
from django.contrib.auth import get_user_model

from .models import (
    CommunityPost,
    PrivateMessage,
)


# ============================================================
# 1. USER MODEL
# ============================================================

# MarketPulse uses the custom user model configured through:
#
# settings.AUTH_USER_MODEL
#
# get_user_model() ensures this form works with that model
# rather than assuming Django's default User model.
User = get_user_model()


# ============================================================
# 2. COMMUNITY POST FORM
# ============================================================

class CommunityPostForm(forms.ModelForm):
    """
    Form used by authenticated MarketPulse users to publish
    posts to the Community Pulse feed.

    Supported post information:

    - post type
    - optional market ticker
    - post content
    """

    class Meta:

        model = CommunityPost

        fields = [
            "post_type",
            "ticker",
            "content",
        ]

        widgets = {

            "post_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "ticker": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Optional ticker e.g. AAPL"
                    ),
                    "autocomplete": "off",
                }
            ),

            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Share a market update, warning, "
                        "risk observation or trading discussion..."
                    ),
                }
            ),
        }


    # ========================================================
    # NORMALISE OPTIONAL TICKER
    # ========================================================

    def clean_ticker(self):
        """
        Convert a supplied ticker to uppercase.

        Example:

            aapl
                ↓
            AAPL
        """

        ticker = self.cleaned_data.get(
            "ticker"
        )

        if ticker:

            ticker = (
                ticker
                .strip()
                .upper()
            )

        return ticker


# ============================================================
# 3. NEW CONVERSATION FORM
# ============================================================

class NewConversationForm(forms.Form):
    """
    Start a new one-to-one private conversation.

    The user selects another MarketPulse user only once.

    After the conversation exists, further communication uses
    MessageReplyForm and does not require another recipient
    selection.
    """

    # --------------------------------------------------------
    # RECIPIENT
    # --------------------------------------------------------

    recipient = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Start a chat with",
        empty_label="Choose a MarketPulse user",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "aria-label": (
                    "Choose a MarketPulse user"
                ),
            }
        ),
    )


    # --------------------------------------------------------
    # FIRST MESSAGE
    # --------------------------------------------------------

    body = forms.CharField(
        max_length=3000,
        label="Message",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": (
                    "Write your first message..."
                ),
                "aria-label": (
                    "Write your first message"
                ),
            }
        ),
    )


    # ========================================================
    # FORM INITIALISATION
    # ========================================================

    def __init__(
        self,
        *args,
        sender=None,
        **kwargs,
    ):
        """
        Restrict the recipient list so the current user cannot
        start a conversation with themselves.
        """

        super().__init__(
            *args,
            **kwargs,
        )


        # Store the authenticated sender so validation can also
        # check against self-messaging.
        self.sender = sender


        if sender:

            self.fields[
                "recipient"
            ].queryset = (
                User.objects
                .exclude(
                    pk=sender.pk
                )
                .order_by(
                    "username"
                )
            )

        else:

            # Do not expose all users if the form was created
            # without an authenticated sender.
            self.fields[
                "recipient"
            ].queryset = (
                User.objects.none()
            )


    # ========================================================
    # RECIPIENT VALIDATION
    # ========================================================

    def clean_recipient(self):
        """
        Prevent self-messaging at the validation layer as well
        as through the filtered select field.
        """

        recipient = self.cleaned_data.get(
            "recipient"
        )


        if (
            self.sender
            and
            recipient
            and
            recipient.pk == self.sender.pk
        ):

            raise forms.ValidationError(
                "You cannot start a conversation with yourself."
            )


        return recipient


    # ========================================================
    # MESSAGE VALIDATION
    # ========================================================

    def clean_body(self):
        """
        Remove unnecessary surrounding whitespace and prevent
        an empty/whitespace-only first message.
        """

        body = self.cleaned_data.get(
            "body",
            "",
        ).strip()


        if not body:

            raise forms.ValidationError(
                "Please enter a message."
            )


        return body


# ============================================================
# 4. MESSAGE REPLY FORM
# ============================================================

class MessageReplyForm(forms.ModelForm):
    """
    Add a message to an existing conversation.

    A reply does not ask the user to select:

    - a recipient
    - a subject

    The conversation already identifies the participants.

    The view is responsible for assigning:

        message.sender
        message.conversation
    """

    class Meta:

        model = PrivateMessage

        fields = [
            "body",
        ]

        widgets = {

            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Write a message..."
                    ),
                    "aria-label": (
                        "Write a message"
                    ),
                }
            ),

        }

        labels = {

            "body": "",

        }


    # ========================================================
    # MESSAGE VALIDATION
    # ========================================================

    def clean_body(self):
        """
        Prevent blank or whitespace-only chat messages.
        """

        body = self.cleaned_data.get(
            "body",
            "",
        ).strip()


        if not body:

            raise forms.ValidationError(
                "Please enter a message."
            )


        return body