import typing as t

import click

from .recorder import (
    IORecorder,
    _isvalid_video_format,
)


def validate_fname(
    ctx: click.Context,
    param: str,
    value: t.Optional[str],
) -> t.Optional[str]:
    if value is None or _isvalid_video_format(value):
        return value
    raise click.BadParameter(f"'{value}' has an invalid extension.")


def validate_interval(
    ctx: click.Context,
    param: str,
    value: float,
) -> float:
    if value > 0:
        return value
    raise click.BadParameter(
        "Parameter 'interval' must be a positive number."
    )


def validate_pin(
    ctx: click.Context,
    param: str,
    value: int,
) -> int:
    if 0 <= value <= 26:
        return value
    raise click.BadParameter("Parameter 'pin' must be an integer of 0 ~ 26.")


def validate_resolution(
    ctx: click.Context,
    param: str,
    value: str,
) -> t.Tuple[int, int]:
    value = value.split(":")
    if len(value) != 2:
        raise click.BadParameter(
            ""
        )

    try:
        width, height = int(value[0]), int(value[1])
    except ValueError as e:
        raise click.BadParameter() from e
    else:
        return (width, height)


def validate_timeout(
    ctx: click.Context,
    param: str,
    value: t.Optional[str],
) -> float:
    if value is None:
        return -1.

    timesum = 0
    temp = []
    for char in value:
        if str.isnumeric(char) or char == ".":
            temp.append(char)
            continue

        alpha = str.lower(char)
        num = float("".join(temp))
        temp.clear()

        if alpha == "h":
            timesum += num * 3600
        elif alpha == "m":
            timesum += num * 60
        elif alpha == "s":
            timesum += num
        else:
            raise click.BadParameter(f"'{value}' has an invalid time format.")
    if len(temp):
        timesum += float("".join(temp))

    return timesum


@click.command()
@click.argument(
    "pin",
    type=int,
    callback=validate_pin,
)
@click.option(
    "-f",
    "--fname",
    callback=validate_fname,
)
@click.option(
    "-i",
    "--interval",
    type=float,
    default=1.,
    show_default=True,
    callback=validate_interval,
)
@click.option(
    "-r",
    "--resolution",
    default="640:480",
    show_default=True,
    callback=validate_resolution,
)
@click.option(
    "--start-with-low",
    is_flag=True,
    default=False,
    show_default=True,
)
@click.option(
    "-t",
    "--timeout",
    callback=validate_timeout,
)
def main(
    pin: int,
    fname: t.Optional[str],
    interval: float,
    resolution: t.Tuple[int, int],
    start_with_low: bool,
    timeout: float,

) -> None:
    start_level = not start_with_low
    with IORecorder(pin, fname=fname, resolution=resolution) as rec:
        rec.start_record(
            interval=interval,
            timeout=timeout,
            start_level=start_level,
        )
