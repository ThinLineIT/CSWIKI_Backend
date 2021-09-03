from ctrlfbe.serializers import (
    NoteCreateRequestBodySerializer,
    NoteListQuerySerializer,
    NoteSerializer,
    PageSerializer,
    TopicCreateSerializer,
    TopicSerializer,
)

SWAGGER_PAGE_LIST_VIEW = {
    "responses": {200: PageSerializer(many=True)},
    "operation_summary": "Page List API",
    "operation_description": "topic_id에 해당하는 page들의 list를 리턴해줍니다",
    "tags": ["디테일 화면"],
}

SWAGGER_TOPIC_LIST_VIEW = {
    "responses": {200: TopicSerializer(many=True)},
    "operation_summary": "Topic List API",
    "operation_description": "note_id에 해당하는 topic들의 list를 리턴해줍니다",
    "tags": ["디테일 화면"],
}

SWAGGER_NOTE_DETAIL_VIEW = {
    "responses": {200: NoteSerializer()},
    "operation_summary": "Note Detail API",
    "operation_description": "note_id에 해당하는 Note의 상세 내용을 리턴합니다",
    "tags": ["디테일 화면"],
}

SWAGGER_NOTE_LIST_VIEW = {
    "query_serializer": NoteListQuerySerializer,
    "operation_summary": "Note List API",
    "operation_description": "Cursor based pagination 처리된 Note List를 리턴 합니다",
    "tags": ["메인 화면"],
}

SWAGGER_NOTE_CREATE_VIEW = {
    "operation_summary": "Note Create API",
    "operation_description": "비활성화된 Note와 이슈를 생성 합니다.",
    "request_body": NoteCreateRequestBodySerializer,
    "tags": ["메인 화면"],
}

SWAGGER_TOPIC_DETAIL_VIEW = {
    "responses": {200: TopicSerializer()},
    "operation_summary": "Topic Detail API",
    "operation_description": "topic_id에 해당하는 Topic의 상세 내용을 리턴합니다",
    "tags": ["디테일 화면"],
}

SWAGGER_PAGE_DETAIL_VIEW = {
    "responses": {200: PageSerializer()},
    "operation_summary": "Page Detail API",
    "operation_description": "page_id에 해당하는 Page의 상세 내용을 리턴합니다",
    "tags": ["디테일 화면"],
}

SWAGGER_TOPIC_CREATE_VIEW = {
    "request_body": TopicCreateSerializer,
    "responses": {201: ""},
    "operation_summary": "Topic Create API",
    "operation_description": "미승인 토픽을 생성하고 토픽 생성 이슈를 등록합니다.",
    "tags": ["디테일 화면"],
}
