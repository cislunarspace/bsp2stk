"""Unit tests for StkWriter — exact byte-level assertions, no mocking."""

from bsp2stk.core.stk_writer import StkHeader, StkWriter


def _basic_header(num_points: int = 0) -> StkHeader:
    return StkHeader(
        num_points=num_points,
        epoch_jd=2459989.0,
        interpolation_method="Lagrange",
        interpolation_samples_m1=5,
        central_body="Earth",
        coordinate_system="J2000",
    )


def test_empty_writer_produces_header_and_footer(tmp_path):
    """Zero samples still yields well-formed header + footer."""
    path = tmp_path / "empty.stk"
    header = _basic_header(num_points=0)

    with StkWriter.open(str(path), header):
        pass

    expected = (
        "stk.v.9.0\n"
        "\n"
        "BEGIN Ephemeris\n"
        "\n"
        "    NumberOfEphemerisPoints\t\t 0\n"
        "\n"
        "    ScenarioEpoch\t\t 13 Feb 2023 00:00:00.000000\n"
        "\n"
        "# Epoch in JDate format: 2459989.00000000000000\n"
        "# Epoch in YYDDD format:   23044.00000000000000\n"
        "\n"
        "\n"
        "    InterpolationMethod\t\t Lagrange\n"
        "\n"
        "    InterpolationSamplesM1\t\t 5\n"
        "\n"
        "    CentralBody\t\t Earth\n"
        "\n"
        "    CoordinateSystem\t\t J2000\n"
        "\n"
        "# Time of first point: 13 Feb 2023 00:00:00.000000.000000000 UTCG"
        " = 2459989.00000000000000 JDate"
        " = 23044.00000000000000 YYDDD\n"
        "\n"
        "    EphemerisTimePosVel\t\t\n"
        "\n"
        "\n"
        "\n"
        "END Ephemeris\n"
    )

    assert path.read_text() == expected


def test_single_sample_uses_scientific_notation(tmp_path):
    """A single sample renders with 23.16e formatting."""
    path = tmp_path / "single.stk"
    header = _basic_header(num_points=1)

    with StkWriter.open(str(path), header) as writer:
        writer.write_sample(1.0, (2.0, 3.0, 4.0), (5.0, 6.0, 7.0))

    content = path.read_text()
    expected_line = (
        "  1.0000000000000000e+00"
        "   2.0000000000000000e+00"
        "   3.0000000000000000e+00"
        "   4.0000000000000000e+00"
        "   5.0000000000000000e+00"
        "   6.0000000000000000e+00"
        "   7.0000000000000000e+00\n"
    )
    assert expected_line in content

    # Verify it sits between header end and footer start
    assert "    EphemerisTimePosVel\t\t\n\n" + expected_line in content
    assert expected_line + "\n\nEND Ephemeris\n" in content


def test_header_fields_use_exact_tab_whitespace_pattern(tmp_path):
    """Header field formatting matches the literal substrings the legacy tests rely on."""
    path = tmp_path / "fields.stk"
    header = StkHeader(
        num_points=42,
        epoch_jd=2459989.0,
        interpolation_method="Lagrange",
        interpolation_samples_m1=7,
        central_body="Moon",
        coordinate_system="J2000",
    )

    with StkWriter.open(str(path), header):
        pass

    text = path.read_text()
    assert text.startswith("stk.v.9.0\n")
    assert "BEGIN Ephemeris\n" in text
    assert "    NumberOfEphemerisPoints\t\t 42\n" in text
    assert "    CentralBody\t\t Moon\n" in text
    assert "    CoordinateSystem\t\t J2000\n" in text
    assert "    InterpolationMethod\t\t Lagrange\n" in text
    assert "    InterpolationSamplesM1\t\t 7\n" in text
    assert "    EphemerisTimePosVel\t\t\n" in text
    assert "END Ephemeris\n" in text


def test_writer_accepts_list_and_tuple_samples(tmp_path):
    """write_sample accepts any indexable [0]/[1]/[2] for pos and vel."""
    path = tmp_path / "list.stk"
    header = _basic_header(num_points=2)

    with StkWriter.open(str(path), header) as writer:
        writer.write_sample(0.0, [1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
        writer.write_sample(60.0, (7.0, 8.0, 9.0), (10.0, 11.0, 12.0))

    content = path.read_text()
    # Both lines present with relative seconds in the first column
    assert "  0.0000000000000000e+00" in content
    assert "  6.0000000000000000e+01" in content
