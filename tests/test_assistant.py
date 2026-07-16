import unittest

from app.assistant import apply_actions, parse_json_object
from app.storage import empty_user


class AssistantHelpersTests(unittest.TestCase):
    def test_parse_json_from_code_fence(self):
        result = parse_json_object('```json\n{"profile": {"专业": "计算机"}}\n```')
        self.assertEqual(result["profile"]["专业"], "计算机")

    def test_apply_actions_adds_profile_and_task(self):
        result = apply_actions(
            empty_user(),
            {
                "profile": {"年级": "大二"},
                "task_action": {
                    "type": "add",
                    "title": "完成作业",
                    "deadline": "周五",
                },
            },
        )
        self.assertEqual(result["用户信息"]["年级"], "大二")
        self.assertEqual(result["待办任务"][0]["任务"], "完成作业")

    def test_apply_actions_avoids_duplicate_open_task(self):
        data = empty_user()
        action = {
            "task_action": {
                "type": "add",
                "title": "完成作业",
                "deadline": "周五",
            }
        }
        apply_actions(data, action)
        apply_actions(data, action)
        self.assertEqual(len(data["待办任务"]), 1)


if __name__ == "__main__":
    unittest.main()
