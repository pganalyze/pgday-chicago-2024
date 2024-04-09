"""Goal of the user (an objective that later becomes a constraint)."""


import copy
from math import ceil, floor
from ortools.sat.python import cp_model

import modelize


class Goal:
    """Goal of the user.

    A Goal object takes care of both the objective and the resulting constraint.
    """

    _names = ("Minimize Index Write Overhead",
              "Minimal Indexes",
              "Minimal Cost")

    def __init__(self, name, tolerance=0.0):
        """Intialize the goal.

        Args:
          name: Name of the goal (e.g., "Minimal Cost").
          tolerance: How much the resulting constraint is allowed to deviate from the value found (tolerance >= 0.0).
        """
        self._name = name
        self._tolerance = tolerance

        assert self._name in self._names
        assert self._tolerance >= 0.0

        # Value of the optimized goal, None if it has not yet been optimized
        self._value = None

    def get_name(self):
        """Return the name of the goal."""
        return self._name

    def is_optimized(self):
        """Return a boolean indicating if the goal has been optimized."""
        return self._value is not None

    def get_value(self):
        """Return the value of the goal."""
        assert self.is_optimized()

        return self._value

    def update_value(self, value):
        """Update the value of the goal after it has been optimized."""
        self._value = value

    def add_as_objective(self, model):
        """Add the goal as an objective to the model."""
        if self._name == "Minimize Index Write Overhead":
            model.Add(model.objective ==
                      cp_model.LinearExpr.WeightedSum(model.x, model.index_iwo))
            model.Minimize(model.objective)

        elif self._name == "Minimal Indexes":
            model.Add(model.objective == cp_model.LinearExpr.Sum(model.x))
            model.Minimize(model.objective)

        elif self._name == "Minimal Cost":
            model.Add(model.objective == cp_model.LinearExpr.Sum(model.scan_cost))
            model.Minimize(model.objective)

    def add_as_constraint(self, model):
        """Add the goal as a constraint to the model."""
        assert self.is_optimized()

        if self._name == "Minimize Index Write Overhead":
            model.Add(cp_model.LinearExpr.WeightedSum(model.x, model.index_iwo)
                      <= floor(self.get_value() * (1 + self._tolerance)))

        elif self._name == "Minimal Indexes":
            model.Add(cp_model.LinearExpr.Sum(model.x)
                      <= floor(self.get_value() * (1 + self._tolerance)))

        elif self._name == "Minimal Cost":
            model.Add(cp_model.LinearExpr.Sum(model.scan_cost)
                      <= floor(self.get_value() * (1 + self._tolerance)))

    def get_objective_description(self):
        """Return the description of the objective."""
        description = ""

        if self._name == "Minimize Index Write Overhead":
            description = "Minimize the sum of IWO (of the existing and possible indexes)"

        elif self._name == "Minimal Indexes":
            description = "Minimize the number of existing and possible indexes"

        elif self._name == "Minimal Cost":
            description = "Minimize the combined costs of all the scans"

        return description

    def get_constraint_description(self):
        """Return the description of the constraint."""
        assert self.is_optimized()

        floor_suffix = "must be at most " + \
            f"{floor(self.get_value()) * (1 + self._tolerance):.2f} " + \
            f"({self.get_value()} with a tolerance of {self._tolerance:.2%})"

        description = ""

        if self._name == "Minimize Index Write Overhead":
            description = f"The sum of all IWO {floor_suffix}"

        elif self._name == "Minimal Indexes":
            description = f"The number of existing and possible indexes {floor_suffix}"

        elif self._name == "Minimal Cost":
            description = f"The combined costs of all the scans {floor_suffix}"

        return description
