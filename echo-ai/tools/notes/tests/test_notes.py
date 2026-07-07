import os
import shutil
import unittest
from tools.notes.notes_models import NoteCreate, NoteUpdate
from tools.notes.notes_service import NotesService

class TestNotesService(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath("uploads/test_notes_temp")
        self.service = NotesService(storage_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_and_get_note(self):
        note_in = NoteCreate(title="Test Title", content="Test Content", tags=["test", "unit"])
        note = self.service.create_note(note_in)
        
        self.assertIsNotNone(note.id)
        self.assertEqual(note.title, "Test Title")
        self.assertEqual(note.content, "Test Content")
        self.assertEqual(note.tags, ["test", "unit"])
        self.assertIsNotNone(note.created_at)
        
        fetched = self.service.get_note(note.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, note.id)
        self.assertEqual(fetched.title, "Test Title")

    def test_update_note(self):
        note_in = NoteCreate(title="Old Title", content="Old Content", tags=[])
        note = self.service.create_note(note_in)
        
        note_up = NoteUpdate(title="New Title", content="New Content", tags=["updated"])
        updated = self.service.update_note(note.id, note_up)
        
        self.assertIsNotNone(updated)
        self.assertEqual(updated.title, "New Title")
        self.assertEqual(updated.content, "New Content")
        self.assertEqual(updated.tags, ["updated"])
        
        # Verify in get
        fetched = self.service.get_note(note.id)
        self.assertEqual(fetched.title, "New Title")

    def test_delete_note(self):
        note_in = NoteCreate(title="To Delete", content="Content", tags=[])
        note = self.service.create_note(note_in)
        
        self.assertTrue(self.service.delete_note(note.id))
        self.assertIsNone(self.service.get_note(note.id))
        self.assertFalse(self.service.delete_note(note.id))

    def test_list_and_search_notes(self):
        note1 = self.service.create_note(NoteCreate(title="Apples", content="Buy apples", tags=["shopping"]))
        note2 = self.service.create_note(NoteCreate(title="Bananas", content="Eat bananas", tags=["fruit"]))
        
        all_notes = self.service.list_notes()
        self.assertEqual(len(all_notes), 2)
        
        search_res = self.service.search_notes("apples")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0].title, "Apples")
        
        search_tag = self.service.search_notes("fruit")
        self.assertEqual(len(search_tag), 1)
        self.assertEqual(search_tag[0].title, "Bananas")

if __name__ == "__main__":
    unittest.main()
