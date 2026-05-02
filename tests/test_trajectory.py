import math
import unittest

from driverx.datasets.fixtures import load_fixture_frame
from driverx.planning.baselines import generate_rule_baselines
from driverx.planning.candidates import generate_candidates
from driverx.planning.ranking import rank_candidates
from driverx.planning.smoothing import smooth_candidate
from driverx.reasoning.mock import MockReasoner


class TrajectoryTest(unittest.TestCase):
    def test_candidates_have_waymo_shape(self) -> None:
        frame = load_fixture_frame("construction_merge")
        intent = MockReasoner().infer_intent(frame)
        candidates = generate_candidates(frame, intent)
        self.assertGreaterEqual(len(candidates), 3)
        for candidate in candidates:
            self.assertEqual(len(candidate.points_xy), 20)

    def test_smoothing_clamps_large_steps(self) -> None:
        frame = load_fixture_frame("construction_merge")
        intent = MockReasoner().infer_intent(frame)
        candidate = generate_candidates(frame, intent)[0]
        smoothed = smooth_candidate(candidate, max_step=0.5)
        for previous, current in zip(
            smoothed.points_xy[:-1],
            smoothed.points_xy[1:],
            strict=True,
        ):
            self.assertLessEqual(math.dist(previous, current), 0.5 + 1e-6)

    def test_ranking_returns_candidate(self) -> None:
        frame = load_fixture_frame("construction_merge")
        intent = MockReasoner().infer_intent(frame)
        candidates = [smooth_candidate(candidate) for candidate in generate_candidates(frame, intent)]
        selected = rank_candidates(frame, candidates)
        self.assertEqual(len(selected.points_xy), 20)
        self.assertIn("rank_cost", selected.metadata)

    def test_rule_baselines_have_waymo_shape(self) -> None:
        frame = load_fixture_frame("construction_merge")
        candidates = generate_rule_baselines(frame)
        self.assertEqual(
            [candidate.source for candidate in candidates],
            ["constant_velocity", "constant_acceleration", "cautious_stop"],
        )
        for candidate in candidates:
            self.assertEqual(len(candidate.points_xy), 20)
            self.assertEqual(candidate.metadata["strategy"], candidate.source)
            self.assertTrue(candidate.metadata["baseline"])


if __name__ == "__main__":
    unittest.main()
