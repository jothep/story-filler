"""Regression coverage for admin permissions and public API failures."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import OperationalError
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, Throttled
from rest_framework.test import APITestCase

from .models import AppConfig, BackgroundMusic, BlankLink, Paragraph, Story, Word


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class AppConfigAdminPermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user(
            username="configuration-editor", is_staff=True
        )
        cls.add_url = reverse("admin:core_appconfig_add")

    def setUp(self):
        self.client.force_login(self.staff)

    def grant_permissions(self, *codenames):
        permissions = Permission.objects.filter(
            content_type__app_label="core", codename__in=codenames
        )
        self.staff.user_permissions.add(*permissions)

    def test_staff_without_add_permission_cannot_open_add_page(self):
        self.assertFalse(self.staff.has_perm("core.add_appconfig"))

        response = self.client.get(self.add_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_without_add_permission_cannot_create_configuration(self):
        response = self.client.post(self.add_url, {"menu_bgm": "", "_save": "Save"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(AppConfig.objects.exists())

    def test_authorized_staff_can_create_first_configuration(self):
        self.grant_permissions("add_appconfig")
        self.assertEqual(self.client.get(self.add_url).status_code, status.HTTP_200_OK)

        response = self.client.post(self.add_url, {"menu_bgm": "", "_save": "Save"})

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(AppConfig.objects.count(), 1)

    def test_authorized_staff_cannot_create_second_configuration(self):
        self.grant_permissions("add_appconfig")
        AppConfig.objects.create()

        response = self.client.post(self.add_url, {"menu_bgm": "", "_save": "Save"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(AppConfig.objects.count(), 1)

    def test_authorized_staff_can_still_edit_existing_configuration(self):
        self.grant_permissions("view_appconfig", "change_appconfig")
        config = AppConfig.objects.create()
        music = BackgroundMusic.objects.create(
            title="Menu music", audio_file="bgm/menu.mp3"
        )
        change_url = reverse("admin:core_appconfig_change", args=[config.pk])
        self.assertEqual(self.client.get(change_url).status_code, status.HTTP_200_OK)

        response = self.client.post(change_url, {"menu_bgm": music.pk, "_save": "Save"})

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        config.refresh_from_db()
        self.assertEqual(config.menu_bgm_id, music.pk)


class PublicAPIErrorTests(APITestCase):
    """Database and serialization failures must not look like valid empty data."""

    internal_error = "database mock-private.example failed for mock_database_user"

    @classmethod
    def setUpTestData(cls):
        cls.story = Story.objects.create(title="Water story")
        cls.word = Word.objects.create(maori_word="wai", english_translation="water")
        cls.paragraph = Paragraph.objects.create(
            story=cls.story, order=1, text="Find __BLANK_water__ and __BLANK_pending__."
        )
        cls.link = BlankLink.objects.create(
            paragraph=cls.paragraph, placeholder="__BLANK_water__", word=cls.word
        )
        cls.pending_link = BlankLink.objects.create(
            paragraph=cls.paragraph, placeholder="__BLANK_pending__", word=None
        )
        cls.list_url = reverse("story-list")
        cls.detail_url = reverse("story-detail", args=[cls.story.pk])
        cls.config_url = reverse("app-config")

    def assert_safe_server_error(self, response):
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response["Content-Type"].split(";", 1)[0], "application/json")
        self.assertIn("error", response.data)
        self.assertIsInstance(response.data["error"], str)
        public_output = (
            response.content.decode() + "\n" + "\n".join(response.headers.values())
        )
        self.assertNotIn(self.internal_error, public_output)
        self.assertNotIn("mock-private.example", public_output)
        self.assertNotIn("mock_database_user", public_output)

    def test_story_list_database_failure_returns_safe_error(self):
        with self.assertLogs("core.views", level="ERROR") as logs:
            with patch(
                "django.db.models.sql.compiler.SQLCompiler.execute_sql",
                side_effect=OperationalError(self.internal_error),
            ):
                response = self.client.get(self.list_url)

        self.assert_safe_server_error(response)
        self.assertTrue(any(self.internal_error in message for message in logs.output))
        self.assertIsNotNone(logs.records[0].exc_info)

    def test_known_api_failure_keeps_its_status(self):
        with patch(
            "core.views.StoryListAPIView.get_queryset",
            side_effect=Throttled(wait=10),
        ):
            response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response["Retry-After"], "10")

    def test_story_object_permission_failure_remains_forbidden(self):
        with patch(
            "core.views.StoryDetailAPIView.check_object_permissions",
            side_effect=PermissionDenied("This story is not accessible."),
        ):
            response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_config_database_failure_is_not_a_successful_empty_config(self):
        with patch(
            "django.db.models.sql.compiler.SQLCompiler.execute_sql",
            side_effect=OperationalError(self.internal_error),
        ):
            response = self.client.get(self.config_url)

        self.assert_safe_server_error(response)

    def test_linked_word_query_failure_is_not_a_successful_empty_bank(self):
        with patch(
            "core.serializers.Word.objects.filter",
            side_effect=OperationalError(self.internal_error),
        ):
            response = self.client.get(self.detail_url)

        self.assert_safe_server_error(response)

    def test_word_serialization_failure_is_not_a_null_word(self):
        with patch(
            "core.serializers.WordSerializer.to_representation",
            side_effect=RuntimeError(self.internal_error),
        ):
            response = self.client.get(self.detail_url)

        self.assert_safe_server_error(response)

    def test_blank_serialization_failure_is_not_an_empty_paragraph(self):
        with patch(
            "core.serializers.BlankLinkSerializer.to_representation",
            side_effect=RuntimeError(self.internal_error),
        ):
            response = self.client.get(self.detail_url)

        self.assert_safe_server_error(response)

    def test_config_serialization_failure_is_not_a_successful_empty_config(self):
        music = BackgroundMusic.objects.create(
            title="Menu music", audio_file="bgm/menu.mp3"
        )
        AppConfig.objects.create(menu_bgm=music)
        with patch(
            "core.serializers.BackgroundMusicSerializer.to_representation",
            side_effect=RuntimeError(self.internal_error),
        ):
            response = self.client.get(self.config_url)

        self.assert_safe_server_error(response)

    def test_story_response_preserves_optional_media_and_unlinked_blanks(self):
        extra_word = Word.objects.create(maori_word="rangi", english_translation="sky")
        self.story.word_bank.add(extra_word)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_word = {
            "id": self.word.pk,
            "maori_word": "wai",
            "english_translation": "water",
            "image": None,
            "maori_audio": None,
            "english_audio": None,
        }
        self.assertEqual(
            response.data,
            {
                "id": self.story.pk,
                "title": "Water story",
                "background_music_url": None,
                "picture_url": None,
                "words_in_bank": [expected_word],
                "paragraphs": [
                    {
                        "id": self.paragraph.pk,
                        "order": 1,
                        "text": self.paragraph.text,
                        "audio": None,
                        "blank_links": [
                            {
                                "id": self.link.pk,
                                "placeholder": "__BLANK_water__",
                                "word": expected_word,
                            },
                            {
                                "id": self.pending_link.pk,
                                "placeholder": "__BLANK_pending__",
                                "word": None,
                            },
                        ],
                    }
                ],
            },
        )

    def test_story_list_keeps_its_public_array_response(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{"id": self.story.pk, "title": "Water story"}])

    def test_public_endpoints_remain_read_only(self):
        for url in (self.list_url, self.detail_url, self.config_url):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
                self.assertEqual(self.client.head(url).status_code, status.HTTP_200_OK)
                response = self.client.options(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertSetEqual(
                    set(response["Allow"].split(", ")), {"GET", "HEAD", "OPTIONS"}
                )
                self.assertEqual(
                    self.client.post(url, {"title": "Unexpected write"}).status_code,
                    status.HTTP_405_METHOD_NOT_ALLOWED,
                )
        self.assertEqual(Story.objects.count(), 1)
        self.assertFalse(AppConfig.objects.exists())

    def test_missing_story_still_returns_not_found(self):
        response = self.client.get(reverse("story-detail", args=[self.story.pk + 1]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_configuration_still_returns_empty_music(self):
        response = self.client.get(self.config_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"menu_bgm": None})

    def test_configuration_without_music_still_returns_empty_music(self):
        AppConfig.objects.create()

        response = self.client.get(self.config_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"menu_bgm": None})

    def test_configuration_with_music_keeps_its_response_shape(self):
        music = BackgroundMusic.objects.create(
            title="Menu music", audio_file="bgm/menu.mp3"
        )
        AppConfig.objects.create(menu_bgm=music)

        response = self.client.get(self.config_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "menu_bgm": {
                    "id": music.pk,
                    "title": "Menu music",
                    "audio_url": music.audio_file.url,
                }
            },
        )
