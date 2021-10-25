from rest_framework import serializers

from .models import (
    ContentRequest,
    CtrlfActionType,
    CtrlfContentType,
    Issue,
    Note,
    Page,
    Topic,
)


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
        ctrlf_content = validated_data.pop("ctrlf_content")
        content_type = (
            CtrlfContentType.NOTE
            if type(ctrlf_content) is Note
            else CtrlfContentType.TOPIC
            if type(ctrlf_content) is Topic
            else CtrlfContentType.PAGE
        )

        content_request_data = {
            "user": owner,
            "sub_id": ctrlf_content.id,
            "type": content_type,
            "action": CtrlfActionType.CREATE,
            "reason": f"{CtrlfActionType.CREATE} {str(ctrlf_content._meta).split('.')[1]}",
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

        def create(self, validated_data):
            owner = validated_data.pop("owners")[0]
            topic = Topic.objects.all(**validated_data)
            topic.owners.add(owner)
            return topic


class TopicCreateRequestBodySerializer(serializers.Serializer):
    note_id = serializers.IntegerField()
    title = serializers.CharField()
    content = serializers.CharField()


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = "__all__"
        read_only_fields = ["id", "created_at"]

        def create(self, validated_data):
            owner = validated_data.pop("owners")[0]
            page = Page.objects.create(**validated_data)
            page.owners.add(owner)
            return page


class PageListSerializer(PageSerializer):
    issue_id = serializers.SerializerMethodField()

    def get_issue_id(self, obj):
        content_request = ContentRequest.objects.filter(sub_id=obj.id, type=CtrlfContentType.PAGE).first()
        if content_request is None:
            return content_request
        else:
            return Issue.objects.get(content_request=content_request).id


class PageCreateRequestBodySerializer(serializers.Serializer):
    topic_id = serializers.IntegerField()
    title = serializers.CharField()
    content = serializers.CharField()
    summary = serializers.CharField()


class IssueSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    owner = serializers.EmailField()
    title = serializers.CharField()
    content = serializers.CharField()
    status = serializers.CharField()


class IssueDetailSerializer(serializers.Serializer):
    note_id = serializers.SerializerMethodField()
    topic_id = serializers.SerializerMethodField()
    page_id = serializers.SerializerMethodField()

    id = serializers.IntegerField()
    owner = serializers.EmailField()
    title = serializers.CharField()
    content = serializers.CharField()
    status = serializers.CharField()

    def get_note_id(self, obj):
        page = Page.objects.get(id=obj.content_request.sub_id)
        topic = Topic.objects.get(id=page.topic.id)
        return Note.objects.get(id=topic.note.id).id

    def get_topic_id(self, obj):
        page = Page.objects.get(id=obj.content_request.sub_id)
        return Topic.objects.get(id=page.topic.id).id

    def get_page_id(self, obj):
        return Page.objects.get(id=obj.content_request.sub_id).id


class IssueListQuerySerializer(serializers.Serializer):
    cursor = serializers.IntegerField()


class IssueApproveResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class IssueApproveRequestBodySerializer(serializers.Serializer):
    issue_id = serializers.IntegerField()
