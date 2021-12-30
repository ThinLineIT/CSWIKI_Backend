from common.s3.client import S3Client
from ctrlfbe.mixins import CtrlfAuthenticationMixin
from ctrlfbe.swagger import (
    SWAGGER_HEALTH_CHECK_VIEW,
    SWAGGER_IMAGE_UPLOAD_VIEW,
    SWAGGER_ISSUE_APPROVE_VIEW,
    SWAGGER_ISSUE_DETAIL_VIEW,
    SWAGGER_ISSUE_LIST_VIEW,
    SWAGGER_NOTE_CREATE_VIEW,
    SWAGGER_NOTE_DETAIL_VIEW,
    SWAGGER_NOTE_LIST_VIEW,
    SWAGGER_NOTE_UPDATE_VIEW,
    SWAGGER_PAGE_CREATE_VIEW,
    SWAGGER_PAGE_DETAIL_VIEW,
    SWAGGER_PAGE_LIST_VIEW,
    SWAGGER_PAGE_UPDATE_VIEW,
    SWAGGER_TOPIC_CREATE_VIEW,
    SWAGGER_TOPIC_DETAIL_VIEW,
    SWAGGER_TOPIC_LIST_VIEW,
    SWAGGER_TOPIC_UPDATE_VIEW,
)
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .basedata import NoteData, PageData, TopicData
from .models import (
    CtrlfActionType,
    CtrlfContentType,
    CtrlfIssueStatus,
    Issue,
    Note,
    Page,
    PageHistory,
    PageVersionType,
    Topic,
)
from .paginations import IssueListPagination, NoteListPagination
from .serializers import (
    IssueCreateSerializer,
    IssueDetailSerializer,
    IssueListSerializer,
    NoteSerializer,
    NoteUpdateRequestBodySerializer,
    PageCreateSerializer,
    PageDetailSerializer,
    PageHistorySerializer,
    PageListSerializer,
    PageUpdateRequestBodySerializer,
    TopicSerializer,
    TopicUpdateRequestBodySerializer,
)

s3_client = S3Client()


class BaseContentViewSet(CtrlfAuthenticationMixin, ModelViewSet):
    def paginated_list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        parent_model_kwargs = self.get_parent_kwargs(list(kwargs.values())[0])
        self.queryset = self.child_model.objects.filter(**parent_model_kwargs)

        return super().list(request, *args, **kwargs)

    def get_parent_kwargs(self, parent_id):
        parent_name = str(self.parent_model._meta).split(".")[1]
        parent_queryset = self.parent_model.objects.filter(id=parent_id)
        parent = get_object_or_404(parent_queryset)

        return {parent_name: parent}

    def create(self, request, *args, **kwargs):
        ctrlf_user = self._ctrlf_authentication(request)
        kwargs["model_data"]["owners"] = [ctrlf_user.id]
        kwargs["issue_data"]["owner"] = ctrlf_user.id

        related_model_serializer = self.get_serializer(data=kwargs["model_data"])
        issue_serializer = IssueCreateSerializer(data=kwargs["issue_data"])

        related_model_serializer.is_valid(raise_exception=True)
        issue_serializer.is_valid(raise_exception=True)
        issue_serializer.save(related_model=related_model_serializer.save())

        return Response(status=status.HTTP_201_CREATED)


