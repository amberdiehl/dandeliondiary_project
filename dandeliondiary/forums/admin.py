from django.contrib import admin

from . import models

from guardian.admin import GuardedModelAdmin


# class ForumThreadAdmin(admin.ModelAdmin):
class ForumThreadAdmin(GuardedModelAdmin):

    class ForumThreadReplyInline(admin.StackedInline):
        model = models.ForumReply
        extra = 1

    list_display = [
        "id",
        "title",
        "created",
        "author",
        "view_count",
        "reply_count",
        "subscriber_count",
    ]
    inlines = [
        ForumThreadReplyInline
    ]


admin.site.register(
    models.ForumCategory,
    list_display=[
        "title",
        "parent"
    ]
)


class ForumAdmin(GuardedModelAdmin):

    list_display=[
        "id",
        "title",
        "parent",
        "category",
        "view_count",
        "post_count"
    ]


admin.site.register(models.Forum, ForumAdmin)

admin.site.register(models.ForumThread, ForumThreadAdmin)
