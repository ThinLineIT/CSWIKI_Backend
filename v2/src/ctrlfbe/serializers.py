from rest_framework import serializers

from .models import ContentRequest, Issue, Note, Page, Topic

from .models import (
    ContentRequest,
    CtrlfActionType,
    CtrlfContentType,
    Issue,
    Note,
    Page,
    Topic,
)


class ContentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentRequest
        fields = "__all__"


class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = "__all__"


class NoteListSerializer(serializers.ListSerializer):
    pass


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = "__all__"
        read_only_fields = ["id", "created_at"]
        list_serializer_class = NoteListSerializer

    def create(self, validated_data):
        owner = validated_data.pop("owners")[0]
        note = Note.objects.create(**validated_data)
        note.owners.add(owner)
        return note


class IssueCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = "__all__"

    def create(self, validated_data):
        owner = validated_data.pop("owner")
        note = validated_data.pop("note")
        content_request_data = {
            "user": owner,
            "sub_id": note.id,
            "type": CtrlfContentType.NOTE,
            "action": CtrlfActionType.CREATE,
            "reason": "create note",
        }
        content_request = ContentRequest.objects.create(**content_request_data)
        issue = Issue.objects.create(owner=owner, content_request=content_request, **validated_data)
        return issue


class NoteCreateRequestBodySerializer(serializers.Serializer):
    title = serializers.CharField()
    content = serializers.CharField()


class NoteListQuerySerializer(serializers.Serializer):
    cursor = serializers.IntegerField()


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = "__all__"
        read_only_fields = ["id", "created_at"]