class NoteViewSet(BaseContentViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    pagination_class = NoteListPagination
    lookup_url_kwarg = "note_id"

    @swagger_auto_schema(**SWAGGER_NOTE_LIST_VIEW)
    def list(self, request, *args, **kwargs):
        return super().paginated_list(request, *args, **kwargs)

    @swagger_auto_schema(**SWAGGER_NOTE_CREATE_VIEW)
    def create(self, request, *args, **kwargs):
        data = NoteData(request).build_data()
        return super().create(request, **data)

    @swagger_auto_schema(**SWAGGER_NOTE_DETAIL_VIEW)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(**SWAGGER_NOTE_UPDATE_VIEW)
    def update(self, request, *args, **kwargs):
        ctrlf_user = self._ctrlf_authentication(request)
        note_id = kwargs["note_id"]
        note = Note.objects.filter(id=note_id).first()
        if note is None:
            return Response(data={"message": "Note를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        note_serializer = NoteUpdateRequestBodySerializer(data=request.data)
        if not note_serializer.is_valid():
            return Response(data={"message": "요청이 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
        issue_data = {
            "owner": ctrlf_user.id,
            "title": request.data["new_title"],
            "reason": request.data["reason"],
            "status": CtrlfIssueStatus.REQUESTED,
            "related_model_type": CtrlfContentType.NOTE,
            "action": CtrlfActionType.UPDATE,
            "etc": note.title,
        }
        issue_serializer = IssueCreateSerializer(data=issue_data)
        issue_serializer.is_valid(raise_exception=True)
        issue_serializer.save(related_model=note)

        return Response(data={"message": "Note 수정 이슈를 생성하였습니다."}, status=status.HTTP_200_OK)


class TopicViewSet(BaseContentViewSet):
    parent_model = Note
    child_model = Topic
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    lookup_url_kwarg = "topic_id"

    @swagger_auto_schema(**SWAGGER_TOPIC_LIST_VIEW)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(**SWAGGER_TOPIC_CREATE_VIEW)
    def create(self, request, *args, **kwargs):
        data = TopicData(request).build_data()
        return super().create(request, **data)

    @swagger_auto_schema(**SWAGGER_TOPIC_DETAIL_VIEW)
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(**SWAGGER_TOPIC_UPDATE_VIEW)
    def update(self, request, *args, **kwargs):
        ctrlf_user = self._ctrlf_authentication(request)
        topic = Topic.objects.filter(id=kwargs["topic_id"]).first()
        if topic is None:
            return Response(data={"message": "Topic이 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)

        topic_serializer = TopicUpdateRequestBodySerializer(data=request.data)
        if not topic_serializer.is_valid():
            return Response(data={"message": "요청이 유효하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        issue_data = {
            "owner": ctrlf_user.id,
            "title": request.data["new_title"],
            "reason": request.data["reason"],
            "status": CtrlfIssueStatus.REQUESTED,
            "related_model_type": CtrlfContentType.TOPIC,
            "action": CtrlfActionType.UPDATE,
            "etc": topic.title,
        }
        issue_serializer = IssueCreateSerializer(data=issue_data)
        issue_serializer.is_valid(raise_exception=True)
        issue_serializer.save(related_model=topic)

        return Response(data={"message": "Topic 수정 이슈를 생성하였습니다."}, status=status.HTTP_200_OK)


class PageViewSet(BaseContentViewSet):
    parent_model = Topic
    child_model = Page
    queryset = Page.objects.all()
    lookup_url_kwarg = "page_id"
    serializer_class = PageCreateSerializer

    @swagger_auto_schema(**SWAGGER_PAGE_LIST_VIEW)
    def list(self, request, *args, **kwargs):
        self.serializer_class = PageListSerializer
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(**SWAGGER_PAGE_CREATE_VIEW)
    def create(self, request, *args, **kwargs):
        data = PageData(request).build_data()
        return super().create(request, **data)

    @swagger_auto_schema(**SWAGGER_PAGE_DETAIL_VIEW)
    def retrieve(self, request, *args, **kwargs):
        version_no = int(request.query_params["version_no"])
        page_id = list(kwargs.values())[0]

        page = Page.objects.filter(id=page_id).first()
        if page is None:
            return Response(data={"message": "페이지를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        page_history = PageHistory.objects.filter(page=page, version_no=version_no).first()
        if page_history is None:
            return Response(data={"message": "버전 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        page_serializer = PageDetailSerializer(page_history)
        data = page_serializer.data

        return Response(data=data, status=status.HTTP_200_OK)

    @swagger_auto_schema(**SWAGGER_PAGE_UPDATE_VIEW)
    def update(self, request, *args, **kwargs):
        ctrlf_user = self._ctrlf_authentication(request)
        page = Page.objects.filter(id=kwargs["page_id"]).first()
        if page is None:
            return Response(data={"message": "페이지를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        page_serializer = PageUpdateRequestBodySerializer(data=request.data)
        page_serializer.is_valid(raise_exception=True)

        version_count = PageHistory.objects.filter(page=page).count()
        page_history_data = {
            "owner": ctrlf_user.id,
            "page": page.id,
            "title": request.data["new_title"],
            "content": request.data["new_content"],
            "version_no": version_count + 1,
            "version_type": PageVersionType.UPDATE,
        }
        page_history_serializer = PageHistorySerializer(data=page_history_data)
        page_history_serializer.is_valid(raise_exception=True)
        new_page_history = page_history_serializer.save()

        issue_data = {
            "owner": ctrlf_user.id,
            "title": request.data["new_title"],
            "reason": request.data["reason"],
            "status": CtrlfIssueStatus.REQUESTED,
            "related_model_type": CtrlfContentType.PAGE,
            "action": CtrlfActionType.UPDATE,
        }
        issue_serializer = IssueCreateSerializer(data=issue_data)
        issue_serializer.is_valid(raise_exception=True)
        issue_serializer.save(related_model=new_page_history)

        return Response(status=status.HTTP_201_CREATED)


class IssueViewSet(CtrlfAuthenticationMixin, ModelViewSet):
    queryset = Issue.objects.all()
    serializer_class = IssueListSerializer
    pagination_class = IssueListPagination
    lookup_url_kwarg = "issue_id"

    @swagger_auto_schema(**SWAGGER_ISSUE_LIST_VIEW)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(**SWAGGER_ISSUE_DETAIL_VIEW)
    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = IssueDetailSerializer
        return super().retrieve(request, *args, **kwargs)


class IssueApproveView(CtrlfAuthenticationMixin, APIView):
    @swagger_auto_schema(**SWAGGER_ISSUE_APPROVE_VIEW)
    def post(self, request, *args, **kwargs):
        issue_approve_request_user = self._ctrlf_authentication(request)
        issue_id = request.data["issue_id"]
        try:
            issue = Issue.objects.get(id=issue_id)
        except Issue.DoesNotExist:
            return Response(data={"message": "이슈 ID를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        try:
            ctrlf_content = self.get_content(issue=issue, ctrlf_user=issue_approve_request_user)
        except ValueError:
            return Response(data={"message": "승인 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        if issue.action == CtrlfActionType.UPDATE:
            if isinstance(ctrlf_content, Note):
                ctrlf_content.title = issue.title

        if issue.action == CtrlfActionType.UPDATE:
            if not ctrlf_content.owners.filter(email=issue_approve_request_user.email).exists():
                return Response(status=status.HTTP_403_FORBIDDEN)
            if isinstance(ctrlf_content, Topic):
                ctrlf_content.title = issue.title

        if issue.action == CtrlfActionType.UPDATE:
            if not ctrlf_content.owners.filter(email=issue_approve_request_user.email).exists():
                return Response(status=status.HTTP_403_FORBIDDEN)
            if isinstance(ctrlf_content, Page):
                page_id = PageHistory.objects.filter(id=issue.related_model_id).first().page.id

                new_page_history = PageHistory.objects.filter(page=page_id, version_type=PageVersionType.UPDATE).first()
                prev_page_history = PageHistory.objects.filter(
                    page=page_id, version_type=PageVersionType.CURRENT
                ).first()
                prev_page_history.version_type = PageVersionType.PREVIOUS
                prev_page_history.save()

                new_page_history.is_approved = True
                new_page_history.version_type = PageVersionType.CURRENT
                new_page_history.save()

                ctrlf_content.title = new_page_history.title
                ctrlf_content.content = new_page_history.content

        ctrlf_content.is_approved = True
        ctrlf_content.save()
        if isinstance(ctrlf_content, Page):
            page_history = ctrlf_content.page_history.first()
            if page_history is not None:
                page_history.is_approved = True
                page_history.save()

        issue.status = CtrlfIssueStatus.APPROVED
        issue.save()

        return Response(data={"message": "승인 완료"}, status=status.HTTP_200_OK)

    def get_content(self, issue, ctrlf_user):
        content = (
            PageHistory.objects.get(id=issue.related_model_id).page
            if issue.related_model_type == CtrlfContentType.PAGE
            else Note.objects.get(id=issue.related_model_id)
            if issue.related_model_type == CtrlfContentType.NOTE
            else Topic.objects.get(id=issue.related_model_id)
            if issue.related_model_type == CtrlfContentType.TOPIC
            else None
        )
        if issue.action == CtrlfActionType.CREATE:
            if type(content) is Page:
                if not content.topic.owners.filter(id=ctrlf_user.id).exists():
                    raise ValueError
            elif type(content) is Topic:
                if not content.note.owners.filter(id=ctrlf_user.id).exists():
                    raise ValueError
            elif type(content) is Note:
                if not content.owners.filter(id=ctrlf_user.id).exists():
                    raise ValueError

        return content


class ImageUploadView(APIView):
    BUCKET_BASE_DIR = settings.S3_BUCKET_BASE_DIR
    BASE_URL = settings.S3_BASE_URL
    parser_classes = (MultiPartParser,)

    @swagger_auto_schema(**SWAGGER_IMAGE_UPLOAD_VIEW)
    def post(self, request, *args, **kwargs):
        image_data = request.FILES["image"]
        file_name_to_upload = image_data.name
        file_content_type = image_data.content_type
        bucket_path = f"{self.BUCKET_BASE_DIR}/{file_name_to_upload}"
        s3_client.upload_file_object(image_data=image_data, bucket_path=bucket_path, content_type=file_content_type)

        return Response(data={"image_url": f"{self.BASE_URL}/{bucket_path}"}, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    @swagger_auto_schema(**SWAGGER_HEALTH_CHECK_VIEW)
    def get(self, request):
        return Response(data={"message": "OK"}, status=status.HTTP_200_OK)
