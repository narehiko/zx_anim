import unittest

from zxanim.smoothing import RapidTapSmoother


class RapidTapSmootherTests(unittest.TestCase):
    def test_first_tap_is_immediate(self):
        smoother = RapidTapSmoother(70)
        self.assertEqual(
            smoother.request("left", True, 1000),
            ("left", True),
        )

    def test_stream_updates_are_limited_to_configured_cadence(self):
        smoother = RapidTapSmoother(70)
        smoother.request("left", True, 1000)
        self.assertIsNone(smoother.request("right", True, 1020))
        self.assertIsNone(smoother.request("left", True, 1040))
        self.assertEqual(
            smoother.poll("left", True, 1070),
            ("left", True),
        )

    def test_latest_tap_wins_during_smoothing_window(self):
        smoother = RapidTapSmoother(70)
        smoother.request("left", True, 1000)
        smoother.request("right", True, 1020)
        smoother.request("left", True, 1040)
        smoother.request("right", True, 1060)
        self.assertEqual(
            smoother.poll("left", True, 1070),
            ("right", True),
        )

    def test_release_grace_avoids_default_pose_between_taps(self):
        smoother = RapidTapSmoother(70)
        smoother.request("right", True, 1000)
        smoother.release_to_idle(1010)
        self.assertIsNone(smoother.poll("left", False, 1079))
        self.assertEqual(
            smoother.poll("left", False, 1080),
            ("left", False),
        )

    def test_zero_disables_smoothing(self):
        smoother = RapidTapSmoother(0)
        self.assertEqual(
            smoother.request("left", True, 1000),
            ("left", True),
        )
        self.assertEqual(
            smoother.request("right", True, 1001),
            ("right", True),
        )


if __name__ == "__main__":
    unittest.main()
