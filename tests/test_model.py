from langchain.schema import Document
from unittest.mock import Mock
from model.t5 import T5Model
import unittest
import pytest

class TestT5Model(unittest.TestCase):
    
    def setUp(self):       
        self.model = T5Model()
        self.model.clear_history()

    def test_read_pdf_file_not_found(self):
        # Arrange
        mock_pdf = Mock()
        mock_pdf.getvalue.side_effect = FileNotFoundError()

        # Act
        result = self.model.read_pdf(mock_pdf)

        # Assert
        self.assertEqual(result, "File not found.")

    def test_text_splitter(self):
        # Arrange
        test_docs = [Document(page_content="Test content " * 100, metadata={"page": 1})]

        # Act
        result = self.model._text_splitter(test_docs)

        # Assert
        self.assertIsInstance(result, list)
        self.assertTrue(all(isinstance(doc, Document) for doc in result))
        self.assertTrue(len(result) > 1)  # Should split into multiple chunks

    def test_remove_pua(self):
        # Arrange
        test_text = "Regular text \ue000 PUA char \uf8ff end \U000f0000 more"
        expected = "Regular text  PUA char  end  more"

        # Act
        result = self.model._remove_pua(test_text)

        # Assert
        self.assertEqual(result, expected)

    def test_remove_characters(self):
        # Arrange
        test_docs = [
            Document(page_content="Line1-\nLine2\n\nExtra  spaces", metadata={"page": 1}),
            Document(page_content="More-\ntext\nhere", metadata={"page": 2})
        ]

        # Act
        result = self.model._remove_characters(test_docs)

        # Assert
        self.assertEqual(result[0].page_content, "Line1Line2 Extra spaces")
        self.assertEqual(result[1].page_content, "Moretext here")

    def test_clear_history(self):
        # Arrange
        self.model._chat_history = [("question1", "answer1"), ("question2", "answer2")]

        # Act
        self.model.clear_history()

        # Assert
        self.assertEqual(self.model._chat_history, [])
