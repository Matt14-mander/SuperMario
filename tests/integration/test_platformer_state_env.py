import unittest

try:
    import gymnasium as gym
    import numpy as np
    from gymnasium.utils.env_checker import check_env

    import ai_platformer.envs
    from ai_platformer.agents.scripted import MoveRightAgent, RuleJumpAgent
    from ai_platformer.benchmark import evaluate_scripted_agent, run_reward_exploit_audit
    from ai_platformer.envs import OBSERVATION_SIZE, PlatformerStateEnv

    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False


@unittest.skipUnless(GYMNASIUM_AVAILABLE, "Gymnasium benchmark dependencies are not installed")
class PlatformerStateEnvironmentTests(unittest.TestCase):
    def test_registered_environment_passes_checker(self) -> None:
        env = gym.make("PlatformerState-v0").unwrapped
        check_env(env)

        observation, info = env.reset(seed=123)

        self.assertEqual(observation.shape, (OBSERVATION_SIZE,))
        self.assertEqual(observation.dtype, np.float32)
        self.assertTrue(env.observation_space.contains(observation))
        self.assertEqual(info["seed"], 123)

    def test_fixed_seed_and_actions_are_deterministic(self) -> None:
        actions = [6] * 20 + [9] * 5 + [6] * 20

        def rollout():
            env = PlatformerStateEnv()
            observation, _ = env.reset(seed=42)
            transitions = [(observation.copy(), 0.0, False, False)]
            for action in actions:
                observation, reward, terminated, truncated, _ = env.step(action)
                transitions.append((observation.copy(), reward, terminated, truncated))
                if terminated or truncated:
                    break
            return transitions

        first = rollout()
        second = rollout()
        self.assertEqual(len(first), len(second))
        for left, right in zip(first, second):
            np.testing.assert_array_equal(left[0], right[0])
            self.assertEqual(left[1:], right[1:])

    def test_reward_breakdown_sums_to_reward(self) -> None:
        env = PlatformerStateEnv()
        env.reset(seed=7)

        _, reward, _, _, info = env.step(6)

        self.assertAlmostEqual(reward, sum(info["reward_components"].values()))
        self.assertEqual(
            set(info["reward_components"]),
            {"progress", "coin", "success", "death", "time"},
        )

    def test_environment_step_limit_truncates_episode(self) -> None:
        env = PlatformerStateEnv(episode_step_limit=3)
        env.reset(seed=7)

        for _ in range(3):
            _, _, terminated, truncated, info = env.step(0)

        self.assertFalse(terminated)
        self.assertTrue(truncated)
        self.assertEqual(info["outcome"], "time_limit")
        self.assertEqual(info["episode_step"], 3)

    def test_reward_exploit_audit_passes(self) -> None:
        report = run_reward_exploit_audit()

        self.assertTrue(report.passed)
        self.assertLess(report.noop_return, 0.0)
        self.assertFalse(report.duplicate_collectibles)

    def test_rule_jump_baseline_beats_move_right(self) -> None:
        move_right = evaluate_scripted_agent("move-right", MoveRightAgent, [100], max_steps=500)
        rule_jump = evaluate_scripted_agent("rule-jump", RuleJumpAgent, [100], max_steps=500)

        self.assertLess(move_right.episodes[0].progress, rule_jump.episodes[0].progress)
        self.assertEqual(rule_jump.episodes[0].outcome, "success")
        self.assertEqual(rule_jump.summary()["success_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
