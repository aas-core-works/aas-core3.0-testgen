"""Collect frozen_examples and counter-frozen_examples of XSD values."""
import collections
from typing import Mapping

import aas_core_meta.v3

from aas_core3_0_testgen.frozen_examples._types import Examples

# pylint: disable=line-too-long

# noinspection SpellCheckingInspection

BY_VALUE_TYPE: Mapping[str, Examples] = collections.OrderedDict(
    [
        (
            "xs:anyURI",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("integer", "1234"),
                        ("absolute_path_without_scheme", "/path/to/somewhere"),
                        ("relative_path_without_scheme", "path/to/somewhere"),
                        ("URI", "https://github.com/aas-core-works/aas-core-codegen"),
                        ("fuzzed_01", "HCSxO:"),
                        ("fuzzed_02", "?\U000fe800#/"),
                        ("fuzzed_03", "iU6r56h-XH22E1:"),
                        (
                            "fuzzed_04",
                            "/&&/::/(/%Dc:/þ/(%Ac:%C1:%25::,*/=ċ/@%d3%CDs%adZĉt%9B/%fD@::¦%06,:(v/@Ł$:Į%F8/;;%BC@+Ĳ:Ŝ%95@/ġ%2b@::%2c%e5/=(R:/\U0004674f=Ý,:Ã:%07%A7%Dd(,@///@%4D%fd+%0D:Ĉ:@$ìY%DC%eA\U0008cc77\U00099d82'/+%B2\U000b5762%Af%E2@%D1*:*\U0003147a\U0006daac@/@$/:'/'%bb%6d$/j%BF%c3!:*@/𪮀Ò%3Dľ%FB$=:%EB/F@/'Ĥp/K$%ED'°/:/#5/",
                        ),
                        ("fuzzed_05", ""),
                        (
                            "fuzzed_06",
                            "/6:ģ@ś//@ħ%eB\U0001c22d@/;£;%fC;%08Đ%c8%5b//;:%51#/)?/=/ô??%F0@?",
                        ),
                        ("fuzzed_07", "@Ċ@=%ac/%Ecu%2a"),
                        ("fuzzed_08", "//%Ea/=*?\ue006"),
                        (
                            "fuzzed_09",
                            "//%2f%6B!+ď%B6ĶĮ!¸\U00086d3d%9f@252.234.9.112:365//::\U0006aa9d%Bc%Ab:,%B6??#Ī?/",
                        ),
                        (
                            "fuzzed_10",
                            "%Ac@@%42@@@%3a/:*/@?'𢡦//\ue075\ue07e\U000f6061!\ue0a9/&//@??苁",
                        ),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("too_many_fragments", "http://datypic.com#frag1#frag2"),
                        (
                            "percentage_followed_by_non_two_hexadecimal_digits",
                            "http://datypic.com#f% rag",
                        ),
                        ("negatively_fuzzed_01", "``"),
                        (
                            "negatively_fuzzed_02",
                            "yE;\x9a¶)Æ¬fQ\x13§A\U000975ed©\U00014675\x8a\U0003c040",
                        ),
                        ("negatively_fuzzed_03", "W:𠦳\x13\x8f¨9\x83"),
                        ("negatively_fuzzed_04", "''1\x83𐧂"),
                        ("negatively_fuzzed_05", "''ÿ\U00108c1a쎸Èº«Ù"),
                        ("negatively_fuzzed_06", "`0"),
                        ("negatively_fuzzed_07", "Ô·Ù\x9f\U000c8e74»\x06Ô#\x14FBÉÛÍ~O"),
                        ("negatively_fuzzed_08", "\U0004a254\x05¿."),
                        (
                            "negatively_fuzzed_09",
                            "Ꜭ倀\U000b4bf8½¼\x00ì\tº;Ï\U000847b7w\x97\U000b0dd9D𥙌º|",
                        ),
                        ("negatively_fuzzed_10", "\x97LùÙ"),
                    ]
                ),
            ),
        ),
        (
            "xs:base64Binary",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("without_space_uppercase", "0FB8"),
                        ("without_space_lowercase", "0fb8"),
                        ("whitespace_is_allowed_anywhere_in_the_value", "0 FB8 0F+9"),
                        ("equals_signs_are_used_for_padding", "0F+40A=="),
                        ("an_empty_value_is_valid", ""),
                        (
                            "fuzzed_01",
                            "RJ I k 7 c /F / 1 J8F o 0ivZ v AE 3bj ASP y PI k+ 1 fku W 5M=",
                        ),
                        (
                            "fuzzed_02",
                            "Ie 9 20 Y F 5 Ve9 Y c 0W rH p 2 FQaS /xw /t RtE=",
                        ),
                        ("fuzzed_03", "n3wT"),
                        ("fuzzed_04", "wfw E"),
                        ("fuzzed_05", "jj5 n"),
                        ("fuzzed_06", "j j5 n"),
                        ("fuzzed_07", "S w SO 5 S5r"),
                        ("fuzzed_08", "UBU iUBU iQ n cy q 7wK"),
                        ("fuzzed_09", "HU UH"),
                        ("fuzzed_10", "00000000"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("an_odd_number_of_characters_is_not_valid", "FB8"),
                        ("equals_signs_may_only_appear_at_the_end", "==0F"),
                        ("negatively_fuzzed_01", "©l·\x8eÌ𠸄T\x19Ø\x1agd¥6ZÄ"),
                        ("negatively_fuzzed_02", "1𑂘\x1a\xa0´`𦞙Ù\x9bÃ\x8a"),
                        ("negatively_fuzzed_03", "#/"),
                        ("negatively_fuzzed_04", "0"),
                        ("negatively_fuzzed_05", "\U000a4788\xa0\U00077a4e\U00060d14ú"),
                        ("negatively_fuzzed_06", "]]P"),
                        ("negatively_fuzzed_07", "ȏ®BFo^\x0e罳Ø"),
                        ("negatively_fuzzed_08", "í"),
                        ("negatively_fuzzed_09", "\U00055d62C\xad\x06\x02ÚH\x97Ô"),
                        ("negatively_fuzzed_10", "\x82"),
                    ]
                ),
            ),
        ),
        (
            "xs:boolean",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("true_in_letters", "true"),
                        ("true_as_number", "1"),
                        ("false_in_letters", "false"),
                        ("false_as_number", "0"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("true_in_uppercase", "TRUE"),
                        ("true_in_camelcase", "True"),
                        ("false_in_uppercase", "FALSE"),
                        ("false_in_camelcase", "False"),
                        ("true_as_number_with_leading_zeros", "0001"),
                        ("false_as_number_with_leading_zeros", "0000"),
                        ("negatively_fuzzed_01", "\U000bc161\U000da2326\U000da232"),
                        (
                            "negatively_fuzzed_02",
                            "/\U000787ef\x82»uÎÃ#öÚ¸\x1dÔ\U000cfd24\x1e",
                        ),
                        ("negatively_fuzzed_03", "\U00035bf4"),
                        ("negatively_fuzzed_04", "1Ñ¯ã¬]\x1aä"),
                        ("negatively_fuzzed_05", "\u2007º\U0004cbfdn"),
                        ("negatively_fuzzed_06", "¹½\x174x|톎¬§T\U00073818"),
                        (
                            "negatively_fuzzed_07",
                            "\U00011770\U0004a8afZ5\x1b \U001057b3ë{Â",
                        ),
                        ("negatively_fuzzed_08", "\U000a4ff6n\x11"),
                        ("negatively_fuzzed_09", "\xad\U0005e82b\U000338e2WX\x1b"),
                        ("negatively_fuzzed_10", "\U000aae0fza\U000368bb\x89"),
                    ]
                ),
            ),
        ),
        (
            "xs:date",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("date", "2022-04-01"),
                        ("date_with_utc", "2022-04-01Z"),
                        ("date_with_positive_offset", "2022-04-01+02:34"),
                        ("date_with_zero_offset", "2022-04-01+00:00"),
                        ("date_with_negative_offset", "2022-04-01-02:00"),
                        (
                            "date_with_large_positive_year",
                            "12345678901234567890123456789012345678901234567890-04-01",
                        ),
                        (
                            "date_with_large_negative_year",
                            "-12345678901234567890123456789012345678901234567890-04-01",
                        ),
                        (
                            "year_1_bce_is_a_leap_year",
                            "-0001-02-29",
                        ),
                        (
                            "year_5_bce_is_a_leap_year",
                            "-0005-02-29",
                        ),
                        ("fuzzed_01", "0705-04-10+14:00"),
                        ("fuzzed_02", "-0236-12-31Z"),
                        ("fuzzed_03", "9088-11-06"),
                        ("fuzzed_04", "-7506-08-02"),
                        ("fuzzed_05", "-3637143-04-09"),
                        ("fuzzed_06", "-0311-11-30"),
                        ("fuzzed_07", "-0844-11-30"),
                        ("fuzzed_08", "0111-04-04"),
                        ("fuzzed_09", "0412-04-08-10:58"),
                        ("fuzzed_10", "0520-01-01"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("date_time_without_zone", "2022-04-01T01:02:03"),
                        ("date_time_with_offset", "2022-04-01T01:02:03+02:00"),
                        ("date_time_with_UTC", "2022-04-01T01:02:03Z"),
                        ("non_existing_february_29th", "2011-02-29"),
                        ("date_with_invalid_positive_offset", "2022-04-01+15:00"),
                        ("date_with_invalid_negative_offset", "2022-04-01-15:00"),
                        ("date_with_seconds_in_offset", "2022-04-01+02:00:12"),
                        ("year_zero_doesnt_exist", "0000-01-02"),
                        # NOTE (mristin, 2022-10-30):
                        # Year 1 BCE is a leap year.
                        ("year_4_bce_february_29th", "-0004-02-29"),
                    ]
                ),
            ),
        ),
        (
            "xs:dateTime",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("date_time_without_zone", "2022-04-01T01:02:03"),
                        ("date_time_with_UTC", "2022-04-01T01:02:03Z"),
                        ("date_time_with_positive_offset", "2022-04-01T01:02:03+02:00"),
                        ("date_time_with_zero_offset", "2022-04-01T01:02:03+00:00"),
                        ("date_time_with_negative_offset", "2022-04-01T01:02:03+00:00"),
                        (
                            "date_time_with_long_fractional_seconds",
                            "2022-04-01T01:02:03.0123456789Z",
                        ),
                        (
                            "date_time_with_large_positive_year",
                            "12345678901234567890123456789012345678901234567890-04-01T01:02:03",
                        ),
                        (
                            "date_time_with_large_negative_year",
                            "-12345678901234567890123456789012345678901234567890-04-01T01:02:03",
                        ),
                        ("midnight_with_zeros", "2022-04-01T00:00:00"),
                        ("midnight_with_24_hours", "2022-04-01T24:00:00"),
                        (
                            "year_1_bce_is_a_leap_year",
                            "-0001-02-29T01:02:03",
                        ),
                        (
                            "year_5_bce_is_a_leap_year",
                            "-0005-02-29T01:02:03",
                        ),
                        ("fuzzed_01", "-0811-10-21T24:00:00.000000Z"),
                        ("fuzzed_02", "-0819-11-21T24:00:00.00Z"),
                        ("fuzzed_03", "-665280014-06-30T21:15:16Z"),
                        ("fuzzed_04", "-0811-11-21T24:00:00.0000Z"),
                        ("fuzzed_05", "0532-09-07T18:47:52+14:00"),
                        ("fuzzed_06", "0707-11-02T24:00:00.00"),
                        ("fuzzed_07", "-0003-12-20T22:53:54.02567"),
                        ("fuzzed_08", "-1092-02-25T24:00:00.0000"),
                        ("fuzzed_09", "-6602-06-30T24:00:00"),
                        ("fuzzed_10", "-2111111-08-31T23:58:19.269348"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("date", "2022-04-01"),
                        ("date_with_time_zone", "2022-04-01Z"),
                        ("non_existing_february_29th", "2011-02-29T01:02:03Z"),
                        (
                            "date_time_with_invalid_positive_offset",
                            "2022-04-01T01:02:03+15:00",
                        ),
                        (
                            "date_time_with_invalid_negative_offset",
                            "2022-04-01T01:02:03-15:00",
                        ),
                        (
                            "date_time_with_seconds_in_offset",
                            "2022-04-01T01:02:03+02:00:12",
                        ),
                        ("without_seconds", "2022-04-01T01:02Z"),
                        ("without_minutes", "2022-04-01T01Z"),
                        (
                            "date_time_with_unexpected_suffix",
                            "2022-04-01T01:02:03Z-unexpected-suffix",
                        ),
                        (
                            "date_time_with_unexpected_prefix",
                            "unexpected-prefix-2022-04-01T01:02:03Z",
                        ),
                        ("year_zero_doesnt_exist", "0000-01-02T01:02:03"),
                        # NOTE (mristin, 2022-10-30):
                        # Year 1 BCE is a leap year.
                        ("year_4_bce_february_29th", "-0004-02-29T01:02:03"),
                    ]
                ),
            ),
        ),
        (
            "xs:decimal",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("integer", "1234"),
                        ("decimal", "1234.01234"),
                        ("integer_with_preceding_zeros", "0001234"),
                        ("decimal_with_preceding_zeros", "0001234.01234"),
                        (
                            "decimal_with_long_fractional",
                            "1234.1234567890123456789012345678901234567890123456789012345678901234567890",
                        ),
                        (
                            "very_large_decimal",
                            "123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890.12345678901234567890123456789012345678901234567890123456789012345678901234567890",
                        ),
                        ("fuzzed_01", ".33324"),
                        ("fuzzed_02", "01195"),
                        ("fuzzed_03", "+875"),
                        ("fuzzed_04", "-8"),
                        ("fuzzed_05", "-0.0"),
                        ("fuzzed_06", "-13522106"),
                        ("fuzzed_07", "+10"),
                        ("fuzzed_08", "-030725"),
                        ("fuzzed_09", ".3"),
                        ("fuzzed_10", "0061707"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                    ]
                ),
            ),
        ),
        (
            "xs:double",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("integer", "1234"),
                        ("double", "1234.01234"),
                        ("integer_with_preceding_zeros", "0001234"),
                        ("with_preceding_zeros", "0001234.01234"),
                        ("scientific_notation_negative", "-12.34e56"),
                        ("scientific_notation_positive", "+12.34e56"),
                        ("scientific_notation", "12.34e56"),
                        ("scientific_notation_positive_exponent", "12.34e+56"),
                        ("scientific_notation_negative_exponent", "12.34e-56"),
                        ("minus_inf", "-INF"),
                        ("inf", "INF"),
                        ("nan", "NaN"),
                        (
                            "loss_of_precision_is_not_detected_by_design",
                            "1234.1234567890123456789012345678901234567890123456789012345678901234567890",
                        ),
                        # See https://stackoverflow.com/questions/48630106/what-are-the-actual-min-max-values-for-float-and-double-c
                        (
                            "lowest",
                            "-179769313486231570814527423731704356798070567525844996598917476803157260780028538760589558632766878171540458953514382464234321326889464182768467546703537516986049910576551282076245490090389328944075868508455133942304583236903222948165808559332123348274797826204144723168738177180919299881250404026184124858368",
                        ),
                        (
                            "max",
                            "179769313486231570814527423731704356798070567525844996598917476803157260780028538760589558632766878171540458953514382464234321326889464182768467546703537516986049910576551282076245490090389328944075868508455133942304583236903222948165808559332123348274797826204144723168738177180919299881250404026184124858368",
                        ),
                        # See https://en.wikipedia.org/wiki/Double-precision_floating-point_format
                        (
                            "min_subnormal_positive",
                            "0.0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000049406564584124654417656879286822137236505980261432476442558568250067550727020875186529983636163599237979656469544571773092665671035593979639877479601078187812630071319031140452784581716784898210368872",
                        ),
                        (
                            "max_subnormal",
                            "0.000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000022250738585072008890245868760858598876504231122409594654935248025624400092282356951787758888037591552642309780950434312085877387158357291821993020294379224223559819827501242041788969571311791082261044",
                        ),
                        (
                            "min_normal_positive",
                            "0.000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000022250738585072013830902327173324040642192159804623318305533274168872044348139181958542831590125110205640673397310358110051524341615534601088560123853777188211307779935320023304796101474425836360719216",
                        ),
                        ("fuzzed_01", ".1118"),
                        ("fuzzed_02", "-.662"),
                        ("fuzzed_03", ".0E0"),
                        ("fuzzed_04", ".4"),
                        ("fuzzed_05", ".11"),
                        ("fuzzed_06", "+76E-86"),
                        ("fuzzed_07", "-.662"),
                        ("fuzzed_08", "1e+7"),
                        ("fuzzed_09", "-.66E-45"),
                        ("fuzzed_10", "140206134"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("inf_case_matters", "inf"),
                        ("nan_case_matters", "nan"),
                        ("plus_inf", "+INF"),
                        ("no_fraction_in_scientific_notation", "12.34e5.6"),
                        ("too_large", "1.123456789e1234567890"),
                    ]
                ),
            ),
        ),
        (
            "xs:duration",
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
        (
            "xs:float",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("integer", "1234"),
                        ("float", "1234.01234"),
                        ("integer_with_preceding_zeros", "0001234"),
                        ("with_preceding_zeros", "0001234.01234"),
                        ("scientific_notation_negative", "-12.34e16"),
                        ("scientific_notation_positive", "+12.34e16"),
                        ("scientific_notation", "12.34e16"),
                        ("scientific_notation_positive_exponent", "12.34e+16"),
                        ("scientific_notation_negative_exponent", "12.34e-16"),
                        ("negative_inf", "-INF"),
                        ("inf", "INF"),
                        ("nan", "NaN"),
                        (
                            "loss_of_precision_is_not_detected_by_design",
                            "1234.1234567890123456789012345678901234567890123456789012345678901234567890",
                        ),
                        # See https://en.wikipedia.org/wiki/Single-precision_floating-point_format
                        (
                            "smallest_positive_subnormal",
                            "0.00000000000000000000000000000000000000000000140129846432481707092372958328991613128026194187651577175706828388979108268586060148663818836212158203125",
                        ),
                        (
                            "largest_subnormal",
                            "0.00000000000000000000000000000000000001175494210692441075487029444849287348827052428745893333857174530571588870475618904265502351336181163787841796875",
                        ),
                        (
                            "smallest_positive_normal",
                            "0.000000000000000000000000000000000000011754943508222875079687365372222456778186655567720875215087517062784172594547271728515625",
                        ),
                        ("largest_normal", "340282346638528859811704183484516925440"),
                        ("largest_number_less_than_one", "0.999999940395355224609375"),
                        (
                            "smallest_number_larger_than_one",
                            "1.00000011920928955078125",
                        ),
                        ("fuzzed_01", "-.80E0"),
                        ("fuzzed_02", "-147E7"),
                        ("fuzzed_03", "18"),
                        ("fuzzed_04", ".1532E+16"),
                        ("fuzzed_05", "+44.6393"),
                        ("fuzzed_06", ".5885e-29"),
                        ("fuzzed_07", "1e-7"),
                        ("fuzzed_08", "+732.55619"),
                        ("fuzzed_09", ".1E05"),
                        ("fuzzed_10", "1102"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("inf_case_matters", "inf"),
                        ("nan_case_matters", "nan"),
                        ("plus_inf", "+INF"),
                        ("no_fraction_in_scientific_notation", "12.34e5.6"),
                        ("too_large", "1.123456789e1234567890"),
                    ]
                ),
            ),
        ),
        (
            "xs:gDay",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("single_digit_day_without_zone", "---01"),
                        ("double_digit_day_without_zone", "---15"),
                        ("day_not_existing_in_all_months_without_zone", "---31"),
                        ("utc_zone", "---01Z"),
                        ("positive_offset", "---01+02:00"),
                        ("zero_offset", "---01+00:00"),
                        ("negative_offset", "---01-04:00"),
                        ("fuzzed_01", "---23Z"),
                        ("fuzzed_02", "---24"),
                        ("fuzzed_03", "---10"),
                        ("fuzzed_04", "---30-14:00"),
                        ("fuzzed_05", "---31-09:25"),
                        ("fuzzed_06", "---17Z"),
                        ("fuzzed_07", "---30+00:00"),
                        ("fuzzed_08", "---30-10:11"),
                        ("fuzzed_09", "---22Z"),
                        ("fuzzed_10", "---30Z"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("unexpected_suffix", "--30-"),
                        ("day_outside_of_range", "---35"),
                        ("missing_leading_digit", "---5"),
                        ("missing_leading_dashes", "15"),
                        ("invalid_positive_offset", "---01+15:00"),
                        ("invalid_negative_offset", "---01-15:00"),
                        ("invalid_offset_with_seconds", "---01+15:00:12"),
                    ]
                ),
            ),
        ),
        (
            "xs:gMonth",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("single_digit_month_without_zone", "--05"),
                        ("double_digit_month_without_zone", "--11"),
                        ("utc_zone", "--11Z"),
                        ("positive_offset", "--11+02:00"),
                        ("zero_offset", "--11+00:00"),
                        ("negative_offset", "--11-04:00"),
                        ("fuzzed_01", "--11-13:34"),
                        ("fuzzed_02", "--10+14:00"),
                        ("fuzzed_03", "--10+07:39"),
                        ("fuzzed_04", "--11-05:22"),
                        ("fuzzed_05", "--01"),
                        ("fuzzed_06", "--12Z"),
                        ("fuzzed_07", "--10-13:30"),
                        ("fuzzed_08", "--07"),
                        ("fuzzed_09", "--11-10:05"),
                        ("fuzzed_10", "--11+12:33"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("unexpected_prefix_and_suffix", "-01-"),
                        ("month_outside_of_range", "--13"),
                        ("missing_leading_digit", "--1"),
                        ("missing_leading_dashes", "01"),
                        ("invalid_positive_offset", "--11+15:00"),
                        ("invalid_negative_offset", "--11-15:00"),
                        ("invalid_offset_with_seconds", "--11+02:00:12"),
                    ]
                ),
            ),
        ),
        (
            "xs:gMonthDay",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("single_digit_month_single_digit_day_without_zone", "--05-01"),
                        ("double_digit_month_single_digit_day_without_zone", "--11-01"),
                        ("double_digit_month_double_digit_day_without_zone", "--11-14"),
                        ("february_29th_which_does_not_exist_in_all_years", "--02-29"),
                        ("utc_zone", "--11-01Z"),
                        ("positive_offset", "--11-01+02:00"),
                        ("zero_offset", "--11-01+02:00"),
                        ("negative_offset", "--11-01-04:00"),
                        ("fuzzed_01", "--11-20"),
                        ("fuzzed_02", "--12-06"),
                        ("fuzzed_03", "--12-01"),
                        ("fuzzed_04", "--11-21+14:00"),
                        ("fuzzed_05", "--10-07"),
                        ("fuzzed_06", "--10-30"),
                        ("fuzzed_07", "--12-27"),
                        ("fuzzed_08", "--04-30"),
                        ("fuzzed_09", "--10-10-14:00"),
                        ("fuzzed_10", "--10-11Z"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("unexpected_prefix_and_suffix", "-01-30-"),
                        ("day_outside_of_range", "--01-35"),
                        ("non_existing_april_31st", "--04-31"),
                        ("missing_leading_digit", "--1-5"),
                        ("missing_leading_dashes", "01-15"),
                        ("invalid_positive_offset", "--11-01+15:00"),
                        ("invalid_negative_offset", "--11-01-15:00"),
                        ("invalid_offset_with_seconds", "--11-01+02:00:12"),
                    ]
                ),
            ),
        ),
        (
            "xs:gYear",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("year_without_zone", "2001"),
                        ("five_digit_year", "20000"),
                        (
                            "very_large_positive_year",
                            "123456789012345678901234567890123456789012345678901234567890",
                        ),
                        (
                            "very_large_negative_year",
                            "-123456789012345678901234567890123456789012345678901234567890",
                        ),
                        ("utc_zone", "2001Z"),
                        ("positive_offset", "2001+02:00"),
                        ("zero_offset", "2001+00:00"),
                        ("negative_offset", "2001-04:00"),
                        ("negative_year", "-2001"),
                        ("five_digit_negative_year", "-20000"),
                        ("fuzzed_01", "0740-07:36"),
                        ("fuzzed_02", "125774274"),
                        ("fuzzed_03", "-0444"),
                        ("fuzzed_04", "0000"),
                        ("fuzzed_05", "-0111+14:00"),
                        ("fuzzed_06", "11111"),
                        ("fuzzed_07", "973419862"),
                        ("fuzzed_08", "1717608219759Z"),
                        ("fuzzed_09", "-0863"),
                        ("fuzzed_10", "-0109+14:00"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("missing_century", "01"),
                        ("unexpected_month", "2001-12"),
                        ("invalid_positive_offset", "2001+15:00"),
                        ("invalid_negative_offset", "2001-15:00"),
                        ("invalid_offset_with_seconds", "2001+02:00:12"),
                    ]
                ),
            ),
        ),
        (
            "xs:gYearMonth",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_year_month", "2001-10"),
                        (
                            "very_large_positive_year",
                            "123456789012345678901234567890123456789012345678901234567890-04",
                        ),
                        ("with_utc_zone", "2001-10Z"),
                        ("with_positive_offset", "2001-10+02:00"),
                        ("with_zero_offset", "2001-10+00:00"),
                        ("with_negative_offset", "2001-10-02:00"),
                        ("negative_year", "-2001-10"),
                        ("five_digit_negative_year", "-20000-04"),
                        (
                            "very_large_negative_year",
                            "-123456789012345678901234567890123456789012345678901234567890-04",
                        ),
                        ("fuzzed_01", "-65822-10"),
                        ("fuzzed_02", "0730-10-14:00"),
                        ("fuzzed_03", "-4111-11Z"),
                        ("fuzzed_04", "1000-01"),
                        ("fuzzed_05", "0010-09-14:00"),
                        ("fuzzed_06", "0555-07"),
                        ("fuzzed_07", "0404-11-14:00"),
                        ("fuzzed_08", "-0882-11+14:00"),
                        ("fuzzed_09", "-0230-09Z"),
                        ("fuzzed_10", "0119-12-14:00"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("missing_month", "2001"),
                        ("month_out_of_range", "2001-13"),
                        ("missing_century", "01-13"),
                        ("invalid_positive_offset", "2001-10+15:00"),
                        ("invalid_negative_offset", "2001-10-15:00"),
                        ("invalid_offset_with_seconds", "2001-10+02:00:12"),
                    ]
                ),
            ),
        ),
        (
            "xs:hexBinary",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("one_one", "11"),
                        ("one_two", "12"),
                        ("one_two_three_four", "1234"),
                        (
                            "long_random_hex",
                            "3c3f786d6c2076657273696f6e3d22312e302220656e636f64696e67",
                        ),
                        ("fuzzed_01", "f22fF9004a6D9AD1"),
                        ("fuzzed_02", "00"),
                        ("fuzzed_03", "FFFFfef3CB"),
                        ("fuzzed_04", "A8"),
                        ("fuzzed_05", "3C3C82"),
                        ("fuzzed_06", "23ee"),
                        ("fuzzed_07", "00"),
                        ("fuzzed_08", "aBe5ccF85fbf32"),
                        ("fuzzed_09", "aBe5ccF85fbf32"),
                        ("fuzzed_10", "C4E02bbC"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("free_form_text", "some free form text"),
                        ("single_digit", "1"),
                        ("odd_number_of_digits", "123"),
                    ]
                ),
            ),
        ),
        (
            "xs:time",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_example", "21:32:52"),
                        ("with_utc_timezone", "19:32:52Z"),
                        ("positive_offset", "21:32:52+02:00"),
                        ("zero_offset", "21:32:52+00:00"),
                        ("negative_offset", "21:32:52-02:00"),
                        ("with_second_fractional", "21:32:52.12679"),
                        (
                            "with_long_second_fractional",
                            "21:32:52.12345678901234567890123456789012345678901234567890",
                        ),
                        ("fuzzed_01", "24:00:00.00Z"),
                        ("fuzzed_02", "01:19:39.4378+10:53"),
                        ("fuzzed_03", "01:00:12+14:00"),
                        ("fuzzed_04", "24:00:00.0Z"),
                        ("fuzzed_05", "01:10:12+14:00"),
                        ("fuzzed_06", "24:00:00-14:00"),
                        ("fuzzed_07", "20:55:25"),
                        ("fuzzed_08", "24:00:00-10:44"),
                        ("fuzzed_09", "24:00:00-13:00"),
                        ("fuzzed_10", "24:00:00.000000+14:00"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("missing_seconds", "21:32"),
                        ("hour_out_of_range", "25:25:10"),
                        ("minute_out_of_range", "01:61:10"),
                        ("second_out_of_range", "01:02:61"),
                        ("negative", "-10:00:00"),
                        ("missing_padded_zeros", "1:20:10"),
                        ("invalid_positive_offset", "21:32:52+15:00"),
                        ("invalid_negative_offset", "21:32:52-15:00"),
                        ("invalid_offset_with_seconds", "21:32:52-02:00:12"),
                    ]
                ),
            ),
        ),
        (
            "xs:integer",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_example", "1"),
                        ("negative", "-1"),
                        ("zero", "0"),
                        ("explicitly_positive", "+1"),
                        ("prefixed_with_zeros", "001"),
                        ("zero_prefixed_with_zeros", "000"),
                        (
                            "very_large",
                            "1234567890123456789012345678901234567890123456789012345678901234567890",
                        ),
                        ("fuzzed_01", "817778847926480"),
                        ("fuzzed_02", "+022"),
                        ("fuzzed_03", "-43045"),
                        ("fuzzed_04", "-3009"),
                        ("fuzzed_05", "0"),
                        ("fuzzed_06", "-3"),
                        ("fuzzed_07", "8"),
                        ("fuzzed_08", "221"),
                        ("fuzzed_09", "9191"),
                        ("fuzzed_10", "-3909"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("decimal", "1.2"),
                        ("scientific", "1e2"),
                        ("mathematical_formula", "2**5"),
                    ]
                ),
            ),
        ),
        (
            "xs:long",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_example", "1"),
                        ("negative", "-1"),
                        ("zero", "0"),
                        ("explicitly_positive", "+1"),
                        ("prefixed_with_zeros", "001"),
                        ("zero_prefixed_with_zeros", "000"),
                        ("max", "9223372036854775807"),
                        ("min", "-9223372036854775808"),
                        ("fuzzed_01", "-002728"),
                        ("fuzzed_02", "6257"),
                        ("fuzzed_03", "088"),
                        ("fuzzed_04", "29"),
                        ("fuzzed_05", "-288"),
                        ("fuzzed_06", "004775"),
                        ("fuzzed_07", "2912577609592844"),
                        ("fuzzed_08", "-0161"),
                        ("fuzzed_09", "00000000000048533"),
                        ("fuzzed_10", "3116670676"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("decimal", "1.2"),
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("max_plus_one", "9223372036854775808"),
                        ("min_minus_one", "-9223372036854775809"),
                        ("scientific", "1e2"),
                        ("mathematical_formula", "2**5"),
                    ]
                ),
            ),
        ),
        (
            "xs:int",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_example", "1"),
                        ("negative", "-1"),
                        ("zero", "0"),
                        ("explicitly_positive", "+1"),
                        ("prefixed_with_zeros", "001"),
                        ("zero_prefixed_with_zeros", "000"),
                        ("max", "2147483647"),
                        ("min", "-2147483648"),
                        ("fuzzed_01", "00"),
                        ("fuzzed_02", "-0"),
                        ("fuzzed_03", "000000000000069268"),
                        ("fuzzed_04", "+478978"),
                        ("fuzzed_05", "7097"),
                        ("fuzzed_06", "68"),
                        ("fuzzed_07", "+0"),
                        ("fuzzed_08", "6612453"),
                        ("fuzzed_09", "-00"),
                        ("fuzzed_10", "+0000000946381"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("decimal", "1.2"),
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("max_plus_one", "2147483648"),
                        ("min_minus_one", "-2147483649"),
                        ("scientific", "1e2"),
                        ("mathematical_formula", "2**5"),
                    ]
                ),
            ),
        ),
        (
            "xs:short",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_example", "1"),
                        ("negative", "-1"),
                        ("zero", "0"),
                        ("explicitly_positive", "+1"),
                        ("prefixed_with_zeros", "001"),
                        ("zero_prefixed_with_zeros", "000"),
                        ("max", "32767"),
                        ("min", "-32768"),
                        ("fuzzed_01", "9"),
                        ("fuzzed_02", "01"),
                        ("fuzzed_03", "+1"),
                        ("fuzzed_04", "8801"),
                        ("fuzzed_05", "125"),
                        ("fuzzed_06", "20518"),
                        ("fuzzed_07", "60"),
                        ("fuzzed_08", "-01"),
                        ("fuzzed_09", "+31923"),
                        ("fuzzed_10", "22"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("decimal", "1.2"),
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("max_plus_one", "32768"),
                        ("min_minus_one", "-32769"),
                        ("scientific", "1e2"),
                        ("mathematical_formula", "2**5"),
                    ]
                ),
            ),
        ),
        (
            "xs:byte",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_example", "1"),
                        ("negative", "-1"),
                        ("zero", "0"),
                        ("explicitly_positive", "+1"),
                        ("prefixed_with_zeros", "001"),
                        ("zero_prefixed_with_zeros", "000"),
                        ("max", "127"),
                        ("min", "-128"),
                        ("fuzzed_01", "05"),
                        ("fuzzed_02", "000110"),
                        ("fuzzed_03", "+00"),
                        ("fuzzed_04", "-108"),
                        ("fuzzed_05", "0001"),
                        ("fuzzed_06", "103"),
                        ("fuzzed_07", "06"),
                        ("fuzzed_08", "+0000002"),
                        ("fuzzed_09", "000000006"),
                        ("fuzzed_10", "-00011"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("decimal", "1.2"),
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("max_plus_one", "128"),
                        ("min_minus_one", "-129"),
                        ("scientific", "1e2"),
                        ("mathematical_formula", "2**5"),
                    ]
                ),
            ),
        ),
        (
            "xs:nonNegativeInteger",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_example", "1"),
                        ("zero", "0"),
                        ("minus_zero", "-0"),
                        ("explicitly_positive", "+1"),
                        ("positive_zero", "+0"),
                        ("prefixed_with_zeros", "001"),
                        ("explicitly_positive_prefixed_with_zeros", "+001"),
                        ("zero_prefixed_with_zeros", "000"),
                        (
                            "very_large",
                            "1234567890123456789012345678901234567890123456789012345678901234567890",
                        ),
                        ("fuzzed_01", "+4"),
                        ("fuzzed_02", "00018"),
                        ("fuzzed_03", "22777"),
                        ("fuzzed_04", "22077"),
                        ("fuzzed_05", "+06"),
                        ("fuzzed_06", "09"),
                        ("fuzzed_07", "+3"),
                        ("fuzzed_08", "+5739"),
                        ("fuzzed_09", "+70126"),
                        ("fuzzed_10", "05688"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("decimal", "1.2"),
                        ("negative", "-1"),
                    ]
                ),
            ),
        ),
        (
            "xs:positiveInteger",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_example", "1"),
                        ("explicitly_positive", "+1"),
                        ("prefixed_with_zeros", "001"),
                        (
                            "very_large",
                            "1234567890123456789012345678901234567890123456789012345678901234567890",
                        ),
                        ("fuzzed_01", "550788"),
                        ("fuzzed_02", "7775"),
                        ("fuzzed_03", "+87138"),
                        ("fuzzed_04", "8093888718"),
                        ("fuzzed_05", "01145"),
                        ("fuzzed_06", "01"),
                        ("fuzzed_07", "+57345"),
                        ("fuzzed_08", "54691"),
                        ("fuzzed_09", "+01"),
                        ("fuzzed_10", "3"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("decimal", "1.2"),
                        ("negative", "-1"),
                        ("zero_prefixed_with_zeros", "000"),
                        ("zero", "0"),
                    ]
                ),
            ),
        ),
        (
            "xs:unsignedLong",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_example", "1"),
                        ("zero", "0"),
                        ("explicitly_positive", "+1"),
                        ("prefixed_with_zeros", "001"),
                        ("zero_prefixed_with_zeros", "000"),
                        ("max", "18446744073709551615"),
                        ("fuzzed_01", "00"),
                        ("fuzzed_02", "+0013081"),
                        ("fuzzed_03", "+00008773"),
                        ("fuzzed_04", "+000000858"),
                        ("fuzzed_05", "+000000000002599"),
                        ("fuzzed_06", "+0257364527"),
                        ("fuzzed_07", "+000000038893"),
                        ("fuzzed_08", "+0000000000000111491"),
                        ("fuzzed_09", "+09"),
                        ("fuzzed_10", "0012208354443"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("decimal", "1.2"),
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("max_plus_one", "18446744073709551616"),
                        ("negative", "-1"),
                        ("scientific", "1e2"),
                        ("mathematical_formula", "2**5"),
                    ]
                ),
            ),
        ),
        (
            "xs:unsignedInt",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_example", "1"),
                        ("zero", "0"),
                        ("explicitly_positive", "+1"),
                        ("prefixed_with_zeros", "001"),
                        ("zero_prefixed_with_zeros", "000"),
                        ("max", "4294967295"),
                        ("fuzzed_01", "+000832736002"),
                        ("fuzzed_02", "0454"),
                        ("fuzzed_03", "0000000000001161715506"),
                        ("fuzzed_04", "+0006096840"),
                        ("fuzzed_05", "8547"),
                        ("fuzzed_06", "+092843"),
                        ("fuzzed_07", "+44"),
                        ("fuzzed_08", "+0881299729"),
                        ("fuzzed_09", "+00604"),
                        ("fuzzed_10", "+000101"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("decimal", "1.2"),
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("max_plus_one", "4294967296"),
                        ("negative", "-1"),
                        ("scientific", "1e2"),
                        ("mathematical_formula", "2**5"),
                    ]
                ),
            ),
        ),
        (
            "xs:unsignedShort",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_example", "1"),
                        ("zero", "0"),
                        ("explicitly_positive", "+1"),
                        ("prefixed_with_zeros", "001"),
                        ("zero_prefixed_with_zeros", "000"),
                        ("max", "65535"),
                        ("fuzzed_01", "+00"),
                        ("fuzzed_02", "06949"),
                        ("fuzzed_03", "0391"),
                        ("fuzzed_04", "+000004"),
                        ("fuzzed_05", "00000000391"),
                        ("fuzzed_06", "+085"),
                        ("fuzzed_07", "10233"),
                        ("fuzzed_08", "044598"),
                        ("fuzzed_09", "+00066"),
                        ("fuzzed_10", "+00000000000000000000003250"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("decimal", "1.2"),
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("max_plus_one", "65536"),
                        ("negative", "-1"),
                        ("scientific", "1e2"),
                        ("mathematical_formula", "2**5"),
                    ]
                ),
            ),
        ),
        (
            "xs:unsignedByte",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("common_example", "1"),
                        ("zero", "0"),
                        ("explicitly_positive", "+1"),
                        ("prefixed_with_zeros", "001"),
                        ("zero_prefixed_with_zeros", "000"),
                        ("max", "255"),
                        ("fuzzed_01", "0000000000000000000000000000067"),
                        ("fuzzed_02", "+130"),
                        ("fuzzed_03", "232"),
                        ("fuzzed_04", "+110"),
                        ("fuzzed_05", "+000000000012"),
                        ("fuzzed_06", "055"),
                        ("fuzzed_07", "031"),
                        ("fuzzed_08", "0178"),
                        ("fuzzed_09", "+00"),
                        ("fuzzed_10", "+00000006"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("decimal", "1.2"),
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("max_plus_one", "256"),
                        ("negative", "-1"),
                        ("scientific", "1e2"),
                        ("mathematical_formula", "2**5"),
                    ]
                ),
            ),
        ),
        (
            "xs:nonPositiveInteger",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("negative", "-1"),
                        ("zero", "0"),
                        ("prefixed_with_zeros", "-001"),
                        ("explicitly_positive_zero", "+0"),
                        (
                            "very_large",
                            "-1234567890123456789012345678901234567890123456789012345678901234567890",
                        ),
                        ("fuzzed_01", "-51"),
                        ("fuzzed_02", "-8908938"),
                        ("fuzzed_03", "-553"),
                        ("fuzzed_04", "+0"),
                        ("fuzzed_05", "-4006"),
                        ("fuzzed_06", "-83"),
                        ("fuzzed_07", "-004"),
                        ("fuzzed_08", "-551521749598676413553"),
                        ("fuzzed_09", "-12116166"),
                        ("fuzzed_10", "-553"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("decimal", "1.2"),
                        ("implicitly_positive", "1"),
                        ("explicitly_positive", "+1"),
                        ("scientific", "-1e2"),
                        ("mathematical_formula", "-2**5"),
                    ]
                ),
            ),
        ),
        (
            "xs:negativeInteger",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("negative", "-1"),
                        ("prefixed_with_zeros", "-001"),
                        (
                            "very_large",
                            "-1234567890123456789012345678901234567890123456789012345678901234567890",
                        ),
                        ("fuzzed_01", "-001"),
                        ("fuzzed_02", "-002"),
                        ("fuzzed_03", "-009"),
                        ("fuzzed_04", "-8"),
                        ("fuzzed_05", "-1"),
                        ("fuzzed_06", "-00000000000000000000000516481"),
                        ("fuzzed_07", "-003"),
                        ("fuzzed_08", "-00126"),
                        ("fuzzed_09", "-01"),
                        ("fuzzed_10", "-3"),
                    ]
                ),
                negatives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free form text"),
                        ("zero", "0"),
                        ("zero_prefixed_with_zeros", "000"),
                        ("explicitly_positive_zero", "+0"),
                        ("decimal", "1.2"),
                        ("implicitly_positive", "1"),
                        ("explicitly_positive", "+1"),
                        ("scientific", "-1e2"),
                        ("mathematical_formula", "-2**5"),
                    ]
                ),
            ),
        ),
        (
            "xs:string",
            Examples(
                positives=collections.OrderedDict(
                    [
                        ("empty", ""),
                        ("free_form_text", "some free & <free> \u1984 form text"),
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
                        ("NUL_as_x", "\x00"),
                        ("NUL_as_utf16", "\u0000"),
                        ("NUL_as_utf32", "\U00000000"),
                        (
                            "negatively_fuzzed_01",
                            "摲\x00À\x12Vêìê¸´ç;\U000da189Î\x8bOsJBô",
                        ),
                        ("negatively_fuzzed_02", "@ÝJ¦\x00\U0009afb6õ\U0004f775𐒐}"),
                        ("negatively_fuzzed_03", "\x91ÈÊ\x00\U00019bec"),
                        ("negatively_fuzzed_04", "\U00104e86\x00R\t-8^"),
                        (
                            "negatively_fuzzed_05",
                            "\x15>Ò\U000e5b00LË)T\x00Îç\U000ba5cf\U0010877d\x08Àº\U000a68cfÊ\xa08]\U000fca08\x181D\x0cY\U00060b23A\\¬ï\U000598e3\U0006622cc",
                        ),
                        (
                            "negatively_fuzzed_06",
                            "\U0003a78b\U000b955fÑ\x1c°\u1f58ªW\U00097442\x00\U000ca33b",
                        ),
                        (
                            "negatively_fuzzed_07",
                            "\U0005df63\x00'\x1f \U000562acxxÏÖ\nwf",
                        ),
                        (
                            "negatively_fuzzed_08",
                            "\U000cad55쮾\x17Ò\x918¤M\U000360d5ÔÅ\x00\r\U0007bfa9Zs6\x12À>\x19\U00105b43\x0e§\U000be9db",
                        ),
                        (
                            "negatively_fuzzed_09",
                            "\U000aa52b\x12U\x91ô\x81ô\x16\U0010bc24\U000cd094\x00",
                        ),
                        (
                            "negatively_fuzzed_10",
                            "´²\x82\x00\U000fc89dÀâ¨*û𭮩ò\x8f¤\x82¡ÂÝ_쇽\U000ac5e8EÖ\U000c9731ý⼪åùH\U0007d4cbP¶\x13Ä",
                        ),
                    ]
                ),
            ),
        ),
    ],
)


def _assert_all_covered_and_not_more() -> None:
    """Assert that we covered all the XSD data types."""
    covered = set(BY_VALUE_TYPE.keys())

    literal_values = {literal.value for literal in aas_core_meta.v3.Data_type_def_XSD}

    not_covered = sorted(literal_values.difference(covered))
    surplus = sorted(covered.difference(literal_values))

    if len(not_covered) > 0:
        raise AssertionError(
            f"The following {aas_core_meta.v3.Data_type_def_XSD.__name__} literals "
            f"were not covered: {not_covered}"
        )

    if len(surplus) > 0:
        raise AssertionError(
            f"The following keys in BY_VALUE_TYPE were not present in "
            f"{aas_core_meta.v3.Data_type_def_XSD.__name__} literals: {surplus}"
        )


_assert_all_covered_and_not_more()
