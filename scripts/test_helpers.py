"""Unit tests for file type helpers (no network)."""

import base64
import unittest

from app.core.exceptions import GraphValidationError
from app.services.file_types import (
    SUPPORTED_EXTENSIONS,
    infer_mime_type,
    validate_supported_file_name,
)


class FileTypesTest(unittest.TestCase):
    def test_supported_extensions(self):
        self.assertIn(".pdf", SUPPORTED_EXTENSIONS)
        self.assertIn(".docx", SUPPORTED_EXTENSIONS)
        self.assertIn(".xlsx", SUPPORTED_EXTENSIONS)
        self.assertIn(".pptx", SUPPORTED_EXTENSIONS)

    def test_infer_mime_pdf(self):
        self.assertEqual(
            infer_mime_type("report.pdf"),
            "application/pdf",
        )

    def test_infer_mime_docx(self):
        mime = infer_mime_type("brief.docx")
        self.assertIn("wordprocessingml", mime)

    def test_reject_unknown_extension(self):
        with self.assertRaises(GraphValidationError):
            validate_supported_file_name("notes.txt")

    def test_validate_ok(self):
        self.assertEqual(validate_supported_file_name("deck.pptx"), "deck.pptx")


if __name__ == "__main__":
    unittest.main()
