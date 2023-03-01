"""
Collect example texts which match / don't match regular expressions.

Some frozen_examples are manually curated, while others are fuzzed by Hypothesis.
Since we want to generate the test data in a deterministic manner, we do not
automatically fuzz the patterns on-the-fly.
"""
# pylint: disable=line-too-long

import collections
import pathlib
from typing import Mapping, MutableMapping, List

from aas_core_codegen import intermediate
import aas_core_codegen.run
import aas_core_meta.v3

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
                        ('zero', '0'),
                        ('one', '1'),
                        ('two_digits', '10'),
                        ('three_digits', '120'),
                        ('four_digits', '1230'),
                        ('fuzzed_01', '59'),
                        ('fuzzed_02', '116'),
                        ('fuzzed_03', '7'),
                        ('fuzzed_04', '32'),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ('negative', '-1'),
                        ('dot', '1.0'),
                        ('letter', '1.0rc1')
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
                        ('just_english_lowercase', 'en'),
                        ('just_english_uppercase', 'EN'),
                        ('english_lowercase_great_britain', 'en-GB'),
                        ('english_lowercase_south_africa', 'en-ZA'),
                        ('english_uppercase_great_britain', 'en-GB'),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ('german_lowercase', 'de'),
                        ('german_uppercase', 'DE'),
                        ('german_swiss', 'de-CH')
                    ]
                ),
            ),
        ),
        # TODO (mristin, 2023-03-1): matches_XML_serializable_string
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
        # MIME type
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
                        (
                            "fuzzed_01",
                            '7/6qwqh6g   ;\t  \t\t\tSfY`0%T$j="\\£\\-\\z\\ß\\\x83\\n";\t \t\t\t \tafHag\'=Ojk;z6="àø"  \t \t\t\t\t\t;GHaV0^|#=":õsïõv\xad¢¿ÿ\\>"\t; \tse=!`B5#|91+gIZf&rwrjF  ;  \txYWL%Rl_8="Ç\\¥\\÷\\}"   \t \t \t     \t   \t;\tv="\\ü"',
                        ),
                        ("fuzzed_02", "15j/5j"),
                        (
                            "fuzzed_03",
                            '\'VbrwFrYTU/fO7NnLxq   \t; \tMX.`10dB732`X5yRy=I56Ov9Us\t ;\t\t pRb~~hdw_C%2Zf=""\t\t\t    \t\t\t \t \t\t \t  ; h=1tT.9`#~  \t ;Zn%y=atQHDeMs`a2Hbza',
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
            "^(([a-zA-Z]{2,3}(-[a-zA-Z]{3}(-[a-zA-Z]{3}){2})?|[a-zA-Z]{4}|[a-zA-Z]{5,8})(-[a-zA-Z]{4})?(-([a-zA-Z]{2}|[0-9]{3}))?(-(([a-zA-Z0-9]){5,8}|[0-9]([a-zA-Z0-9]){3}))*(-[0-9A-WY-Za-wy-z](-([a-zA-Z0-9]){2,8})+)*(-[xX](-([a-zA-Z0-9]){1,8})+)?|[xX](-([a-zA-Z0-9]){1,8})+|((en-GB-oed|i-ami|i-bnn|i-default|i-enochian|i-hak|i-klingon|i-lux|i-mingo|i-navajo|i-pwn|i-tao|i-tay|i-tsu|sgn-BE-FR|sgn-BE-NL|sgn-CH-DE)|(art-lojban|cel-gaulish|no-bok|no-nyn|zh-guoyu|zh-hakka|zh-min|zh-min-nan|zh-xiang)))$",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("only_language", "en"),
                        ("language_and_dialect", "de-CH"),
                        # Fuzzed
                        ("fuzzed_01", "x-Sw4u3ZDO-nJLabnE"),
                        (
                            "fuzzed_02",
                            "Tvwqa-500-8EQd-y-8f5-k-vqdMn7-Ohw9-CcA628-DHKP-hPAjUZ-cnr1REUf-S8-p-9X0r-wtCI-KunG3uzI-7dGUsrTu-fY7-C3-hFN-Y-ML69DgnJ-0-Y0H-TLACBVB-Z0HRibbz-yzSf8dvR-zAn-B-6h8VjcKX-jnwR-0Z8l-ghRIZ7mo-wZG7-zXHdSIV-Oy-8dH00A6L-nJY2dA1-57o8dQ-RpxkBTbE-qBJR-M-DyGDA3U-aguRfIhj-x-XmO-1u",
                        ),
                        ("fuzzed_03", "X-33DQI-g"),
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
            "^file:(//((localhost|(\\[((([0-9A-Fa-f]{1,4}:){6}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|::([0-9A-Fa-f]{1,4}:){5}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|([0-9A-Fa-f]{1,4})?::([0-9A-Fa-f]{1,4}:){4}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(([0-9A-Fa-f]{1,4}:)?[0-9A-Fa-f]{1,4})?::([0-9A-Fa-f]{1,4}:){3}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(([0-9A-Fa-f]{1,4}:){2}[0-9A-Fa-f]{1,4})?::([0-9A-Fa-f]{1,4}:){2}([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(([0-9A-Fa-f]{1,4}:){3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(([0-9A-Fa-f]{1,4}:){4}[0-9A-Fa-f]{1,4})?::([0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(([0-9A-Fa-f]{1,4}:){5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}|(([0-9A-Fa-f]{1,4}:){6}[0-9A-Fa-f]{1,4})?::)|[vV][0-9A-Fa-f]+\\.([a-zA-Z0-9\\-._~]|[!$&'()*+,;=]|:)+)\\]|([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])|([a-zA-Z0-9\\-._~]|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=])*)))?/((([a-zA-Z0-9\\-._~]|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=]|[:@]))+(/(([a-zA-Z0-9\\-._~]|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=]|[:@]))*)*)?|/((([a-zA-Z0-9\\-._~]|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=]|[:@]))+(/(([a-zA-Z0-9\\-._~]|%[0-9A-Fa-f][0-9A-Fa-f]|[!$&'()*+,;=]|[:@]))*)*)?)$",
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
        # xs:dateTimeStamp with UTC
        (
            "^-?(([1-9][0-9][0-9][0-9]+)|(0[0-9][0-9][0-9]))-((0[1-9])|(1[0-2]))-((0[1-9])|([12][0-9])|(3[01]))T(((([01][0-9])|(2[0-3])):[0-5][0-9]:([0-5][0-9])(\\.[0-9]+)?)|24:00:00(\\.0+)?)Z$",
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
    ]
)

