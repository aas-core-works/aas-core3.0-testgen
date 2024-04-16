"""
Collect example texts which match / don't match regular expressions.

Some frozen_examples are manually curated, while others are fuzzed by Hypothesis.
Since we want to generate the test data in a deterministic manner, we do not
automatically fuzz the patterns on-the-fly.
"""
# pylint: disable=line-too-long

import collections
from typing import Mapping, MutableMapping, List

from aas_core_codegen import intermediate

from aas_core3_0_testgen import common
from aas_core3_0_testgen.frozen_examples._types import Examples

# noinspection SpellCheckingInspection

BY_PATTERN: Mapping[str, Examples] = collections.OrderedDict(
    [
        # Version type, revision type
        (
            "^(0|[1-9][0-9]*)$",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("zero", "0"),
                        ("one", "1"),
                        ("two_digits", "10"),
                        ("three_digits", "120"),
                        ("four_digits", "1230"),
                        ("fuzzed_01", "59"),
                        ("fuzzed_02", "116"),
                        ("fuzzed_03", "7"),
                        ("fuzzed_04", "32"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [("negative", "-1"), ("dot", "1.0"), ("letter", "1.0rc1")]
                ),
            ),
        ),
        # Date-time UTC
        (
            "^-?(([1-9][0-9][0-9][0-9]+)|(0[0-9][0-9][0-9]))-((0[1-9])|(1[0-2]))-((0[1-9])|([12][0-9])|(3[01]))T(((([01][0-9])|(2[0-3])):[0-5][0-9]:([0-5][0-9])(\\.[0-9]+)?)|24:00:00(\\.0+)?)(Z|\\+00:00|-00:00)$",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("random_positive", "2022-04-01T01:02:03Z"),
                        ("midnight_with_zeros", "2022-04-01T00:00:00Z"),
                        ("midnight_with_24_hours", "2022-04-01T24:00:00Z"),
                        (
                            "very_large_year",
                            "123456789012345678901234567-04-01T00:00:00Z",
                        ),
                        (
                            "very_long_fractional_second",
                            "2022-04-01T00:00:00.1234567890123456789012345678901234567890Z",
                        ),
                        (
                            "year_1_bce_is_a_leap_year",
                            "-0001-02-29T01:02:03Z",
                        ),
                        (
                            "year_5_bce_is_a_leap_year",
                            "-0005-02-29T01:02:03Z",
                        ),
                        (
                            "plus_zero_offset",
                            "2022-04-01T24:00:00+00:00",
                        ),
                        (
                            "minus_zero_offset",
                            "2022-04-01T24:00:00-00:00",
                        ),
                        ("fuzzed_01", "0013-10-11T24:00:00.000000Z"),
                        ("fuzzed_02", "0001-01-01T00:00:00Z"),
                        ("fuzzed_03", "-3020-08-21T24:00:00.0Z"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("only_date", "2022-04-01"),
                        ("only_date_with_time_zone", "2022-04-01Z"),
                        ("date_time_without_zone", "2022-04-01T01:02:03"),
                        ("date_time_with_offset", "2022-04-01T01:02:03+02:00"),
                        ("without_seconds", "2022-04-01T01:02Z"),
                        ("without_minutes", "2022-04-01T01Z"),
                        (
                            "date_time_with_UTC_and_suffix",
                            "2022-04-01T01:02:03Z-unexpected-suffix",
                        ),
                        ("negatively_fuzzed_01", "hh?aåx윳\x10[\x82\x15 K/"),
                        (
                            "negatively_fuzzed_02",
                            "<1\U0003ca06\U00088dd0Å\\H\U000c0a13",
                        ),
                        ("negatively_fuzzed_03", "𢬣\U0004287cÍ·ð\x98²+\x9a\U0004117f"),
                        ("negatively_fuzzed_04", "\U0004a4b3ð\x8d\x85\U0004742f"),
                        ("negatively_fuzzed_05", "\U000e2bbee\U0001354d\x97ñ>"),
                        ("negatively_fuzzed_06", "\U00103da6𮝸"),
                        ("negatively_fuzzed_07", "匟16È\x12\U000150e0"),
                        ("negatively_fuzzed_08", "hh"),
                        ("negatively_fuzzed_09", "E\x85𑄦𠧃Z"),
                        (
                            "negatively_fuzzed_10",
                            "\U000c9efd\U000c9efd\U0007bafe\U0001bfa8\U0010908c\U00013eb6",
                        ),
                    ]
                ),
            ),
        ),
        # duration
        (
            "^-?P((([0-9]+Y([0-9]+M)?([0-9]+D)?|([0-9]+M)([0-9]+D)?|([0-9]+D))(T(([0-9]+H)([0-9]+M)?([0-9]+(\\.[0-9]+)?S)?|([0-9]+M)([0-9]+(\\.[0-9]+)?S)?|([0-9]+(\\.[0-9]+)?S)))?)|(T(([0-9]+H)([0-9]+M)?([0-9]+(\\.[0-9]+)?S)?|([0-9]+M)([0-9]+(\\.[0-9]+)?S)?|([0-9]+(\\.[0-9]+)?S))))$",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("full", "P1Y2M3DT5H20M30.123S"),
                        ("only_year", "-P1Y"),
                        ("day_seconds", "P1DT2S"),
                        ("month_seconds", "PT2M10S"),
                        ("only_seconds", "PT130S"),
                        (
                            "many_many_seconds",
                            "PT1234567890"
                            "1234567890"
                            "1234567890"
                            "1234567890"
                            "1234567890"
                            "1234567890"
                            "1234567890"
                            "1234567890S",
                        ),
                        (
                            "long_second_fractal",
                            "PT1."
                            "1234567890"
                            "1234567890"
                            "1234567890"
                            "1234567890"
                            "1234567890"
                            "1234567890"
                            "1234567890"
                            "1234567890S",
                        ),
                        ("fuzzed_01", "-P009D"),
                        ("fuzzed_02", "P5Y36660767143M"),
                        ("fuzzed_03", "-PT01332.1S"),
                        ("fuzzed_04", "-P11DT142M"),
                        ("fuzzed_05", "PT88M48936316289.34291243605107045S"),
                        ("fuzzed_06", "-P1M923D"),
                        ("fuzzed_07", "-PT0.332S"),
                        ("fuzzed_08", "-PT313148178698146281H866062127724898M"),
                        ("fuzzed_09", "-PT1.5375209S"),
                        ("fuzzed_10", "PT18688M"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("integer", "1234"),
                        ("leading_P_missing", "1Y"),
                        ("separator_T_missing", "P1S"),
                        ("negative_years", "P-1Y"),
                        ("positive_year_negative_months", "P1Y-1M"),
                        ("the_order_matters", "P1M2Y"),
                    ]
                ),
            ),
        ),
        # is_BCP_47_for_english
        (
            "^(en|EN)(-.*)?$",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("just_english_lowercase", "en"),
                        ("just_english_uppercase", "EN"),
                        ("english_lowercase_great_britain", "en-GB"),
                        ("english_lowercase_south_africa", "en-ZA"),
                        ("english_uppercase_great_britain", "en-GB"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("german_lowercase", "de"),
                        ("german_uppercase", "DE"),
                        ("german_swiss", "de-CH"),
                    ]
                ),
            ),
        ),
        # XML serializable string
        (
            "^[\\x09\\x0A\\x0D\\x20-\\uD7FF\\uE000-\\uFFFD\\U00010000-\\U0010FFFF]*$",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("fuzzed_01", "11ÕÑ\U00010ee8´K\U00102b2de<\U000e15de¨ngA"),
                        ("fuzzed_02", "𠤢4𠤢"),
                        ("fuzzed_03", "[\\h$\U00052e9fìÖċ\x8a1¿"),
                        ("fuzzed_04", "öĖa\U0010d8e1\x99|"),
                        ("fuzzed_05", "J5"),
                        ("fuzzed_06", "Ûă<P\U000e8c7d²|dn\x9cÞ®"),
                        ("fuzzed_07", "6"),
                        ("fuzzed_08", "\U000a444cM𪠇\U0001b50a\U00082132"),
                        ("fuzzed_09", "<ă<P\U000e8c7d²|dn\x9cÞ®"),
                        ("fuzzed_10", "0"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        (
                            "negatively_fuzzed_01",
                            "\U00086b7aØõ\U00015e66,å½Ý\x92½\U000c5b6b\U000d0635\U0008817a©\x00\x92Ü",
                        ),
                        ("negatively_fuzzed_02", "餍\x17½é"),
                        (
                            "negatively_fuzzed_03",
                            "\U000fea28AD\x0f\U000ca696\x85\U000eff4fÕ",
                        ),
                        ("negatively_fuzzed_04", "ºò\x18\x7f"),
                        (
                            "negatively_fuzzed_05",
                            "A\x04\x1e»\U00069a46\U000bb36f\x17°P",
                        ),
                        ("negatively_fuzzed_06", "0\x00\x9a\U000b1206"),
                        ("negatively_fuzzed_07", "봇àc\x1dr\x0c"),
                        (
                            "negatively_fuzzed_08",
                            "Q\x1a\x90(^\\\x8a\U00052727\x8dü\U000104aa×\U000d6657\U00016006\x13",
                        ),
                        ("negatively_fuzzed_09", "Âû\x9f\x1c\x96m'ß"),
                        ("negatively_fuzzed_10", "êò\x0f\U00086254U"),
                    ]
                ),
            ),
        ),
        # ID short
        (
            "^[a-zA-Z][a-zA-Z0-9_]*$",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("fuzzed_01", "Z0"),
                        ("fuzzed_02", "gdVdV"),
                        ("fuzzed_03", "uI"),
                        ("fuzzed_04", "Yf5"),
                        ("fuzzed_05", "l5"),
                        ("fuzzed_06", "A10HQ7"),
                        ("fuzzed_07", "g39dV"),
                        ("fuzzed_08", "g1WbUAIAP_94"),
                        ("fuzzed_09", "PiXO1wyHierj"),
                        ("fuzzed_10", "fiZ"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("negatively_fuzzed_01", "L´"),
                        ("negatively_fuzzed_02", "0"),
                        (
                            "negatively_fuzzed_03",
                            "¹\U000f5c15¹s\U00035d55s?\U0008dd0a\x88z¢Z",
                        ),
                        ("negatively_fuzzed_04", "\U0005ec3e"),
                        ("negatively_fuzzed_05", "¥&J\x13\U00067124"),
                        ("negatively_fuzzed_06", "´"),
                        (
                            "negatively_fuzzed_07",
                            "é\x0c&é𪩦\U0005647f\U000f4006É\U0010957a\U000af1fd",
                        ),
                        ("negatively_fuzzed_08", "\nÑ2"),
                        ("negatively_fuzzed_09", "MÇj"),
                        ("negatively_fuzzed_10", "\U0006f42bS³G"),
                    ]
                ),
            ),
        ),
        # Content type (a.k.a. MIME type)
        (
            "^([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+/([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+([ \t]*;[ \t]*([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+=(([!#$%&'*+\\-.^_`|~0-9a-zA-Z])+|\"(([\t !#-\\[\\]-~]|[\\x80-\\xff])|\\\\([\t !-~]|[\\x80-\\xff]))*\"))*$",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("random_common_MIME_type", "application/something-random"),
                        ("only_letters", "audio/aac"),
                        ("dash", "application/x-abiword"),
                        ("dots", "application/vnd.amazon.ebook"),
                        ("plus", "application/vnd.apple.installer+xml"),
                        ("number prefix and suffix", "audio/3gpp2"),
                        # Fuzzed
                        ("fuzzed_01", "7/6qwqh6g"),
                        ("fuzzed_02", "15j/5j"),
                        (
                            "fuzzed_03",
                            '\'VbrwFrYTU/fO7NnLxq   \t; \tMX.`10dB732`X5yRy=I56Ov9Us\t ;\t\t pRb~~hdw_C%2Zf=""\t\t\t    \t\t\t \t \t\t \t  ; h=1t',
                        ),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("number", "1234"),
                        (
                            "negatively_fuzzed_01",
                            "\U000b1b2e\U000ea76e\U000c86fa7\x1eýÑ\x9d|\U001019cd",
                        ),
                        (
                            "negatively_fuzzed_02",
                            "\U000b1b2e\U000ea76e\U000c86fa7\x1eýÑ\x9d|\U001019cd",
                        ),
                        (
                            "negatively_fuzzed_03",
                            "𡔹",
                        ),
                        (
                            "negatively_fuzzed_04",
                            "ÐÐ",
                        ),
                        (
                            "negatively_fuzzed_05",
                            "\U000ddd7d§\x85°¢\U000c385a>3\U000f8d37",
                        ),
                        (
                            "negatively_fuzzed_06",
                            "q\x95d",
                        ),
                        (
                            "negatively_fuzzed_07",
                            "0",
                        ),
                        (
                            "negatively_fuzzed_08",
                            "",
                        ),
                        (
                            "negatively_fuzzed_09",
                            "\r|ä",
                        ),
                        (
                            "negatively_fuzzed_10",
                            "\U0001cbb0\U0001cbb0",
                        ),
                    ]
                ),
            ),
        ),
        # BCP 47
        (
            "^(([a-zA-Z]{2,3}(-[a-zA-Z]{3}(-[a-zA-Z]{3}){,2})?|[a-zA-Z]{4}|[a-zA-Z]{5,8})(-[a-zA-Z]{4})?(-([a-zA-Z]{2}|[0-9]{3}))?(-(([a-zA-Z0-9]){5,8}|[0-9]([a-zA-Z0-9]){3}))*(-[0-9A-WY-Za-wy-z](-([a-zA-Z0-9]){2,8})+)*(-[xX](-([a-zA-Z0-9]){1,8})+)?|[xX](-([a-zA-Z0-9]){1,8})+|((en-GB-oed|i-ami|i-bnn|i-default|i-enochian|i-hak|i-klingon|i-lux|i-mingo|i-navajo|i-pwn|i-tao|i-tay|i-tsu|sgn-BE-FR|sgn-BE-NL|sgn-CH-DE)|(art-lojban|cel-gaulish|no-bok|no-nyn|zh-guoyu|zh-hakka|zh-min|zh-min-nan|zh-xiang)))$",
            Examples(
                positives=collections.OrderedDict(
                    [
                        # NOTE (mristin):
                        # The positive examples are taken from:
                        # https://www.rfc-editor.org/rfc/bcp/bcp47.txt, Appendix A.
                        ("simple_language_subtag_1", "de"),
                        ("simple_language_subtag_2", "fr"),
                        ("simple_language_subtag_3", "ja"),
                        (
                            "simple_language_subtag_example_of_a_grandfathered_tag",
                            "i-enochian",
                        ),
                        ("language_subtag_plus_script_subtag_1", "zh-Hant"),
                        ("language_subtag_plus_script_subtag_2", "zh-Hans"),
                        ("language_subtag_plus_script_subtag_3", "sr-Cyrl"),
                        ("language_subtag_plus_script_subtag_4", "sr-Latn"),
                        ("extended_language_subtags_1", "zh-cmn-Hans-CN"),
                        ("extended_language_subtags_2", "cmn-Hans-CN"),
                        ("extended_language_subtags_3", "zh-yue-HK"),
                        ("extended_language_subtags_4", "yue-HK"),
                        ("language_script_region_1", "zh-Hans-CN"),
                        ("language_script_region_2", "sr-Latn-RS"),
                        ("language_variant_1", "sl-rozaj"),
                        ("language_variant_2", "sl-rozaj-biske"),
                        ("language_variant_3", "sl-nedis"),
                        ("language_region_variant_1", "de-CH-1901"),
                        ("language_region_variant_2", "sl-IT-nedis"),
                        ("language_script_region_variant", "hy-Latn-IT-arevela"),
                        ("language_region_1", "de-DE"),
                        ("language_region_2", "en-US"),
                        ("language_region_3", "es-419"),
                        ("private_use_subtags_1", "de-CH-x-phonebk"),
                        (
                            "private_use_subtags_2",
                            "az-Arab-x-AZE-derbend",
                        ),
                        ("private_use_registry_values_1", "x-whatever"),
                        ("private_use_registry_values_2", "qaa-Qaaa-QM-x-southern"),
                        ("private_use_registry_values_3", "de-Qaaa"),
                        (
                            "private_use_registry_values_4",
                            "sr-Latn-QM",
                        ),
                        ("private_use_registry_values_5", "sr-Qaaa-RS"),
                        ("tag_with_extension_1", "en-US-u-islamcal"),
                        ("tag_with_extension_2", "zh-CN-a-myext-x-private"),
                        ("tag_with_extension_3", "en-a-myext-b-another"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free-form text"),
                        (
                            "negatively_fuzzed_01",
                            "𝨀\U000f2076𫯶\U0005d155¼°\x07ê\x8b\x00\x04\U00015e5a",
                        ),
                        ("negatively_fuzzed_02", "Ûg\U00105156²\U00085634e´\U00097795"),
                        ("negatively_fuzzed_03", "\U000c9efd\U000c9efd"),
                        ("negatively_fuzzed_04", "0"),
                        ("negatively_fuzzed_05", "\U00100b017111"),
                        ("negatively_fuzzed_06", "\U000efe8f"),
                        ("negatively_fuzzed_07", "\U000c9efd"),
                        ("negatively_fuzzed_08", "øPí"),
                        ("negatively_fuzzed_09", "pÜ\U00083bcb®AÇ"),
                        ("negatively_fuzzed_10", "\U000f15c8\x0b~û\x95\U000d64c4"),
                    ]
                ),
            ),
        ),
        # RFC 8089
        (
            "^file:(//((localhost|(\\[((([0-9A-Fa-f]{1,4}:){6}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|::([0-9A-Fa-f]{1,4}:){5}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|([0-9A-Fa-f]{1,4})?::([0-9A-Fa-f]{1,4}:){4}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(([0-9A-Fa-f]{1,4}:)?[0-9A-Fa-f]{1,4})?::([0-9A-Fa-f]{1,4}:){3}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(([0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]{1,4})?::([0-9A-Fa-f]{1,4}:){2}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(([0-9A-Fa-f]{1,4}:){,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(([0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(([0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}|(([0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::)|[vV][0-9A-Fa-f]+\\.([a-zA-Z0-9\\-._~]|[!$&'()*+,;=]|:)+)\\]|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])|([a-zA-Z0-9\\-._~]|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=])*)))?/((([a-zA-Z0-9\\-._~]|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=]|[:@]))+(/(([a-zA-Z0-9\\-._~]|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=]|[:@]))*)*)?|/((([a-zA-Z0-9\\-._~]|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=]|[:@]))+(/(([a-zA-Z0-9\\-._~]|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=]|[:@]))*)*)?)$",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("local_absolute_path_with_scheme", "file:/path/to/somewhere"),
                        # See: https://datatracker.ietf.org/doc/html/rfc8089#appendix-B
                        (
                            "local_file_with_an_explicit_authority",
                            "file://host.example.com/path/to/file",
                        ),
                        # Fuzzed
                        ("fuzzed_01", "file:/M5/%bA:'%9c%6b%ed%00Y*/%4C=4h:d:"),
                        (
                            "fuzzed_02",
                            "file:///;/@@=%5a@@g@=S%D8:%f5;/@:/%A3&!%f8%6e;%a1!//~/%Ae%c2/%99O@,:",
                        ),
                        ("fuzzed_03", "file://localhost/C:"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("number", "1234"),
                        ("absolute_path_without_scheme", "/path/to/somewhere"),
                        ("relative_path_without_scheme", "path/to/somewhere"),
                        ("local_relative_path_with_scheme", "file:path/to/somewhere"),
                        ("negatively_fuzzed_01", "\U000a8eda\U00082f76ÃZ"),
                        ("negatively_fuzzed_02", "t#á\U0010318fXM~ùÌø\x9e\U0004c9d1"),
                        ("negatively_fuzzed_03", "\U000566ee&1𗃹þ𭀔9"),
                        ("negatively_fuzzed_04", "//"),
                        (
                            "negatively_fuzzed_05",
                            "\U000c7494\x1f\x9b\U000426da\xa0¸\U000be8e1*",
                        ),
                        ("negatively_fuzzed_06", "C"),
                        ("negatively_fuzzed_07", "\U000834ee"),
                        ("negatively_fuzzed_08", "â·\U00055392E"),
                        ("negatively_fuzzed_09", "s\U0001acc1\U00088dd0Å\\H\U000c0a13"),
                        ("negatively_fuzzed_10", "hxY"),
                    ]
                ),
            ),
        ),
    ]
)


