# ============================================================
# COMMUNITY - VIEWS
# ============================================================
#
# MARKETPULSE COMMUNITY ARCHITECTURE
#
# Community Feed
#       ↓
# CommunityPost
#       ↓
# Django ORM
#       ↓
# PostgreSQL / Neon
#
#
# Private Messaging
#       ↓
# Conversation
#       ↓
# Participants
#       ↓
# PrivateMessage
#       ↓
# Django ORM
#       ↓
# PostgreSQL / Neon
#
#
# CONVERSATION WORKFLOW:
#
# User
#     ↓
# Inbox
#     ↓
# Conversation List
#     ↓
# Select Conversation
#     ↓
# Complete Message Thread
#     ↓
# Reply
#     ↓
# Message saved to same Conversation
#
#
# TRANSITION ARCHITECTURE:
#
# PrivateMessage currently still contains:
#
# - conversation
# - sender
# - recipient
# - subject
# - body
# - created_at
# - is_read
#
#
# recipient and subject are retained temporarily so existing
# MarketPulse messages and older functionality remain
# compatible while the application moves from email-style
# messages to continuous conversation threads.
#
#
# IMPORTANT:
#
# Conversation.updated_at uses auto_now=True, but saving a
# related PrivateMessage does not automatically save the
# Conversation itself.
#
# Therefore this module explicitly updates updated_at whenever
# a new message is sent.
#
# This allows the most recently active conversation to appear
# first in the Inbox.
#
# ============================================================


# ============================================================
# 1. DJANGO IMPORTS
# ============================================================

from django.contrib import messages

from django.contrib.auth.decorators import (
    login_required,
)

from django.db import transaction

from django.db.models import (
    Prefetch,
    Q,
)

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from django.utils import timezone


# ============================================================
# 2. COMMUNITY IMPORTS
# ============================================================

from .forms import (
    CommunityPostForm,
    MessageReplyForm,
    NewConversationForm,
)

from .models import (
    CommunityPost,
    Conversation,
    PrivateMessage,
)


# ============================================================
# 3. PRIVATE HELPER FUNCTIONS
# ============================================================


# ============================================================
# 3.1 GET OTHER PARTICIPANT
# ============================================================

def _get_other_participant(
    conversation,
    current_user,
):
    """
    Return the participant other than current_user.

    MarketPulse currently supports direct one-to-one
    conversations.

    Example:

        Conversation
            ↓
        User1 + User2

    If User1 is the authenticated user:

        current_user = User1

    this function returns:

        User2

    If no other participant exists, return None.
    """

    if (
        conversation is None
        or current_user is None
        or not getattr(
            current_user,
            "pk",
            None,
        )
    ):
        return None


    return (
        conversation
        .participants
        .exclude(
            pk=current_user.pk,
        )
        .order_by(
            "username",
        )
        .first()
    )


# ============================================================
# 3.2 FIND EXISTING DIRECT CONVERSATION
# ============================================================

def _find_direct_conversation(
    user,
    other_user,
):
    """
    Find an existing one-to-one conversation containing
    exactly the supplied two users.

    Example:

        User1 ↔ User2

    If that conversation already exists, reuse it rather than
    creating another duplicate conversation.

    This keeps one continuous chat thread between the same
    pair of MarketPulse users.
    """

    # --------------------------------------------------------
    # Validate users
    # --------------------------------------------------------

    if (
        user is None
        or other_user is None
        or not getattr(
            user,
            "pk",
            None,
        )
        or not getattr(
            other_user,
            "pk",
            None,
        )
        or user.pk == other_user.pk
    ):
        return None


    # --------------------------------------------------------
    # Find conversations containing both users
    # --------------------------------------------------------

    candidates = (
        Conversation.objects

        .filter(
            participants=user,
        )

        .filter(
            participants=other_user,
        )

        .prefetch_related(
            "participants",
        )

        .distinct()
    )


    # --------------------------------------------------------
    # Confirm conversation contains exactly these two users
    # --------------------------------------------------------

    for conversation in candidates:

        participant_ids = {
            participant.pk
            for participant
            in conversation.participants.all()
        }


        if participant_ids == {
            user.pk,
            other_user.pk,
        }:

            return conversation


    return None


# ============================================================
# 3.3 COMPATIBILITY SUBJECT
# ============================================================

