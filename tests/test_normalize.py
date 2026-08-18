import unittest
from datetime import date

from backend.normalize import (
    normalize_city,
    normalize_email,
    normalize_name,
    normalize_phone,
    parse_bool,
    parse_ctc,
    parse_date,
    parse_rate,
    split_skills,
)


class NormalizeTests(unittest.TestCase):
    def test_normalize_phone_variants(self):
        self.assertEqual(normalize_phone("9000000104"), "+919000000104")
        self.assertEqual(normalize_phone("919000000143"), "+919000000143")
        self.assertEqual(normalize_phone("+91-9000000131"), "+919000000131")
        self.assertEqual(normalize_phone("09000000287"), "+919000000287")
        self.assertIsNone(normalize_phone("12345"))

    def test_normalize_email_name_city(self):
        self.assertEqual(normalize_email(" DEEPAK.NAIR44@EXAMPLE.COM "), "deepak.nair44@example.com")
        self.assertEqual(normalize_name("R. Verma"), "r verma")
        self.assertEqual(normalize_city("gurugram "), ("gurugram", "Gurugram"))
        self.assertEqual(normalize_city("New Delhi"), ("New Delhi", "Delhi NCR"))

    def test_parse_dates_rates_booleans_and_skills(self):
        self.assertEqual(parse_date("24-07-2026"), date(2026, 7, 24))
        self.assertEqual(parse_date("08/21/2026"), date(2026, 8, 21))
        self.assertEqual(parse_date("7 Jul 2026"), date(2026, 7, 7))
        self.assertEqual(parse_rate("15k/month"), (15000, "month"))
        self.assertEqual(parse_rate("1415/hr"), (1415, "hour"))
        self.assertEqual(parse_ctc("4.2"), 420000)
        self.assertEqual(parse_ctc("417964"), 417964)
        self.assertTrue(parse_bool("Y"))
        self.assertFalse(parse_bool("No"))
        self.assertEqual(split_skills("REST APIs, rest apis, Python"), ["rest apis", "python"])


if __name__ == "__main__":
    unittest.main()
