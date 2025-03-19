import unittest
from bot import QuizGame, MusicQueue

class TestQuizGame(unittest.TestCase):
    def setUp(self):
        self.quiz = QuizGame()

    def test_get_next_question(self):
        question = self.quiz.get_next_question()
        self.assertIsNotNone(question)
        self.assertIn('category', question)
        self.assertIn('question', question)
        self.assertIn('answer', question)

    def test_check_answer_format(self):
        # Test khoảng trắng
        answer1 = "cây  cầu"
        answer2 = "cây cầu"
        self.assertEqual(
            ' '.join(answer1.lower().split()),
            ' '.join(answer2.lower().split())
        )

class TestMusicQueue(unittest.TestCase):
    def setUp(self):
        self.queue = MusicQueue()

    def test_queue_operations(self):
        self.assertTrue(self.queue.is_empty())
        self.queue.add("test_song")
        self.assertFalse(self.queue.is_empty())

if __name__ == '__main__':
    unittest.main() 