def _conversation_subject(
    conversation,
    other_user,
):
    """
    Return an internal compatibility subject.

    The new conversation interface no longer asks the user to
    enter a subject for every message.

    However:

        PrivateMessage.subject

    still exists in the transitional database model.

    Therefore MarketPulse creates an internal subject so older
    code and existing database structure remain compatible.
    """

    # --------------------------------------------------------
    # Reuse an existing conversation subject where possible
    # --------------------------------------------------------

    existing_message = (
        PrivateMessage.objects

        .filter(
            conversation=conversation,
        )

        .exclude(
            subject="",
        )

        .order_by(
            "-created_at",
        )

        .first()
    )


    if (
        existing_message
        and existing_message.subject
    ):

        return existing_message.subject[:150]


    # --------------------------------------------------------
    # Otherwise generate a default subject
    # --------------------------------------------------------

    if other_user:

        return (
            f"Conversation with "
            f"{other_user.username}"
        )[:150]


    return "MarketPulse Conversation"


# ============================================================
# 3.4 UPDATE CONVERSATION ACTIVITY
# ============================================================

def _touch_conversation(
    conversation,
):
    """
    Update Conversation.updated_at whenever a new message is
    created.

    This ensures the most recently active conversation appears
    at the top of the Inbox.
    """

    if (
        conversation is None
        or conversation.pk is None
    ):

        return


    current_time = timezone.now()


    Conversation.objects.filter(
        pk=conversation.pk,
    ).update(
        updated_at=current_time,
    )


    # --------------------------------------------------------
    # Keep current Python object synchronised
    # --------------------------------------------------------

    conversation.updated_at = (
        current_time
    )


# ============================================================
# 4. COMMUNITY FEED
# ============================================================

@login_required
def feed(request):
    """
    Display the MarketPulse Community Feed and allow an
    authenticated user to publish a CommunityPost.

    Framework flow:

        Browser
            ↓
        community:feed
            ↓
        feed()
            ↓
        CommunityPostForm
            ↓
        CommunityPost
            ↓
        PostgreSQL
            ↓
        community/feed.html
    """

    # ========================================================
    # FETCH COMMUNITY POSTS
    # ========================================================

    posts = (
        CommunityPost.objects

        .select_related(
            "author",
        )

        .all()
    )


    # ========================================================
    # CREATE COMMUNITY POST
    # ========================================================

    if request.method == "POST":

        form = CommunityPostForm(
            request.POST,
        )


        if form.is_valid():

            post = form.save(
                commit=False,
            )


            post.author = (
                request.user
            )


            post.save()


            messages.success(
                request,
                (
                    "Your community post "
                    "has been published."
                ),
            )


            # ------------------------------------------------
            # POST / REDIRECT / GET
            #
            # Prevent duplicate submission if browser refreshes.
            # ------------------------------------------------

            return redirect(
                "community:feed",
            )


    # ========================================================
    # GET - EMPTY FORM
    # ========================================================

    else:

        form = (
            CommunityPostForm()
        )


    # ========================================================
    # RENDER FEED
    # ========================================================

    return render(
        request,
        "community/feed.html",
        {

            "posts":
                posts,

            "form":
                form,

        },
    )


# ============================================================
# 5. INBOX / CONVERSATION LIST
# ============================================================

