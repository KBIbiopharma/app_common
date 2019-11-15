import os
from os.path import dirname, isfile
from unittest import TestCase
import json

from app_common.apptools.cache.txt_file_cache import SingleTxtFileDataCache

HERE = dirname(__file__)

DEFAULT_TXT_CACHE_CONTENT = '{"a": [1, {}], "b": [2, {"timestamp": 1234567}]}'


class TestLocalTxtFileDataCache(TestCase):
    def setUp(self):
        self.cache_filepath = "test_cache.json"

    def tearDown(self):
        if isfile(self.cache_filepath):
            os.remove(self.cache_filepath)

    def test_initialize_from_non_existent_file(self):
        cache = SingleTxtFileDataCache(url=self.cache_filepath)
        with self.assertRaises(ValueError):
            cache.initialize()

    def test_auto_initialize_from_non_existent_file(self):
        cache = SingleTxtFileDataCache(url=self.cache_filepath,
                                       auto_initialize=True)
        self.assertTrue(cache.initialized)
        cache.set_value("a", 2)
        self.assertEqual(cache.get_value("a"), 2)

    def test_create_from_empty_json_file(self):
        with open(self.cache_filepath, "w"):
            pass

        cache = SingleTxtFileDataCache(url=self.cache_filepath)
        with self.assertRaises(ValueError):
            cache.initialize()

    def test_create_from_json_file_no_data(self):
        cache = self.create_cache("{}")
        self.assertEqual(len(cache.list_content()), 0)

    def test_contains_keys(self):
        cache = self.create_cache()
        self.assertIn("a", cache)
        self.assertIn("b", cache)
        self.assertNotIn("NON EXISTENT", cache)

    def test_get_value(self):
        cache = self.create_cache()
        self.assertEqual(cache.get_value("a"), 1)
        self.assertEqual(cache.get_value("b"), 2)
        with self.assertRaises(KeyError):
            cache.get_value("NON EXISTENT")

    def test_get_metadata(self):
        cache = self.create_cache()
        self.assertEqual(cache.get_metadata("a"), {})
        self.assertEqual(cache.get_metadata("b"), {"timestamp": 1234567})
        with self.assertRaises(KeyError):
            cache.get_metadata("NON EXISTENT")

    def test_get_specific_metadata(self):
        key = "c"
        cache = self.create_cache()
        metadata = {"attr1": "attr_val",
                    "attr2": "attr_val2",
                    "attr3": "attr_val3"}
        cache.set_value(key, 2, metadata=metadata)
        metadata = cache.get_metadata(key, metadata_list=["attr1", "attr2"])
        self.assertEqual(metadata, {"attr1": "attr_val", "attr2": "attr_val2"})

    def test_set_value(self):
        cache = self.create_cache("{}")
        self.assertNotIn("a", cache)
        cache.set_value("a", 1)
        self.assertEqual(cache.get_value("a"), 1)

        # Second entry
        self.assertNotIn("b", cache)
        cache.set_value("b", 2)
        self.assertEqual(cache.get_value("b"), 2)

    def test_set_value_collision(self):
        cache = self.create_cache("{}")
        self.assertNotIn("a", cache)
        cache.set_value("a", 1)
        with self.assertRaises(ValueError):
            cache.set_value("a", 1)

        # Unless you set the overwrite flag:
        cache.set_value("a", 2, overwrite=True)
        self.assertEqual(cache.get_value("a"), 2)

    def test_set_value_with_metadata(self):
        cache = self.create_cache("{}")
        cache.set_value("a", 1, {"blah": "foo"})
        self.assertEqual(cache.get_metadata("a"), {"blah": "foo"})

    def test_invalidate_cache(self):
        cache = self.create_cache()
        self.assertIn("a", cache)
        self.assertIn("b", cache)

        cache.invalidate(skip_confirm=True)
        self.assertNotIn("a", cache)
        self.assertNotIn("b", cache)

    def test_invalidate_cache_for_keys(self):
        cache = self.create_cache()
        self.assertIn("a", cache)
        self.assertIn("b", cache)

        cache.invalidate(keys=["a"], skip_confirm=True)
        self.assertNotIn("a", cache)
        self.assertIn("b", cache)

    def test_list_content(self):
        cache = self.create_cache()
        self.assertEqual(set(cache.list_content()), {"a", "b"})

    def test_list_content_key_filter(self):
        cache = self.create_cache()
        content = cache.list_content(key_filter=lambda x: "a" in x)
        self.assertEqual(set(content), {"a"})

    def test_list_content_metadata_filter(self):
        cache = self.create_cache()
        content = cache.list_content(
            metadata_filter=lambda x: "timestamp" in x)
        self.assertEqual(set(content), {"b"})

    def test_changed_flag(self):
        cache = self.create_cache('{}')
        self.assertFalse(cache.changed)
        cache.set_value("c", 42)
        self.assertTrue(cache.changed)

    def test_dont_write_index_on_close_if_unmodified(self):
        cache = self.create_cache('{}')
        last_modified = os.path.getmtime(self.cache_filepath)
        cache.close()
        self.assertEqual(last_modified, os.path.getmtime(self.cache_filepath))

    def test_write_index_on_close_if_modified(self):
        cache = self.create_cache('{}')
        cache.set_value("blah", 2)
        cache.close()
        # Make sure the new value is stored in the index:
        index = self.load_index_file()
        self.assertIn("blah", index)

    def test_context_manager_set_value(self):
        self.create_cache()
        with SingleTxtFileDataCache(url=self.cache_filepath) as cache:
            cache.set_value("blah", 2)

        # Make sure the new value is stored in the index:
        index = self.load_index_file()
        self.assertIn("blah", index)

    def test_context_manager_get_value(self):
        self.create_cache()
        with SingleTxtFileDataCache(url=self.cache_filepath) as cache:
            last_modified = os.path.getmtime(self.cache_filepath)
            value = cache.get_value("a")
            self.assertEqual(value, 1)

        # Index file not rewritten:
        self.assertEqual(last_modified, os.path.getmtime(self.cache_filepath))

    # Helper ------------------------------------------------------------------

    def create_cache(self, content=DEFAULT_TXT_CACHE_CONTENT):
        with open(self.cache_filepath, "w") as f:
            f.write(content)

        cache = SingleTxtFileDataCache(url=self.cache_filepath)
        cache.initialize()
        return cache

    def load_index_file(self):
        return json.load(open(self.cache_filepath))
