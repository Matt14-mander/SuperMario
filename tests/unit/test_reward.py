import unittest

try:
    from ai_platformer.envs.reward import RewardConfig, compose_reward

    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False


@unittest.skipUnless(GYMNASIUM_AVAILABLE, "Gymnasium benchmark dependencies are not installed")
class RewardCompositionTests(unittest.TestCase):
    def test_forward_then_backward_cannot_farm_progress(self) -> None:
        config = RewardConfig()
        forward, forward_parts = compose_reward(
            previous_progress=0.2,
            current_progress=0.4,
            coin_delta=0,
            outcome=None,
            config=config,
        )
        backward, backward_parts = compose_reward(
            previous_progress=0.4,
            current_progress=0.2,
            coin_delta=0,
            outcome=None,
            config=config,
        )

        self.assertAlmostEqual(
            forward_parts["progress"] + backward_parts["progress"],
            0.0,
        )
        self.assertLess(forward + backward, 0.0)

    def test_terminal_rewards_have_expected_sign(self) -> None:
        config = RewardConfig()
        success, _ = compose_reward(
            previous_progress=0.9,
            current_progress=1.0,
            coin_delta=0,
            outcome="success",
            config=config,
        )
        death, _ = compose_reward(
            previous_progress=0.9,
            current_progress=0.9,
            coin_delta=0,
            outcome="death",
            config=config,
        )

        self.assertGreater(success, 0.0)
        self.assertLess(death, 0.0)

    def test_negative_coin_delta_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            compose_reward(
                previous_progress=0.0,
                current_progress=0.0,
                coin_delta=-1,
                outcome=None,
                config=RewardConfig(),
            )


if __name__ == "__main__":
    unittest.main()