@login_required
def inbox(request):
    """
    Display all private conversations belonging to the
    authenticated user.

    Previous architecture:

        Received Messages
        Sent Messages


    Updated architecture:

        Conversations
            ↓
        User2
        User3
        User4


    Each Conversation is prepared with:

        conversation.other_user
        conversation.last_message
        conversation.unread_count

    These values are used by:

        community/templates/community/inbox.html
    """

    # ========================================================
    # FETCH USER CONVERSATIONS
    # ========================================================

    conversations = (
        Conversation.objects

        # ----------------------------------------------------
        # SECURITY
        #
        # Only conversations containing the authenticated
        # user are returned.
        # ----------------------------------------------------

        .filter(
            participants=request.user,
        )

        # ----------------------------------------------------
        # Load related data efficiently
        # ----------------------------------------------------

        .prefetch_related(

            "participants",

            Prefetch(
                "messages",

                queryset=(
                    PrivateMessage.objects

                    .select_related(
                        "sender",
                        "recipient",
                    )

                    # -----------------------------------------
                    # Inbox needs newest message first
                    # -----------------------------------------

                    .order_by(
                        "-created_at",
                    )
                ),

                to_attr=
                    "inbox_messages",
            ),

        )

        # ----------------------------------------------------
        # Most recently active conversation first
        # ----------------------------------------------------

        .order_by(
            "-updated_at",
        )

        .distinct()
    )


    # ========================================================
    # PREPARE CONVERSATION DATA FOR TEMPLATE
    # ========================================================

    conversation_list = []


    for conversation in conversations:


        # ----------------------------------------------------
        # OTHER PARTICIPANT
        # ----------------------------------------------------

        conversation.other_user = (
            _get_other_participant(
                conversation,
                request.user,
            )
        )


        # ----------------------------------------------------
        # PREFETCHED MESSAGES
        #
        # Already ordered:
        #
        # newest
        #   ↓
        # oldest
        # ----------------------------------------------------

        prefetched_messages = getattr(
            conversation,
            "inbox_messages",
            [],
        )


        # ----------------------------------------------------
        # LAST MESSAGE
        # ----------------------------------------------------

        conversation.last_message = (
            prefetched_messages[0]
            if prefetched_messages
            else None
        )


        # ----------------------------------------------------
        # UNREAD INCOMING MESSAGE COUNT
        # ----------------------------------------------------

        conversation.unread_count = sum(

            1

            for message
            in prefetched_messages

            if (
                message.recipient_id
                ==
                request.user.pk

                and

                not message.is_read
            )

        )


        conversation_list.append(
            conversation,
        )


    # ========================================================
    # LEGACY MESSAGE COUNT
    # ========================================================
    #
    # Existing PrivateMessage records created before the
    # Conversation model may still contain:
    #
    # conversation = NULL
    #
    # They remain safely stored in the database until the
    # migration step assigns them to Conversation records.
    # ========================================================

    legacy_message_count = (
        PrivateMessage.objects

        .filter(
            conversation__isnull=True,
        )

        .filter(

            Q(
                sender=request.user,
            )

            |

            Q(
                recipient=request.user,
            )

        )

        .count()
    )


    # ========================================================
    # TOTAL UNREAD MESSAGES
    # ========================================================

    total_unread = sum(

        conversation.unread_count

        for conversation
        in conversation_list

    )


    # ========================================================
    # RENDER INBOX
    # ========================================================

    return render(
        request,
        "community/inbox.html",
        {

            "conversations":
                conversation_list,

            "total_unread":
                total_unread,

            "legacy_message_count":
                legacy_message_count,

        },
    )


# ============================================================
# 6. START NEW CONVERSATION
# ============================================================

