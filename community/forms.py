# ============================================================
# COMMUNITY - FORMS
# ============================================================
#
# WHAT IS THIS FILE FOR?
#
# This file defines the Django forms used by the Community app.
#
# It controls:
#
# 1. Creating Community Pulse posts
# 2. Starting a private conversation
# 3. Sending the first private message
# 4. Replying inside an existing conversation
# 5. Validating information entered by users
#
# ============================================================
# DJANGO FRAMEWORK MAPPING
# ============================================================
#
# COMMUNITY POST FLOW:
#
# Browser / Template
#     ↓
# CommunityPostForm
#     ↓
# community/views.py
#     ↓
# CommunityPost model
#     ↓
# Django ORM
#     ↓
# PostgreSQL
#
#
# PRIVATE CONVERSATION FLOW:
#
# Browser / Template
#     ↓
# NewConversationForm
#     ↓
# community/views.py
#     ↓
# Conversation
#     ↓
# First PrivateMessage
#     ↓
# Django ORM
#     ↓
# PostgreSQL
#
#
# EXISTING CONVERSATION FLOW:
#
# Existing Conversation
#     ↓
# MessageReplyForm
#     ↓
# community/views.py
#     ↓
# PrivateMessage
#     ↓
# Django ORM
#     ↓
# PostgreSQL
#
# ============================================================
# HOW THIS CONNECTS TO MY PROGRAMMING LECTURE
# ============================================================
#
# Programming Language Features / Concepts used here:
#
# IMPORTS / MODULES
#     Reuse Django and MarketPulse code from other files.
#
# VARIABLES
#     Store objects and temporary values such as User,
#     ticker, recipient and body.
#
# CLASSES
#     CommunityPostForm, NewConversationForm and
#     MessageReplyForm define reusable form objects.
#
# INHERITANCE
#     forms.ModelForm and forms.Form provide existing Django
#     behaviour that our own classes build upon.
#
# OBJECTS
#     Forms, fields, widgets, users and model records are
#     Python objects created from classes.
#
# METHODS
#     clean_ticker(), __init__(), clean_recipient() and
#     clean_body() define behaviour inside classes.
#
# PARAMETERS / ARGUMENTS
#     Values such as sender=None, *args and **kwargs are
#     passed into functions and methods.
#
# LISTS
#     fields = [...] stores an ordered collection of field
#     names.
#
# DICTIONARIES
#     widgets = {...}, attrs = {...} and labels = {...}
#     store key/value pairs.
#
# CONDITIONALS
#     if statements make decisions based on form data.
#
# BOOLEAN LOGIC
#     and combines several True/False conditions.
#
# METHOD CHAINING
#     User.objects.exclude(...).order_by(...) applies several
#     operations to the same Django QuerySet.
#
# VALIDATION
#     clean_* methods check and normalise user input.
#
# EXCEPTIONS
#     forms.ValidationError stops invalid form data.
#
# RETURN VALUES
#     return sends cleaned values back to Django's form
#     validation system.
#
# OBJECT-ORIENTED PROGRAMMING
#     Classes contain both data definitions and behaviour.
#
# ============================================================
# IMPORTANT PRIVATE-MESSAGING DESIGN
# ============================================================
#
# Private messaging follows a conversation/thread model.
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

# ============================================================
# 1. IMPORTS
# ============================================================

from django import forms  # IMPORT: brings Django's forms module into this file.
from django.contrib.auth import get_user_model  # IMPORT: gets the user model configured by this Django project.
from .models import (  # RELATIVE IMPORT: imports models from this Community app.
    CommunityPost,  # CLASS: database model representing a Community Pulse post.
    PrivateMessage,  # CLASS: database model representing a private message.
)

# ============================================================
# 2. USER MODEL
# ============================================================
#
# MarketPulse uses the custom user model configured through:
#
# settings.AUTH_USER_MODEL
#
# get_user_model() ensures this form works with that model
# rather than assuming Django's default User model.
#
# PROGRAMMING CONCEPT:
# Variable assignment stores the returned class in User.
# ============================================================

