from __future__ import annotations

import ast
from pathlib import Path
from unittest import TestCase


class RouterRegistrationTests(TestCase):
    def test_routers_are_unique_and_fallback_is_last(self) -> None:
        tree = ast.parse(Path("bot.py").read_text(encoding="utf-8"))
        included = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != "include_router" or not node.args:
                continue
            argument = node.args[0]
            if isinstance(argument, ast.Name):
                included.append(argument.id)

        self.assertEqual(len(included), len(set(included)), included)
        self.assertEqual(included[-1], "callback_fallback_router")
        self.assertIn("UserMiddleware", Path("bot.py").read_text(encoding="utf-8"))