@login_required
def new_conversation(request):
    """
    Start a new direct conversation with another MarketPulse
    user.

    If the two users already have a direct conversation:

        existing Conversation
            ↓
        reuse it
            ↓
        add message

    Otherwise:

        create Conversation
            ↓
        add both participants
            ↓
        create first PrivateMessage


    This prevents duplicate chat threads between the same
    two users.
    """

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        form = NewConversationForm(
            request.POST,
            sender=request.user,
        )


        if form.is_valid():

            recipient = (
                form.cleaned_data[
                    "recipient"
                ]
            )


            body = (
                form.cleaned_data[
                    "body"
                ]
                .strip()
            )


            # =================================================
            # DEFENCE-IN-DEPTH:
            # PREVENT SELF-MESSAGING
            # =================================================
            #
            # NewConversationForm already performs this check.
            #
            # The view checks it again so the business rule is
            # also protected here.
            # =================================================

            if (
                recipient.pk
                ==
                request.user.pk
            ):

                form.add_error(
                    "recipient",
                    (
                        "You cannot start a "
                        "conversation with yourself."
                    ),
                )


            # =================================================
            # PREVENT EMPTY MESSAGE
            # =================================================

            elif not body:

                form.add_error(
                    "body",
                    "Please enter a message.",
                )


            # =================================================
            # CREATE / REUSE CONVERSATION
            # =================================================

            else:

                with transaction.atomic():


                    # -----------------------------------------
                    # Find existing one-to-one thread
                    # -----------------------------------------

                    conversation = (
                        _find_direct_conversation(
                            request.user,
                            recipient,
                        )
                    )


                    conversation_created = (
                        conversation is None
                    )


                    # -----------------------------------------
                    # Create new conversation when necessary
                    # -----------------------------------------

                    if conversation_created:

                        conversation = (
                            Conversation.objects.create()
                        )


                        conversation.participants.add(
                            request.user,
                            recipient,
                        )


                    # -----------------------------------------
                    # Generate compatibility subject
                    # -----------------------------------------

                    subject = (
                        _conversation_subject(
                            conversation,
                            recipient,
                        )
                    )


                    # -----------------------------------------
                    # Save first/new message
                    # -----------------------------------------

                    PrivateMessage.objects.create(

                        conversation=
                            conversation,

                        sender=
                            request.user,

                        recipient=
                            recipient,

                        subject=
                            subject,

                        body=
                            body,

                    )


                    # -----------------------------------------
                    # Update conversation activity
                    # -----------------------------------------

                    _touch_conversation(
                        conversation,
                    )


                # =================================================
                # SUCCESS MESSAGE
                # =================================================

                if conversation_created:

                    messages.success(
                        request,
                        (
                            f"Conversation with "
                            f"{recipient.username} "
                            f"has been started."
                        ),
                    )

                else:

                    messages.success(
                        request,
                        (
                            f"Message sent to "
                            f"{recipient.username}."
                        ),
                    )


                # =================================================
                # OPEN CONVERSATION THREAD
                # =================================================

                return redirect(
                    "community:conversation_detail",
                    pk=conversation.pk,
                )


    # ========================================================
    # GET
    # ========================================================

    else:

        form = NewConversationForm(
            sender=request.user,
        )


    # ========================================================
    # RENDER NEW-CONVERSATION FORM
    # ========================================================

    return render(
        request,
        "community/compose_message.html",
        {

            "form":
                form,

            "conversation_mode":
                True,

        },
    )


# ============================================================
# 7. CONVERSATION THREAD
# ============================================================

@login_required
def conversation_detail(
    request,
    pk,
):
    """
    Display one complete private Conversation and process
    replies.

    SECURITY:

    The Conversation query is restricted to:

        participants=request.user

    Therefore an authenticated user cannot manually change:

        /community/inbox/conversation/5/

    to:

        /community/inbox/conversation/6/

    and read Conversation 6 unless they are actually one of
    its participants.
    """

    # ========================================================
    # AUTHORISED CONVERSATION QUERYSET
    # ========================================================

    conversation_queryset = (
        Conversation.objects

        .filter(
            participants=request.user,
        )

        .prefetch_related(
            "participants",
        )

        .distinct()
    )


    # ========================================================
    # LOAD CONVERSATION
    # ========================================================

    conversation = get_object_or_404(
        conversation_queryset,
        pk=pk,
    )


    # ========================================================
    # DETERMINE OTHER PARTICIPANT
    # ========================================================

    other_user = (
        _get_other_participant(
            conversation,
            request.user,
        )
    )


    # ========================================================
    # CONVERSATION INTEGRITY
    # ========================================================

    if other_user is None:

        messages.error(
            request,
            (
                "This conversation does not have "
                "another participant."
            ),
        )


        return redirect(
            "community:inbox",
        )


    # ========================================================
    # MARK INCOMING MESSAGES AS READ
    # ========================================================
    #
    # Only messages addressed to request.user are updated.
    #
    # The other participant's outgoing messages remain
    # unchanged.
    # ========================================================

    (
        PrivateMessage.objects

        .filter(
            conversation=conversation,
            recipient=request.user,
            is_read=False,
        )

        .update(
            is_read=True,
        )
    )


    # ========================================================
    # PROCESS REPLY
    # ========================================================

    if request.method == "POST":

        reply_form = MessageReplyForm(
            request.POST,
        )


        if reply_form.is_valid():

            body = (
                reply_form.cleaned_data[
                    "body"
                ]
                .strip()
            )


            # ------------------------------------------------
            # Defence-in-depth empty-message check
            # ------------------------------------------------

            if not body:

                reply_form.add_error(
                    "body",
                    "Please enter a message.",
                )


            else:

                with transaction.atomic():


                    # -----------------------------------------
                    # Compatibility subject
                    # -----------------------------------------

                    subject = (
                        _conversation_subject(
                            conversation,
                            other_user,
                        )
                    )


                    # -----------------------------------------
                    # Save reply into SAME Conversation
                    # -----------------------------------------

                    PrivateMessage.objects.create(

                        conversation=
                            conversation,

                        sender=
                            request.user,

                        recipient=
                            other_user,

                        subject=
                            subject,

                        body=
                            body,

                    )


                    # -----------------------------------------
                    # Move active thread to top of Inbox
                    # -----------------------------------------

                    _touch_conversation(
                        conversation,
                    )


                # ------------------------------------------------
                # POST / REDIRECT / GET
                #
                # Prevent duplicate message submission after a
                # browser refresh.
                # ------------------------------------------------

                return redirect(
                    "community:conversation_detail",
                    pk=conversation.pk,
                )


    # ========================================================
    # GET - EMPTY REPLY FORM
    # ========================================================

    else:

        reply_form = (
            MessageReplyForm()
        )


    # ========================================================
    # FETCH COMPLETE CONVERSATION HISTORY
    # ========================================================
    #
    # Chat messages display chronologically:
    #
    # oldest
    #   ↓
    # newest
    # ========================================================

    conversation_messages = (
        PrivateMessage.objects

        .filter(
            conversation=conversation,
        )

        .select_related(
            "sender",
            "recipient",
        )

        .order_by(
            "created_at",
        )
    )


    # ========================================================
    # RENDER CHAT THREAD
    # ========================================================
    #
    # message_thread.html receives:
    #
    # conversation
    # other_user
    # conversation_messages
    # reply_form
    #
    # ========================================================

    return render(
        request,
        "community/message_thread.html",
        {

            "conversation":
                conversation,

            "other_user":
                other_user,

            "conversation_messages":
                conversation_messages,

            "reply_form":
                reply_form,

        },
    )