User = get_user_model()  # VARIABLE + FUNCTION CALL: stores MarketPulse's configured user model in User.

# ============================================================
# 3. COMMUNITY POST FORM
# ============================================================
#
# PURPOSE:
#
# Creates and validates the form used to publish posts to the
# Community Pulse feed.
#
# DJANGO:
#
# CommunityPostForm
#     inherits from
# forms.ModelForm
#     and connects to
# CommunityPost
#
# PROGRAMMING CONCEPTS:
#
# - class
# - inheritance
# - nested class
# - lists
# - dictionaries
# - method calls
# - validation
# - conditionals
# - string methods
# - return values
#
# ============================================================

class CommunityPostForm(forms.ModelForm):  # CLASS + INHERITANCE: creates a form class using Django ModelForm behaviour.
    """
    Form used by authenticated MarketPulse users to publish
    posts to the Community Pulse feed.

    Supported post information:

    - post type
    - optional market ticker
    - post content
    """

    # ========================================================
    # 3.1 MODELFORM CONFIGURATION
    # ========================================================

    class Meta:  # NESTED CLASS: Django reads Meta to learn how this ModelForm should work.
        model = CommunityPost  # CLASS VARIABLE: connects this form to the CommunityPost database model.
        fields = [  # LIST: tells Django which CommunityPost model fields should appear in the form.
            "post_type",  # STRING: includes the post_type field.
            "ticker",  # STRING: includes the ticker field.
            "content",  # STRING: includes the content field.
        ]
        widgets = {  # DICTIONARY: maps each form field to a particular HTML widget.
            "post_type": forms.Select(  # OBJECT CREATION: creates a dropdown widget for post_type.
                attrs={  # DICTIONARY: contains HTML attributes for the dropdown.
                    "class": "form-select",  # KEY/VALUE PAIR: gives the widget a Bootstrap CSS class.
                }
            ),
            "ticker": forms.TextInput(  # OBJECT CREATION: creates a text input widget for the ticker.
                attrs={  # DICTIONARY: contains HTML attributes for the ticker input.
                    "class": "form-control",  # KEY/VALUE PAIR: applies Bootstrap form styling.
                    "placeholder": (  # STRING VALUE: defines helper text shown inside the input.
                        "Optional ticker e.g. AAPL"
                    ),
                    "autocomplete": "off",  # KEY/VALUE PAIR: tells the browser not to autocomplete this field.
                }
            ),
            "content": forms.Textarea(  # OBJECT CREATION: creates a multi-line text area for the post content.
                attrs={  # DICTIONARY: contains HTML attributes for the textarea.
                    "class": "form-control",  # KEY/VALUE PAIR: applies Bootstrap styling.
                    "rows": 4,  # INTEGER: makes the textarea four rows high initially.
                    "placeholder": (  # STRING VALUE: provides guidance about what the user can write.
                        "Share a market update, warning, "
                        "risk observation or trading discussion..."
                    ),
                }
            ),
        }

    # ========================================================
    # 3.2 NORMALISE OPTIONAL TICKER
    # ========================================================
    #
    # Django automatically calls clean_ticker() while the form
    # is being validated because the method follows the naming
    # convention:
    #
    # clean_<field_name>()
    #
    # Example:
    #
    # aapl
    #     ↓
    # strip()
    #     ↓
    # aapl
    #     ↓
    # upper()
    #     ↓
    # AAPL
    #
    # ========================================================

    def clean_ticker(self):  # METHOD: defines custom validation/cleaning behaviour for the ticker field.
        """
        Convert a supplied ticker to uppercase.

        Example:

            aapl
                ↓
            AAPL
        """

        ticker = self.cleaned_data.get(  # VARIABLE + METHOD CALL: gets the validated ticker value from Django's cleaned_data dictionary.
            "ticker"  # STRING KEY: identifies which cleaned form field we want.
        )

        if ticker:  # CONDITIONAL: only performs the following cleaning if a ticker was supplied.
            ticker = (  # ASSIGNMENT: replaces ticker with its cleaned version.
                ticker  # VARIABLE: starts with the ticker entered by the user.
                .strip()  # METHOD: removes spaces from the beginning and end.
                .upper()  # METHOD CHAINING: converts the remaining text to uppercase.
            )

        return ticker  # RETURN VALUE: gives the cleaned ticker back to Django.