def _assert_all_pattern_verification_functions_covered_and_not_more()->None:
    """Assert that we have some pattern for each pattern verification function."""
    (
        symbol_table_atok,
        error,
    ) = (
        aas_core_codegen.run.load_model(pathlib.Path(aas_core_meta.v3.__file__))
    )
    if error is not None:
        raise RuntimeError(error)
    assert symbol_table_atok is not None
    symbol_table = symbol_table_atok[0]

    expected = {
        verification.pattern
        for verification in symbol_table.verification_functions
        if (
                isinstance(verification, intermediate.PatternVerification)
                # NOTE (mristin, 2023-03-01):
                # We test the ``matches_xs_*`` functions in xs_value.py.
                and not verification.name.startswith('matches_xs_')
        )
    }

    pattern_to_verifications = dict(
    )  # type: MutableMapping[str, List[intermediate.PatternVerification]]
    for verification in symbol_table.verification_functions:
        if not isinstance(verification, intermediate.PatternVerification):
            continue

        if verification.pattern not in pattern_to_verifications:
            pattern_to_verifications[verification.pattern] = [verification]
        else:
            pattern_to_verifications[verification.pattern].append(verification)

    covered = set(BY_PATTERN.keys())

    not_covered = sorted(expected.difference(covered))
    surplus = sorted(covered.difference(expected))

    if len(not_covered)>0:
        pattern_analysis = []  # type: List[str]

        for pattern in not_covered:
            verification_names = [
                verification.name
                for verification in pattern_to_verifications[pattern]
            ]
            pattern_analysis.append(
                f"{pattern} -> {verification_names}"
            )

        pattern_analysis_joined = "\n".join(pattern_analysis)
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
