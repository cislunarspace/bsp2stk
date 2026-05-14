import pytest

from bsp2stk.core.stk_writer import (
    STK_CENTRAL_BODY_CHOICES,
    STK_COORDINATE_CHOICES,
    STK_INTERPOLATION_CHOICES,
    StkFormat,
)


def test_stk_format_default_values_are_in_choice_tuples():
    default_format = StkFormat.default()

    assert default_format.interpolation_method in STK_INTERPOLATION_CHOICES
    assert default_format.central_body in STK_CENTRAL_BODY_CHOICES
    assert default_format.coordinate_system in STK_COORDINATE_CHOICES


def test_stk_format_with_overrides_returns_new_instance_with_replaced_field():
    default_format = StkFormat.default()

    updated = default_format.with_overrides(step_seconds=120.0)

    assert updated is not default_format
    assert updated.step_seconds == 120.0
    assert updated.interpolation_method == default_format.interpolation_method
    assert updated.interpolation_samples_m1 == default_format.interpolation_samples_m1
    assert updated.central_body == default_format.central_body
    assert updated.coordinate_system == default_format.coordinate_system


def test_stk_format_with_overrides_rejects_unknown_fields():
    default_format = StkFormat.default()

    with pytest.raises(TypeError, match="unexpected field"):
        default_format.with_overrides(unknown_field=True)
