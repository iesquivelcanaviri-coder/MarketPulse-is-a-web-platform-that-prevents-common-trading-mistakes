# ============================================================
# COMMUNITY - VIEWS
# ============================================================

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommunityPostForm, PrivateMessageForm
from .models import CommunityPost, PrivateMessage


# ============================================================
# COMMUNITY FEED
# ============================================================

@login_required
def feed(request):

    posts = CommunityPost.objects.select_related(
        "author"
    ).all()


    if request.method == "POST":

        form = CommunityPostForm(
            request.POST
        )

        if form.is_valid():

            post = form.save(
                commit=False
            )

            post.author = request.user

            post.save()

            messages.success(
                request,
                "Your community post has been published."
            )

            return redirect(
                "community:feed"
            )

    else:

        form = CommunityPostForm()


    return render(
        request,
        "community/feed.html",
        {
            "posts": posts,
            "form": form,
        }
    )


# ============================================================
# INBOX
# ============================================================

@login_required
def inbox(request):

    received_messages = (
        PrivateMessage.objects
        .filter(recipient=request.user)
        .select_related("sender")
    )

    sent_messages = (
        PrivateMessage.objects
        .filter(sender=request.user)
        .select_related("recipient")
    )


    return render(
        request,
        "community/inbox.html",
        {
            "received_messages": received_messages,
            "sent_messages": sent_messages,
        }
    )


# ============================================================
# MESSAGE DETAIL
# ============================================================

@login_required
def message_detail(request, pk):

    message_object = get_object_or_404(
        PrivateMessage,
        pk=pk,
        recipient=request.user,
    )


    if not message_object.is_read:

        message_object.is_read = True

        message_object.save(
            update_fields=["is_read"]
        )


    return render(
        request,
        "community/message_detail.html",
        {
            "message_object": message_object,
        }
    )


# ============================================================
# COMPOSE MESSAGE
# ============================================================

@login_required
def compose_message(request):

    if request.method == "POST":

        form = PrivateMessageForm(
            request.POST,
            sender=request.user,
        )

        if form.is_valid():

            message_object = form.save(
                commit=False
            )

            message_object.sender = request.user

            message_object.save()

            messages.success(
                request,
                "Your message has been sent."
            )

            return redirect(
                "community:inbox"
            )

    else:

        form = PrivateMessageForm(
            sender=request.user
        )


    return render(
        request,
        "community/compose_message.html",
        {
            "form": form,
        }
    )