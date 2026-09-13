# ============================================================
# COMMUNITY - FORMS
# ============================================================

from django import forms
from django.contrib.auth import get_user_model

from .models import CommunityPost, PrivateMessage


User = get_user_model()


# ============================================================
# COMMUNITY POST FORM
# ============================================================

class CommunityPostForm(forms.ModelForm):

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
                    "placeholder": "Optional ticker e.g. AAPL",
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


    def clean_ticker(self):

        ticker = self.cleaned_data.get("ticker")

        if ticker:

            ticker = ticker.strip().upper()

        return ticker


# ============================================================
# PRIVATE MESSAGE FORM
# ============================================================

class PrivateMessageForm(forms.ModelForm):

    class Meta:

        model = PrivateMessage

        fields = [
            "recipient",
            "subject",
            "body",
        ]

        widgets = {

            "recipient": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Message subject",
                }
            ),

            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Write your message...",
                }
            ),
        }


    def __init__(self, *args, sender=None, **kwargs):

        super().__init__(*args, **kwargs)

        # Prevent the user from messaging themselves.
        if sender:

            self.fields["recipient"].queryset = (
                User.objects
                .exclude(pk=sender.pk)
                .order_by("username")
            )