# ============================================================
# 4. NEW CONVERSATION FORM
# ============================================================
#
# PURPOSE:
#
# Used when one authenticated MarketPulse user starts a new
# one-to-one conversation with another user.
#
# The form contains:
#
# recipient
# body
#
# This is forms.Form rather than forms.ModelForm because this
# form represents the action of starting a conversation rather
# than directly representing one complete database model.
#
# PROGRAMMING CONCEPTS:
#
# - class
# - inheritance
# - objects
# - class attributes
# - method overriding
# - positional arguments
# - keyword arguments
# - default parameters
# - conditionals
# - QuerySets
# - comparison operators
# - Boolean operators
# - exceptions
#
# ============================================================

class NewConversationForm(forms.Form):  # CLASS + INHERITANCE: creates a standard Django form that inherits forms.Form behaviour.
    """
    Start a new one-to-one private conversation.

    The user selects another MarketPulse user only once.

    After the conversation exists, further communication uses
    MessageReplyForm and does not require another recipient
    selection.
    """

    # --------------------------------------------------------
    # 4.1 RECIPIENT FIELD
    # --------------------------------------------------------

    recipient = forms.ModelChoiceField(  # CLASS ATTRIBUTE + OBJECT: creates a dropdown whose choices are User model objects.
        queryset=User.objects.none(),  # KEYWORD ARGUMENT: begins with an empty User QuerySet for safety.
        label="Start a chat with",  # STRING: defines the human-readable field label.
        empty_label="Choose a MarketPulse user",  # STRING: defines the default empty dropdown option.
        widget=forms.Select(  # OBJECT CREATION: creates the HTML select/dropdown widget.
            attrs={  # DICTIONARY: contains HTML attributes for the dropdown.
                "class": "form-select",  # KEY/VALUE PAIR: adds Bootstrap select styling.
                "aria-label": (  # ACCESSIBILITY ATTRIBUTE: gives screen readers a description of this control.
                    "Choose a MarketPulse user"
                ),
            }
        ),
    )

    # --------------------------------------------------------
    # 4.2 FIRST MESSAGE FIELD
    # --------------------------------------------------------

    body = forms.CharField(  # CLASS ATTRIBUTE + OBJECT: creates a text field for the first private message.
        max_length=3000,  # INTEGER ARGUMENT: limits the message to 3000 characters.
        label="Message",  # STRING: gives the field a visible label.
        widget=forms.Textarea(  # OBJECT CREATION: displays the CharField as a multi-line textarea.
            attrs={  # DICTIONARY: contains HTML attributes for the textarea.
                "class": "form-control",  # KEY/VALUE PAIR: applies Bootstrap form styling.
                "rows": 4,  # INTEGER: makes the textarea four rows high initially.
                "placeholder": (  # STRING: provides guidance inside the empty textarea.
                    "Write your first message..."
                ),
                "aria-label": (  # ACCESSIBILITY ATTRIBUTE: describes the field for assistive technology.
                    "Write your first message"
                ),
            }
        ),
    )

    # ========================================================
    # 4.3 FORM INITIALISATION
    # ========================================================
    #
    # __init__ is Python's object initialisation method.
    #
    # This version extends Django's normal Form __init__()
    # behaviour by accepting an additional sender parameter.
    #
    # *args
    #     collects extra positional arguments.
    #
    # sender=None
    #     is an optional keyword parameter.
    #
    # **kwargs
    #     collects extra keyword arguments.
    #
    # ========================================================

    def __init__(  # SPECIAL METHOD: runs whenever a NewConversationForm object is created.
        self,  # SELF: refers to the specific form object currently being created.
        *args,  # *ARGS: collects any additional positional arguments.
        sender=None,  # DEFAULT PARAMETER: sender is optional and defaults to None.
        **kwargs,  # **KWARGS: collects additional named arguments.
    ):
        """
        Restrict the recipient list so the current user cannot
        start a conversation with themselves.
        """

        super().__init__(  # INHERITANCE: calls the parent forms.Form initialisation method.
            *args,  # ARGUMENT UNPACKING: passes the collected positional arguments to Django.
            **kwargs,  # KEYWORD UNPACKING: passes the collected keyword arguments to Django.
        )

        # Store the authenticated sender so validation can also
        # check against self-messaging.
        self.sender = sender  # INSTANCE ATTRIBUTE: saves the sender on this particular form object.

        if sender:  # CONDITIONAL: checks whether an authenticated sender was supplied.
            self.fields[  # OBJECT ATTRIBUTE + DICTIONARY ACCESS: accesses Django's collection of fields.
                "recipient"  # STRING KEY: selects the recipient field.
            ].queryset = (  # ASSIGNMENT: replaces the recipient field's available database choices.
                User.objects  # DJANGO ORM MANAGER: begins a database query using the User model.
                .exclude(  # QUERYSET METHOD: removes a user from the possible results.
                    pk=sender.pk  # KEYWORD ARGUMENT: excludes the user whose primary key matches the sender.
                )
                .order_by(  # QUERYSET METHOD CHAINING: sorts the remaining users.
                    "username"  # STRING: sorts users alphabetically by username.
                )
            )
        else:  # CONDITIONAL BRANCH: runs when no sender was supplied.
            # Do not expose all users if the form was created
            # without an authenticated sender.
            self.fields[  # OBJECT ATTRIBUTE + DICTIONARY ACCESS: accesses the form's fields.
                "recipient"  # STRING KEY: selects the recipient field.
            ].queryset = (  # ASSIGNMENT: controls which User records appear in the dropdown.
                User.objects.none()  # DJANGO ORM: returns an empty QuerySet.
            )

    # ========================================================
    # 4.4 RECIPIENT VALIDATION
    # ========================================================
    #
    # This protects against self-messaging even if someone
    # bypassed or manipulated the dropdown in the browser.
    #
    # ========================================================

    def clean_recipient(self):  # METHOD: defines custom validation for the recipient field.
        """
        Prevent self-messaging at the validation layer as well
        as through the filtered select field.
        """

        recipient = self.cleaned_data.get(  # VARIABLE + METHOD CALL: retrieves the validated recipient object.
            "recipient"  # STRING KEY: identifies the recipient field.
        )

        if (  # CONDITIONAL: begins a multi-part Boolean test.
            self.sender  # BOOLEAN TEST: confirms there is a sender.
            and  # BOOLEAN OPERATOR: requires the next condition to also be True.
            recipient  # BOOLEAN TEST: confirms a recipient exists.
            and  # BOOLEAN OPERATOR: requires all three conditions to be True.
            recipient.pk == self.sender.pk  # COMPARISON: checks whether sender and recipient have the same database primary key.
        ):
            raise forms.ValidationError(  # EXCEPTION: marks the form as invalid and displays an error message.
                "You cannot start a conversation with yourself."  # STRING: explains the validation problem to the user.
            )

        return recipient  # RETURN VALUE: sends the valid recipient object back to Django.

    # ========================================================
    # 4.5 FIRST MESSAGE VALIDATION
    # ========================================================

    def clean_body(self):  # METHOD: provides custom validation for the first-message body field.
        """
        Remove unnecessary surrounding whitespace and prevent
        an empty/whitespace-only first message.
        """

        body = self.cleaned_data.get(  # VARIABLE + METHOD CALL: retrieves the cleaned message value.
            "body",  # STRING KEY: identifies the body field.
            "",  # DEFAULT VALUE: uses an empty string if body does not exist.
        ).strip()  # STRING METHOD: removes whitespace from both ends of the message.

        if not body:  # CONDITIONAL + NOT OPERATOR: checks whether the cleaned message is empty.
            raise forms.ValidationError(  # EXCEPTION: stops validation because an empty message is invalid.
                "Please enter a message."  # STRING: error displayed to the user.
            )

        return body  # RETURN VALUE: sends the cleaned message back to Django.

