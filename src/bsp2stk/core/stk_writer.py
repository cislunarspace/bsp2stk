"""STK v9.0 file writer.

This module owns the STK v9.0 file format. It is intentionally ignorant of
BSP files, jplephem, spiceypy, and bsp2stk.io — it only knows how to take a
header description plus a stream of (relative seconds, position, velocity)
samples and produce a valid STK v9.0 ephemeris file.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, fields, replace
from typing import IO, Any, Iterator, Sequence

# Note: jd_to_stk_epoch / jd_to_yyddd are imported lazily inside
# _write_header() to avoid a circular import — bsp2stk.core.convert
# imports StkFormat / StkHeader / StkWriter from this module at top
# level.


# ---------------------------------------------------------------------------
# Allowed values for STK header fields (single source of truth; the GUI
# imports these instead of maintaining its own copies).
# ---------------------------------------------------------------------------

STK_INTERPOLATION_CHOICES: tuple[str, ...] = (
    "Lagrange",
    "Hermite",
    "Linear",
)

STK_CENTRAL_BODY_CHOICES: tuple[str, ...] = (
    "Earth",
    "Moon",
    "Sun",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "Venus",
    "Mercury",
)

STK_COORDINATE_CHOICES: tuple[str, ...] = (
    "J2000",
    "EME2000",
    "ICRF",
    "Fixed",
    "TOD",
    "TrueOfDate",
)


@dataclass(frozen=True)
class StkFormat:
    """Immutable bundle of STK header format parameters.

    Replaces the previous pattern of passing 5 loose kwargs through every
    layer. ``step_seconds`` is included because it travels alongside the
    header knobs through the GUI -> worker -> conversion pipeline even
    though it is not itself written to the header.
    """

    step_seconds: float
    interpolation_method: str
    interpolation_samples_m1: int
    central_body: str
    coordinate_system: str

    @classmethod
    def default(cls) -> "StkFormat":
        """Return the canonical default :class:`StkFormat`."""
        return cls(
            step_seconds=60.0,
            interpolation_method="Lagrange",
            interpolation_samples_m1=5,
            central_body="Earth",
            coordinate_system="J2000",
        )

    def with_overrides(self, **kwargs: Any) -> "StkFormat":
        """Return a new :class:`StkFormat` with selected fields replaced.

        ``None`` values are treated as "no override" — convenient for
        forwarding optional kwargs from backwards-compatible callers.

        Raises:
            TypeError: If ``kwargs`` contains an unknown field name.
        """
        allowed = {f.name for f in fields(self)}
        unknown = [name for name in kwargs if name not in allowed]
        if unknown:
            raise TypeError(
                f"StkFormat.with_overrides() got unexpected field(s): "
                f"{sorted(unknown)}; allowed fields are {sorted(allowed)}"
            )
        effective = {name: value for name, value in kwargs.items() if value is not None}
        if not effective:
            return self
        return replace(self, **effective)


@dataclass(frozen=True)
class StkHeader:
    """Header parameters for an STK v9.0 ephemeris file.

    Attributes:
        num_points: Value emitted as NumberOfEphemerisPoints. Must be known
            up front (cleaner than seek/rewrite — and ``convert_bsp_to_stk``
            already computes this before sampling).
        epoch_jd: Julian Date of the epoch; used to derive ScenarioEpoch
            and the JDate / YYDDD comment lines.
        interpolation_method: Value emitted as InterpolationMethod.
        interpolation_samples_m1: Value emitted as InterpolationSamplesM1.
        central_body: Value emitted as CentralBody.
        coordinate_system: Value emitted as CoordinateSystem.
    """

    num_points: int
    epoch_jd: float
    interpolation_method: str
    interpolation_samples_m1: int
    central_body: str
    coordinate_system: str

    @classmethod
    def from_format(
        cls, fmt: "StkFormat", num_points: int, epoch_jd: float
    ) -> "StkHeader":
        """Build an :class:`StkHeader` from an :class:`StkFormat` plus the
        per-conversion ``num_points`` and ``epoch_jd``.

        ``StkFormat.step_seconds`` is *not* part of the header itself —
        it controls the sampling loop, not the bytes written — so it is
        intentionally dropped here.
        """
        return cls(
            num_points=num_points,
            epoch_jd=epoch_jd,
            interpolation_method=fmt.interpolation_method,
            interpolation_samples_m1=fmt.interpolation_samples_m1,
            central_body=fmt.central_body,
            coordinate_system=fmt.coordinate_system,
        )


class StkWriter:
    """Streaming writer for the STK v9.0 ephemeris file format.

    Usage:

        header = StkHeader(...)
        with StkWriter.open(path, header) as writer:
            for sample in samples:
                writer.write_sample(seconds, pos, vel)
    """

    def __init__(self, file_obj: IO[str], header: StkHeader) -> None:
        self._file = file_obj
        self._header = header
        self._header_written = False
        self._footer_written = False

    @classmethod
    @contextmanager
    def open(cls, path: str, header: StkHeader) -> Iterator["StkWriter"]:
        """Open ``path`` for writing and yield a configured StkWriter.

        The header is written on entry and the footer on a clean exit. If
        the caller raises, the partial file is left in place — the caller
        is responsible for cleanup, matching the behaviour of a plain
        ``open(path, "w")``.
        """
        with open(path, "w") as file_obj:
            writer = cls(file_obj, header)
            writer._write_header()
            yield writer
            writer._write_footer()

    def _write_header(self) -> None:
        if self._header_written:
            return
        # Local import: avoids circular dependency with bsp2stk.core.convert.
        from bsp2stk.core.convert import jd_to_stk_epoch, jd_to_yyddd

        h = self._header
        epoch_str = jd_to_stk_epoch(h.epoch_jd)
        yyddd_str = jd_to_yyddd(h.epoch_jd)

        f = self._file
        f.write("stk.v.9.0\n")
        f.write("\n")
        f.write("BEGIN Ephemeris\n")
        f.write("\n")
        f.write(f"    NumberOfEphemerisPoints\t\t {h.num_points}\n")
        f.write("\n")
        f.write(f"    ScenarioEpoch\t\t {epoch_str}\n")
        f.write("\n")
        f.write(f"# Epoch in JDate format: {h.epoch_jd:.14f}\n")
        f.write(f"# Epoch in YYDDD format:   {yyddd_str}\n")
        f.write("\n")
        f.write("\n")
        f.write(f"    InterpolationMethod\t\t {h.interpolation_method}\n")
        f.write("\n")
        f.write(f"    InterpolationSamplesM1\t\t {h.interpolation_samples_m1}\n")
        f.write("\n")
        f.write(f"    CentralBody\t\t {h.central_body}\n")
        f.write("\n")
        f.write(f"    CoordinateSystem\t\t {h.coordinate_system}\n")
        f.write("\n")
        f.write(
            f"# Time of first point: {epoch_str}.000000000 UTCG"
            f" = {h.epoch_jd:.14f} JDate"
            f" = {yyddd_str} YYDDD\n"
        )
        f.write("\n")
        f.write("    EphemerisTimePosVel\t\t\n")
        f.write("\n")
        self._header_written = True

    def write_sample(
        self,
        seconds_since_epoch: float,
        pos: Sequence[float],
        vel: Sequence[float],
    ) -> None:
        """Write a single ephemeris sample line.

        ``pos`` and ``vel`` may be any object supporting ``[0]``, ``[1]``,
        ``[2]`` indexing (tuples, lists, numpy arrays).
        """
        self._file.write(
            f" {seconds_since_epoch:23.16e}"
            f"  {pos[0]:23.16e}  {pos[1]:23.16e}  {pos[2]:23.16e}"
            f"  {vel[0]:23.16e}  {vel[1]:23.16e}  {vel[2]:23.16e}\n"
        )

    def _write_footer(self) -> None:
        if self._footer_written:
            return
        self._file.write("\n")
        self._file.write("\n")
        self._file.write("END Ephemeris\n")
        self._footer_written = True
