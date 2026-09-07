from unittest import TestCase

from handlers.games import _logic_question
from keyboards.game_kb import GameCB, memory_grid_kb


class GameMechanicsTests(TestCase):
    def test_logic_questions_are_deterministic_rules_with_one_available_answer(self) -> None:
        for round_number in range(1, 6):
            question = _logic_question(round_number, "ru")
            self.assertEqual(len(question["options"]), 4)
            self.assertEqual(len(set(question["options"])), 4)
            self.assertIn(question["correct"], question["options"])
            self.assertTrue(question["explanation"])

    def test_memory_grid_marks_chosen_values_without_reusing_their_callback(self) -> None:
        markup = memory_grid_kb([1, 2, 3, 4, 5, 6, 7, 8, 9], {1, 3})
        callbacks = [button.callback_data for row in markup.inline_keyboard for button in row]
        parsed = [GameCB.unpack(callback) for callback in callbacks]
        self.assertEqual(sum(item.action == "memory_selected" for item in parsed), 2)
        self.assertNotIn("1", [item.param for item in parsed if item.action == "memory_pick"])
