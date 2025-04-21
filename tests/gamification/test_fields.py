# -*- coding: utf-8 -*-
"""
Tests for custom fields.
"""

from datetime import datetime
from typing import ClassVar
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mongoengine import Document

from vulyk.blueprints.gamification.models.fields import UTCComplexDateTimeField

from ..base import BaseTest


class TestDocument(Document):
    """
    Test document class for testing UTCComplexDateTimeField.
    """

    dt_field = UTCComplexDateTimeField()
    meta: ClassVar[dict] = {"collection": "test_document", "allow_inheritance": True}


class TestUTCComplexDateTimeField(BaseTest):
    """
    Tests for the UTCComplexDateTimeField class.
    """

    def tearDown(self) -> None:
        """
        Clean up after each test.
        """
        # Drop the test collection
        TestDocument.drop_collection()

    def test_convert_from_string(self) -> None:
        """
        Test the _convert_from_string method.
        """
        # Create an instance of the field
        field = UTCComplexDateTimeField()

        # Test with a valid datetime string
        dt_string = "2023,12,31,23,59,59,999999"
        result = field._convert_from_string(dt_string)

        # Check that the result is a datetime object
        self.assertIsInstance(result, datetime)

        # Check that the datetime values are correct
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 31)
        self.assertEqual(result.hour, 23)
        self.assertEqual(result.minute, 59)
        self.assertEqual(result.second, 59)
        self.assertEqual(result.microsecond, 999999)

        # Check that the timezone is UTC
        self.assertEqual(str(result.tzinfo), str(ZoneInfo("UTC")))

    def test_round_trip_save_and_load(self) -> None:
        """
        Test saving and loading a document with the field.
        """
        # Create a datetime with UTC timezone
        test_dt = datetime(2023, 12, 31, 23, 59, 59, 999999, tzinfo=ZoneInfo("UTC"))

        # Create and save a test document
        doc = TestDocument(dt_field=test_dt)
        doc.save()

        # Retrieve the document from the database
        # Note: MongoEngine provides 'objects' attribute dynamically at runtime
        loaded_doc = TestDocument.objects.get(id=doc.id)

        # Check that the datetime field has the correct value
        self.assertEqual(loaded_doc.dt_field, test_dt)

        # Check that the timezone is UTC
        self.assertEqual(str(loaded_doc.dt_field.tzinfo), str(ZoneInfo("UTC")))

    def test_custom_separator(self) -> None:
        """
        Test the field with a custom separator.
        """
        # Create an instance of the field with a custom separator
        custom_separator = "|"
        field = UTCComplexDateTimeField(separator=custom_separator)

        # Check that the separator is set correctly
        self.assertEqual(field.separator, custom_separator)

        # Check that the format string uses the custom separator
        expected_format = "|".join(["%Y", "%m", "%d", "%H", "%M", "%S", "%f", "%Z"])
        self.assertEqual(field.format, expected_format)

        # Test with a valid datetime string using the custom separator
        dt_string = "2023|12|31|23|59|59|999999|UTC"
        result = field._convert_from_string(dt_string)

        # Check that the result is a datetime object
        self.assertIsInstance(result, datetime)

        # Check that the datetime values are correct
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 31)
        self.assertEqual(result.hour, 23)
        self.assertEqual(result.minute, 59)
        self.assertEqual(result.second, 59)
        self.assertEqual(result.microsecond, 999999)

        # Check that the timezone is UTC
        self.assertEqual(str(result.tzinfo), str(ZoneInfo("UTC")))

    def test_convert_from_string_with_timezone(self) -> None:
        """
        Test the _convert_from_string method with timezone information in the string.
        """
        # Create an instance of the field
        field = UTCComplexDateTimeField()

        # Test with a valid datetime string including timezone
        dt_string = "2023,12,31,23,59,59,999999,UTC"
        result = field._convert_from_string(dt_string)

        # Check that the result is a datetime object
        self.assertIsInstance(result, datetime)

        # Check that the datetime values are correct
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 31)
        self.assertEqual(result.hour, 23)
        self.assertEqual(result.minute, 59)
        self.assertEqual(result.second, 59)
        self.assertEqual(result.microsecond, 999999)

        # Check that the timezone is UTC
        self.assertEqual(str(result.tzinfo), str(ZoneInfo("UTC")))

        # Try with a different timezone
        dt_string = "2023,12,31,23,59,59,999999,Europe/London"
        result = field._convert_from_string(dt_string)

        # Check that the timezone is London
        self.assertEqual(str(result.tzinfo), str(ZoneInfo("Europe/London")))

    def test_to_mongo(self) -> None:
        """
        Test the to_mongo method.
        """
        # Create an instance of the field
        field = UTCComplexDateTimeField()

        # Create a datetime with UTC timezone
        dt = datetime(2023, 12, 31, 23, 59, 59, 999999, tzinfo=ZoneInfo("UTC"))

        # Convert to mongo format
        result = field.to_mongo(dt)

        # Check that the result is correct
        self.assertIsInstance(result, str)

        # Check that it has the expected format
        expected = "2023,12,31,23,59,59,999999,UTC"
        self.assertEqual(result, expected)

        # Test with a different timezone
        dt = datetime(2023, 12, 31, 23, 59, 59, 999999, tzinfo=ZoneInfo("Europe/London"))

        # Convert to mongo format
        result = field.to_mongo(dt)

        # When converting to mongo, timezone might be converted to daylight saving time.
        expected = "2023,12,31,23,59,59,999999,GMT"
        self.assertEqual(result, expected)

    def test_to_mongo_none(self) -> None:
        """
        Test the to_mongo method with None.
        """
        # Create an instance of the field
        field = UTCComplexDateTimeField()

        with self.assertRaises(AttributeError):
            field.to_mongo(None)

    def test_field_default_values(self) -> None:
        """
        Test the default values of the field.
        """
        # Create an instance of the field
        field = UTCComplexDateTimeField()

        # Check that the separator has the default value
        self.assertEqual(field.separator, ",")

        # Check that the format string is correct
        expected_format = ",".join(["%Y", "%m", "%d", "%H", "%M", "%S", "%f", "%Z"])
        self.assertEqual(field.format, expected_format)

    def test_round_trip_with_different_timezone(self) -> None:
        """
        Test full round trip with a non-UTC timezone.
        """
        # Create a datetime with a non-UTC timezone
        original_dt = datetime(2023, 12, 31, 23, 59, 59, 999999, tzinfo=ZoneInfo("Europe/London"))

        # Create and save a test document with this datetime
        doc = TestDocument(dt_field=original_dt)
        doc.save()

        # Retrieve the document from the database
        # Note: MongoEngine provides 'objects' attribute dynamically at runtime
        loaded_doc = TestDocument.objects.get(id=doc.id)  # type: ignore

        # The field should preserve the original timezone
        self.assertEqual(loaded_doc.dt_field.utcoffset(), original_dt.utcoffset())
        self.assertEqual(loaded_doc.dt_field, original_dt)

    def test_handling_malformed_string(self) -> None:
        """
        Test handling of malformed datetime strings.
        """
        # Create an instance of the field
        field = UTCComplexDateTimeField()

        # Test with a malformed datetime string - missing timezone
        malformed_dt_string = "2023,12,31,23,59,59,999999"

        # Test with a malformed datetime string - invalid values
        malformed_dt_string = "not,a,valid,date,time,string,000000,UTC"
        with self.assertRaises(ValueError):
            field._convert_from_string(malformed_dt_string)

        # Test with a malformed datetime string - invalid timezone
        malformed_dt_string = "2023,12,31,23,59,59,999999,InvalidZone"
        with self.assertRaises(ZoneInfoNotFoundError):
            field._convert_from_string(malformed_dt_string)
