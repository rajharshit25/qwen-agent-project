
import pytest

from backend.tools.registry import run_tool


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "   ",
        "\t\n",
    ],
)
def test_calculator_rejects_blank_expression(expression):
    with pytest.raises(ValueError, match="non-empty string"):
        run_tool("calculator", {"expression": expression})
