import unittest

from driverx.evaluation.ade import average_displacement_error


class EvaluationTest(unittest.TestCase):
    def test_average_displacement_error(self) -> None:
        prediction = [(0.0, 0.0), (1.0, 0.0)]
        truth = [(0.0, 0.0), (1.0, 1.0)]
        self.assertAlmostEqual(average_displacement_error(prediction, truth), 0.5)

    def test_average_displacement_error_shape_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            average_displacement_error([(0.0, 0.0)], [(0.0, 0.0), (1.0, 0.0)])


if __name__ == "__main__":
    unittest.main()
