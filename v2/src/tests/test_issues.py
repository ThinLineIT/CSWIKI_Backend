from ctrlf_auth.models import CtrlfUser
from ctrlf_auth.serializers import LoginSerializer
from ctrlfbe.models import (
    ContentRequest,
    CtrlfActionType,
    CtrlfContentType,
    CtrlfIssueStatus,
    Issue,
    Note,
    Page,
    Topic,
)
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status


class IssueListTextMixin:
    def setUp(self) -> None:
        self.client = Client()
        self.user_data = {
            "email": "test@test.com",
            "password": "12345",
        }
        self.user = CtrlfUser.objects.create_user(**self.user_data)

    def _call_api(self, cursor):
        return self.client.get(
            reverse("issues:issue_list"),
            {"cursor": cursor},
        )

    def _call_detail_api(self, issue_id):
        return self.client.get(reverse("issues:issue_detail", kwargs={"issue_id": issue_id}))

    def _make_issues(self, count):
        for i in range(1, count + 1):
            Issue.objects.create(
                owner=self.user,
                title=f"test title {i}",
                content=f"test content {1}",
                status=CtrlfIssueStatus.REQUESTED,
            )


class TestIssueList(IssueListTextMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

    def test_issue_list_should_return_200(self):
        # Given: 미리 30개의 이슈를 생성하고, 시작 cursor가 주어진다.
        self._make_issues(30)
        given_cursor = 0

        # When: issue list api를 호출한다.
        response = self._call_api(given_cursor)

        # Then: status code 200을 리턴한다.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # And: next_cursor는 30을 리턴한다.
        self.assertEqual(response.data["next_cursor"], 30)
        # And: 시작 cursor부터 30개의 issue list를 리턴한다.
        self.assertEqual(len(response.data["issues"]), 30)

    def test_issue_list_on_issue_count_less_than_30(self):
        # Given: 10개의 이슈를 생성하고 시작 cursor를 3으로 주어진다.
        self._make_issues(10)
        given_cursor = 3

        # When: issue list api를 호출한다.
        response = self._call_api(given_cursor)

        # Then: status code는 200을 리턴한다.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # And: next_cursor는 10을 리턴한다.
        self.assertEqual(response.data["next_cursor"], 10)
        # And: 시작 cursor부터 7개의 issue list를 리턴한다.
        self.assertEqual(len(response.data["issues"]), 7)

    def test_issue_list_on_empty_issue(self):
        # Given: 이슈 생성 없이, cursor만 주어진다.
        given_cursor = 0

        # When: issue list api를 호풀한다.
        response = self._call_api(given_cursor)

        # Then: status code는 200을 리턴한다
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # And: next_cursor는 0을 리턴한다.
        self.assertEqual(response.data["next_cursor"], 0)
        # And: empty list를 리턴한다.
        self.assertEqual(len(response.data["issues"]), 0)


class TestIssueDetail(IssueListTextMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()

    def test_issue_detail_should_return_issue_on_success(self):
        # Given: 이슈를 1개 생성 하였을 때,
        issue = Issue.objects.create(
            owner=self.user,
            title="test title",
            content="test content",
            status=CtrlfIssueStatus.REQUESTED,
        )

        # When: issue list api를 호출한다.
        response = self._call_detail_api(issue_id=issue.id)

        # Then: status code는 200을 리턴한다
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # And: 생성된 이슈와 값이 일치해야한다
        self.assertEqual(response.data["title"], "test title")
        self.assertEqual(response.data["content"], "test content")
        self.assertEqual(response.data["status"], CtrlfIssueStatus.REQUESTED)
        self.assertEqual(response.data["owner"], self.user.email)

    def test_issue_detail_should_return_404_not_found_on_issue_does_not_exist(self):
        # Given: 이슈를 생성하지 않았을 때,
        invalid_issue_id = 1122334

        # When: issue list api를 호출한다.
        response = self._call_detail_api(issue_id=invalid_issue_id)

        # Then: status code는 404을 리턴한다
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestIssueApprove(IssueListTextMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.owner_data = {
            "email": "jinho@naver.com",
            "password": "q1w2e3r4",
        }
        self.owner = CtrlfUser.objects.create_user(**self.owner_data)
        self.note = Note.objects.create(title="basic note")
        self.note.owners.add(self.owner)
        topic_data = {"note": self.note, "title": "basic topic"}
        self.topic = Topic.objects.create(**topic_data)
        self.topic.owners.add(self.owner)

    def _make_note(self):
        note = Note.objects.create(title="test note title")
        note.owners.add(self.owner)
        content_request_data = {
            "user": self.owner,
            "sub_id": note.id,
            "type": CtrlfContentType.NOTE,
            "action": CtrlfActionType.CREATE,
        }
        content_request = ContentRequest.objects.create(**content_request_data)
        issue_data = {"owner": self.owner, "content_request": content_request, "status": CtrlfIssueStatus.REQUESTED}
        issue = Issue.objects.create(**issue_data)
        return note.id, issue.id

    def _make_topic(self):
        topic_data = {"note": self.note, "title": "test topic title"}
        topic = Topic.objects.create(**topic_data)
        topic.owners.add(self.owner)
        content_request_data = {
            "user": self.owner,
            "sub_id": topic.id,
            "type": CtrlfContentType.TOPIC,
            "action": CtrlfActionType.CREATE,
        }
        content_request = ContentRequest.objects.create(**content_request_data)
        issue_data = {"owner": self.owner, "content_request": content_request, "status": CtrlfIssueStatus.REQUESTED}
        issue = Issue.objects.create(**issue_data)
        return topic.id, issue.id

    def _make_page(self):
        page_data = {
            "topic": self.topic,
            "title": "test page title",
            "content": "test page content",
            "summary": "summary",
        }
        page = Page.objects.create(**page_data)
        page.owners.add(self.owner)
        content_request_data = {
            "user": self.owner,
            "sub_id": page.id,
            "type": CtrlfContentType.PAGE,
            "action": CtrlfActionType.CREATE,
        }
        content_request = ContentRequest.objects.create(**content_request_data)
        issue_data = {"owner": self.owner, "content_request": content_request, "status": CtrlfIssueStatus.REQUESTED}
        issue = Issue.objects.create(**issue_data)
        return page.id, issue.id

    def _login(self, user_data):
        serializer = LoginSerializer()
        return serializer.validate(user_data)["token"]

    def _call_api(self, request_body, token=None):
        if token:
            header = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        else:
            header = {}
        return self.client.post(reverse("actions:issue_approve"), request_body, **header)

    def test_issue_approve_should_return_200_on_issue_about_note(self):
        # Given: Note와 Issue를 생성한다.
        note_id, issue_id = self._make_note()
        # And: request_body로 유효한 issue id가 주어진다.
        request_body = {"issue_id": issue_id}
        # And: owner 정보로 로그인 하여 토큰을 발급받은 상태이다.
        owner_token = self._login(self.owner_data)

        # When: 인증이 필요한 approve issue api를 호출한다.
        response = self._call_api(request_body, owner_token)

        # Then: status code는 200을 리턴한다.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # And: "승인 완료"라는 메세지를 리턴한다
        self.assertEqual(response.data["message"], "승인 완료")
        # And: Note의 is_apporved는 True이다.
        note = Note.objects.get(id=note_id)
        self.assertTrue(note.is_approved)
        # And: Issue의 status는 APPROVED이다.
        issue = Issue.objects.get(id=issue_id)
        self.assertEqual(issue.status, CtrlfIssueStatus.APPROVED)

    def test_issue_approve_should_return_200_on_issue_about_topic(self):
        # Given: Topic과 Issue를 생성한다.
        topic_id, issue_id = self._make_topic()
        # And: request_body로 유효한 issue id가 주어진다.
        request_body = {"issue_id": issue_id}
        # And: owner 정보로 로그인 하여 토큰을 발급받은 상태이다.
        owner_token = self._login(self.owner_data)

        # When: 인증이 필요한 approve issue api를 호출한다.
        response = self._call_api(request_body, owner_token)

        # Then: status code는 200을 리턴한다.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # And: "승인 완료"라는 메세지를 리턴한다
        self.assertEqual(response.data["message"], "승인 완료")
        # And: Topic의 is_apporved는 True이다.
        topic = Topic.objects.get(id=topic_id)
        self.assertTrue(topic.is_approved)
        # And: Issue의 status는 APPROVED이다.
        issue = Issue.objects.get(id=issue_id)
        self.assertEqual(issue.status, CtrlfIssueStatus.APPROVED)

    def test_issue_approve_should_return_200_on_issue_about_page(self):
        # Given: Page와 Issue를 생성한다.
        page_id, issue_id = self._make_page()
        # And: request_body로 유효한 issue id가 주어진다.
        request_body = {"issue_id": issue_id}
        # And: owner 정보로 로그인 하여 토큰을 발급받은 상태이다.
        owner_token = self._login(self.owner_data)

        # When: 인증이 필요한 approve issue api를 호출한다.
        response = self._call_api(request_body, owner_token)

        # Then: status code는 200을 리턴한다.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # And: "승인 완료"라는 메세지를 리턴한다
        self.assertEqual(response.data["message"], "승인 완료")
        # And: Page의 is_apporved는 True이다.
        page = Page.objects.get(id=page_id)
        self.assertTrue(page.is_approved)
        # And: Issue의 status는 APPROVED이다.
        issue = Issue.objects.get(id=issue_id)
        self.assertEqual(issue.status, CtrlfIssueStatus.APPROVED)

    def test_should_return_404_on_invalid_issue_id(self):
        # Given: Page와 Issue를 생성한다.
        page_id, issue_id = self._make_page()
        # And: request_body로 유효하지 않은 issue id가 주어진다.
        invalid_issue_id = 2952389
        request_body = {"issue_id": invalid_issue_id}
        # And: owner 정보로 로그인하여 토큰을 발급 받은 상황이다.
        token = self._login(self.owner_data)

        # When: 인증이 필요한 approve issue api를 호출한다.
        response = self._call_api(request_body, token)

        # Then: status code는 404을 리턴한다.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # And: "이슈 ID를 찾을 수 없습니다."라는 메세지를 리턴한다.
        self.assertEqual(response.data["message"], "이슈 ID를 찾을 수 없습니다.")
        # And: 생성한 Page의 is_approved는 False이다.
        page = Page.objects.get(id=page_id)
        self.assertFalse(page.is_approved)
        # And: 생성한 Issue의 Status는 REQUESTD이다
        issue = Issue.objects.get(id=issue_id)
        self.assertEqual(issue.status, CtrlfIssueStatus.REQUESTED)

    def test_should_return_400_on_unauthorized_about_issue(self):
        # Given: Page와 Issue를 생성한다.
        page_id, issue_id = self._make_page()
        # And: request_body로 유효한 issue id가 주어진다.
        request_body = {"issue_id": issue_id}
        # And: owner 정보가 아닌 다른 user 정보로 로그인
        token = self._login(self.user_data)

        # When: 인증이 필요한 approve issue api를 호출한다.
        response = self._call_api(request_body, token)

        # Then: status code는 400을 리턴한다.
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # And: "승인 권한이 없습니다."라는 메세지를 리턴한다.
        self.assertEqual(response.data["message"], "승인 권한이 없습니다.")
        # And: 생성한 Page의 is_approved는 False이다.
        page = Page.objects.get(id=page_id)
        self.assertFalse(page.is_approved)
        # And: 생성한 Issue의 Status는 REQUESTD이다
        issue = Issue.objects.get(id=issue_id)
        self.assertEqual(issue.status, CtrlfIssueStatus.REQUESTED)
