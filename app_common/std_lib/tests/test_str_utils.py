
from unittest import TestCase
from numpy import array

from app_common.std_lib.str_utils import add_suffix_if_exists, format_array, \
    fuzzy_string_search_in, sanitize_string


class TestAddSuffixIfExists(TestCase):
    def test_no_op(self):
        candidate = "foo"
        known_list = []
        self.assertEqual(add_suffix_if_exists(candidate, known_list),
                         candidate)

        candidate = "foo"
        known_list = ["bar", "baz", "zap"]
        self.assertEqual(add_suffix_if_exists(candidate, known_list),
                         candidate)

    def test_rotate(self):
        candidate = "foo"
        known_list = ["foo"]
        self.assertEqual(add_suffix_if_exists(candidate, known_list),
                         candidate + "_v2")

    def test_rotate_twice(self):
        candidate = "foo"
        known_list = ["foo", "foo_v2"]
        self.assertEqual(add_suffix_if_exists(candidate, known_list),
                         candidate + "_v3")

    def test_rotate_whole(self):
        candidate = "foo"
        known_list = ["foo", "foo_v2", "foo_v4"]
        self.assertEqual(add_suffix_if_exists(candidate, known_list),
                         candidate + "_v3")

    def test_rotate_2digits(self):
        candidate = "foo"
        known_list = ["foo"]
        for i in range(2, 11):
            known_list.append("foo_v{}".format(i))
        self.assertEqual(add_suffix_if_exists(candidate, known_list),
                         candidate + "_v11")

    def test_rotate_with_suffix_pattern(self):
        candidate = "foo"
        known_list = ["foo", "foo_2", "foo_3"]
        new_val = add_suffix_if_exists(candidate, known_list,
                                       suffix_patt="_{}")
        self.assertEqual(new_val, candidate + "_4")


class TestFuzzyStringSearchIn(TestCase):
    def setUp(self):
        self.word = "hello_jo"

    def test_trivial_in(self):
        matched = fuzzy_string_search_in(self.word, [self.word])
        self.assertEqual(matched, self.word)
        matched = fuzzy_string_search_in(self.word, [self.word, "blah"])
        self.assertEqual(matched, self.word)

    def test_trivial_not_in(self):
        matched = fuzzy_string_search_in(self.word, [])
        self.assertIsNone(matched)
        matched = fuzzy_string_search_in(self.word, ["blah"])
        self.assertIsNone(matched)

    def test_other_container_type(self):
        matched = fuzzy_string_search_in(self.word, (self.word,))
        self.assertEqual(matched, self.word)
        matched = fuzzy_string_search_in(self.word, {self.word})
        self.assertEqual(matched, self.word)

    def test_with_duplicate(self):
        matched = fuzzy_string_search_in(self.word, (self.word, self.word))
        self.assertEqual(matched, self.word)

    def test_fuzzy_in_ignore_underscore(self):
        matched = fuzzy_string_search_in(self.word, ["_hello jo_ _"])
        self.assertEqual(matched, "_hello jo_ _")

    def test_fuzzy_in_ignore_spaces(self):
        matched = fuzzy_string_search_in(self.word, ["  hello   jo  "])
        self.assertEqual(matched, "  hello   jo  ")

    def test_fuzzy_in_ignore_upper_case(self):
        matched = fuzzy_string_search_in(self.word, ["HELLO jo"])
        self.assertEqual(matched, "HELLO jo")

    def test_fuzzy_not_in(self):
        matched = fuzzy_string_search_in(self.word, ["hello@jo"])
        self.assertIsNone(matched)
        matched = fuzzy_string_search_in(self.word, ["hello_joe"])
        self.assertIsNone(matched)
        matched = fuzzy_string_search_in(self.word, ["hello_j"])
        self.assertIsNone(matched)


class TestSanitizeString(TestCase):
    def test_no_op(self):
        candidate = "foo"
        self.assertEqual(sanitize_string(candidate), candidate)

    def test_no_op2(self):
        candidate = "foo_bar"
        self.assertEqual(sanitize_string(candidate), candidate)

    def test_remove_special_char(self):
        candidate = "f@o#o%b^a&r\\b/a:z+z=e<n>"
        expected = "f_o_o_b_a_r_b_a_z_z_e_n"
        self.assertEqual(sanitize_string(candidate), expected)

    def test_dot_as_special_char(self):
        candidate = "foo.bar"
        self.assertEqual(sanitize_string(candidate), "foo_bar")

    def test_double_special_chars(self):
        candidate = "foo.$%bar"
        self.assertEqual(sanitize_string(candidate), "foo_bar")

    def test_custom_special_chars(self):
        candidate = "foo.$%bar"
        self.assertEqual(sanitize_string(candidate, special_chars="fo"),
                         ".$%bar")


class TestSanitizeStringSpecialReplacementChar(TestCase):
    def test_no_op(self):
        candidate = "foo"
        self.assertEqual(sanitize_string(candidate, replace_with="x"),
                         candidate)

    def test_no_op2(self):
        candidate = "fooxbar"
        self.assertEqual(sanitize_string(candidate, replace_with="x"),
                         candidate)

    def test_remove_special_char(self):
        candidate = "f@o#o%b^a&r\\b/a:z+z=e<n>"
        expected = "fxoxoxbxaxrxbxaxzxzxexn"
        self.assertEqual(sanitize_string(candidate, replace_with="x"),
                         expected)

    def test_dot_as_special_char(self):
        candidate = "foo.bar"
        self.assertEqual(sanitize_string(candidate, replace_with="x"),
                         "fooxbar")

    def test_double_special_chars(self):
        candidate = "foo.$%bar"
        self.assertEqual(sanitize_string(candidate, replace_with="x"),
                         "fooxbar")


class TestFormatArray(TestCase):
    def test_float_array_normal_numbers(self):
        arr = array([1.1, 2.22, 3.333], dtype="float")
        arr_repr = format_array(arr)
        self.assertEqual(arr_repr, "[1.1, 2.22, 3.333]")

    def test_float_array_large_numbers(self):
        arr = array([1.1e9, 2.22e9, 3.333e9], dtype="float")
        arr_repr = format_array(arr)
        self.assertEqual(arr_repr, "[1.1e+09, 2.22e+09, 3.333e+09]")

    def test_float_array_small_numbers(self):
        arr = array([1.1e-9, 2.22e-9, 3.333e-9], dtype="float")
        arr_repr = format_array(arr)
        self.assertEqual(arr_repr, "[1.1e-09, 2.22e-09, 3.333e-09]")

    def test_int_array_normal_numbers(self):
        arr = array([1, 2, 3], dtype="int32")
        arr_repr = format_array(arr)
        self.assertEqual(arr_repr, "[1, 2, 3]")

    def test_int_array_large_numbers(self):
        arr = array([1e9, 2e9, 3e9], dtype="int64")
        arr_repr = format_array(arr)
        self.assertEqual(arr_repr, "[1e+09, 2e+09, 3e+09]")