def _assert_all_pattern_verification_functions_covered_and_not_more() -> None:
    """Assert that we have some pattern for each pattern verification function."""
    (
        symbol_table,
        constraints_by_class,
    ) = common.load_symbol_table_and_infer_constraints_for_schema()

    expected = {
        verification.pattern
        for verification in symbol_table.verification_functions
        if (
            isinstance(verification, intermediate.PatternVerification)
            # NOTE (mristin, 2023-03-01):
            # We test the ``matches_xs_*`` functions in xs_value.py.
            and not verification.name.startswith("matches_xs_")
        )
    }

    pattern_to_sources = dict()  # type: MutableMapping[str, List[str]]
    for verification in symbol_table.verification_functions:
        if not isinstance(verification, intermediate.PatternVerification):
            continue

        source = f"Verification function {verification.name}"
        if verification.pattern not in pattern_to_sources:
            pattern_to_sources[verification.pattern] = [source]
        else:
            pattern_to_sources[verification.pattern].append(source)

    for cls, class_constraints in constraints_by_class.items():
        for prop, constraints in class_constraints.patterns_by_property.items():
            for constraint in constraints:
                expected.add(constraint.pattern)
                source = f"Inferred constraint on {cls.name}.{prop.name}"

                if constraint.pattern not in pattern_to_sources:
                    pattern_to_sources[constraint.pattern] = [source]
                else:
                    pattern_to_sources[constraint.pattern].append(source)

    covered = set(BY_PATTERN.keys())

    not_covered = sorted(expected.difference(covered))
    surplus = sorted(covered.difference(expected))

    if len(not_covered) > 0:
        pattern_analysis_joined = "\n".join(
            f"{pattern!r} -> {pattern_to_sources[pattern]}" for pattern in not_covered
        )
        raise AssertionError(
            f"The following patterns from the respective pattern verification "
            f"functions were not covered:\n{pattern_analysis_joined}"
        )

    if len(surplus) > 0:
        raise AssertionError(
            f"The following patterns could not be traced back to "
            f"any pattern verification function: {surplus}"
        )


_assert_all_pattern_verification_functions_covered_and_not_more()