# ============================================================
# 8. LEGACY COMPOSE MESSAGE COMPATIBILITY
# ============================================================

@login_required
def compose_message(request):
    """
    Preserve the original:

        community:compose_message

    route during the transition to the new Conversation
    architecture.

    Older templates may still link to:

        /community/inbox/compose/

    Instead of maintaining two separate messaging systems,
    that route now uses the same new-conversation workflow.

    Once all templates use:

        community:new_conversation

    this compatibility view can eventually be removed.
    """

    return new_conversation(
        request,
    )


# ============================================================
# 9. LEGACY MESSAGE DETAIL COMPATIBILITY
# ============================================================

@login_required
def message_detail(
    request,
    pk,
):
    """
    Preserve older links pointing to one individual
    PrivateMessage.

    Previous architecture:

        /community/inbox/<message_id>/


    New architecture:

        /community/inbox/conversation/<conversation_id>/


    If the old message has already been assigned to a
    Conversation, redirect the authorised user to the complete
    conversation thread.

    If conversation is still NULL, return the user to the Inbox
    until legacy messages have been migrated.
    """

    # ========================================================
    # AUTHORISED MESSAGE QUERYSET
    # ========================================================

    authorised_messages = (
        PrivateMessage.objects

        .select_related(
            "conversation",
            "sender",
            "recipient",
        )

        .filter(

            Q(
                sender=request.user,
            )

            |

            Q(
                recipient=request.user,
            )

            |

            Q(
                conversation__participants=request.user,
            )

        )

        .distinct()
    )


    # ========================================================
    # FETCH MESSAGE
    # ========================================================

    message_object = get_object_or_404(
        authorised_messages,
        pk=pk,
    )


    # ========================================================
    # LEGACY MESSAGE WITHOUT CONVERSATION
    # ========================================================

    if (
        message_object.conversation_id
        is None
    ):

        messages.info(
            request,
            (
                "This older message has not yet "
                "been assigned to a conversation "
                "thread."
            ),
        )


        return redirect(
            "community:inbox",
        )


    # ========================================================
    # DEFENCE-IN-DEPTH PARTICIPANT CHECK
    # ========================================================

    user_is_participant = (
        message_object
        .conversation
        .participants
        .filter(
            pk=request.user.pk,
        )
        .exists()
    )


    if not user_is_participant:

        messages.error(
            request,
            (
                "You do not have permission to "
                "open that conversation."
            ),
        )


        return redirect(
            "community:inbox",
        )


    # ========================================================
    # REDIRECT TO COMPLETE CONVERSATION
    # ========================================================

    return redirect(
        "community:conversation_detail",
        pk=message_object.conversation_id,
    )