# ============================================================
# 5. MESSAGE REPLY FORM
# ============================================================
#
# PURPOSE:
#
# Adds a PrivateMessage to an already existing conversation.
#
# The form only asks for:
#
# body
#
# It does NOT ask for:
#
# recipient
# subject
#
# because the conversation already identifies the people who
# are communicating.
#
# FRAMEWORK RESPONSIBILITY:
#
# MessageReplyForm
#     validates message body
#
# community/views.py
#     assigns sender
#     assigns conversation
#
# PrivateMessage
#     stores the message
#
# Django ORM
#     writes the record
#
# PostgreSQL
#     permanently stores the record
#
# PROGRAMMING CONCEPTS:
#
# - ModelForm
# - inheritance
# - nested classes
# - lists
# - dictionaries
# - methods
# - validation
# - exceptions
# - return values
#
# ============================================================

class MessageReplyForm(forms.ModelForm):  # CLASS + INHERITANCE: creates a form connected directly to a Django model.
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

    # ========================================================
    # 5.1 MODELFORM CONFIGURATION
    # ========================================================

    class Meta:  # NESTED CLASS: gives Django configuration information about this ModelForm.
        model = PrivateMessage  # CLASS VARIABLE: connects the form to the PrivateMessage database model.
        fields = [  # LIST: controls which model fields the user is allowed to edit through this form.
            "body",  # STRING: only the message body is exposed to the user.
        ]
        widgets = {  # DICTIONARY: maps form fields to HTML widgets.
            "body": forms.Textarea(  # OBJECT CREATION: represents body as a multi-line textarea.
                attrs={  # DICTIONARY: contains HTML attributes for the textarea.
                    "class": "form-control",  # KEY/VALUE PAIR: applies Bootstrap form styling.
                    "rows": 3,  # INTEGER: makes the textarea three rows high initially.
                    "placeholder": (  # STRING: displays guidance when the textarea is empty.
                        "Write a message..."
                    ),
                    "aria-label": (  # ACCESSIBILITY ATTRIBUTE: describes the control for assistive technologies.
                        "Write a message"
                    ),
                }
            ),
        }
        labels = {  # DICTIONARY: customises labels shown by Django.
            "body": "",  # EMPTY STRING: hides the visible body label.
        }

    # ========================================================
    # 5.2 MESSAGE VALIDATION
    # ========================================================

    def clean_body(self):  # METHOD: defines custom validation for the PrivateMessage body field.
        """
        Prevent blank or whitespace-only chat messages.
        """

        body = self.cleaned_data.get(  # VARIABLE + METHOD CALL: gets the validated body value from cleaned_data.
            "body",  # STRING KEY: identifies the message body field.
            "",  # DEFAULT VALUE: returns an empty string when no body exists.
        ).strip()  # STRING METHOD: removes unnecessary spaces around the message.

        if not body:  # CONDITIONAL + BOOLEAN OPERATOR: checks whether the cleaned message is empty.
            raise forms.ValidationError(  # EXCEPTION: tells Django the form data is invalid.
                "Please enter a message."  # STRING: validation message shown to the user.
            )

        return body  # RETURN VALUE: returns the cleaned valid message to Django.