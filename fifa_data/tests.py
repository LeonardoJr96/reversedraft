from unittest.mock import Mock, patch

from django.core.files.base import ContentFile
from django.test import SimpleTestCase

from fifa_data.models import Player
from fifa_data.serializers import PlayerSerializer
from fifa_data.services import fetch_photo_as_file


class PhotoBackfillTests(SimpleTestCase):
    def test_serializer_builds_data_uri_from_image_field(self):
        player = Player()
        player.photo = ContentFile(b"fake-image", name="player.png")

        serializer = PlayerSerializer(instance=player)
        result = serializer.get_photo_data_uri(player)

        self.assertEqual(result, "data:image/png;base64,ZmFrZS1pbWFnZQ==")

    @patch("fifa_data.services.urlopen")
    def test_fetch_photo_as_file_returns_content_file(self, mock_urlopen):
        mock_response = Mock()
        mock_response.read.return_value = b"photo-bytes"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = fetch_photo_as_file("https://example.com/player.png", 123)

        self.assertIsInstance(result, ContentFile)
        self.assertEqual(result.name, "123.png")
        self.assertEqual(result.read(), b"photo-bytes")
