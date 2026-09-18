from calculator import (
    add,
    subtract,
    multiply,
    divide,
    format_result,
)


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(5, 3) == 2


def test_multiply():
    assert multiply(2, 3) == 6


def test_divide():
    assert divide(6, 3) == 2


def test_divide_by_zero():
    try:
        divide(5, 0)
    except ValueError:
        return

    assert False, "divide should reject division by zero"


def test_format_result():
    assert format_result("total", 42) == "total: 42"