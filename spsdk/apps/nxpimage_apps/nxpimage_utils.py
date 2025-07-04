#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 NXP
#
# SPDX-License-Identifier: BSD-3-Clause
"""Nxpimage utils group."""

import logging
import os
from typing import Optional

import click

from spsdk.apps.utils.common_cli_options import (
    SpsdkClickGroup,
    spsdk_config_option,
    spsdk_output_option,
)
from spsdk.apps.utils.utils import INT, SPSDKAppError
from spsdk.exceptions import SPSDKError
from spsdk.utils.binary_image import BinaryImage
from spsdk.utils.config import Config
from spsdk.utils.misc import (
    BinaryPattern,
    Endianness,
    align,
    align_block,
    get_printable_path,
    load_binary,
    load_text,
    value_to_int,
    write_file,
)

logger = logging.getLogger(__name__)


@click.group(name="utils", cls=SpsdkClickGroup)
def nxpimage_utils_group() -> None:
    """Group of utilities."""


@nxpimage_utils_group.group(name="binary-image", cls=SpsdkClickGroup)
def bin_image_group() -> None:
    """Binary Image utilities."""


@bin_image_group.command(name="create", no_args_is_help=True)
@click.option(
    "-s",
    "--size",
    type=INT(),
    required=True,
    help="Size of file to be created.",
)
@click.option(
    "-p",
    "--pattern",
    type=str,
    default="zeros",
    help="Pattern of created file ('zeros', 'ones', 'rand', 'inc' or any number value).",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["BIN", "HEX", "S19"], case_sensitive=False),
    default="BIN",
    help="Output format.",
)
@spsdk_output_option()
def binary_create_command(size: int, pattern: str, output_format: str, output: str) -> None:
    """Create binary file with pattern.

    The helper utility to create simple binary file with pattern.
    """
    binary_create(size, pattern, output_format, output)


def binary_create(size: int, pattern: str, output_format: str, output: str) -> None:
    """Create binary file with pattern."""
    image = BinaryImage(name="", size=size, pattern=BinaryPattern(pattern))
    image.validate()

    image.save_binary_image(output, file_format=output_format)

    logger.info(f"Created file:\n{str(image)}")
    logger.info(f"Created file graph:\n{image.draw()}")
    click.echo(f"Success. (Created binary file: {output} )")


@bin_image_group.command(name="export", no_args_is_help=True)
@spsdk_config_option()
@spsdk_output_option()
@click.option(
    "-p",
    "--keep-padding",
    is_flag=True,
    default=False,
    help="Preserve initial padding before the first image region instead of trimming it (default behavior).",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["BIN", "HEX", "S19"], case_sensitive=False),
    default="BIN",
    help="Output format.",
)
def binary_export_command(
    config: Config, output: str, keep_padding: bool, output_format: str
) -> None:
    """Export merged binary images together by description in YAML/JSON configuration.

    The configuration template files could be generated by subcommand 'utils binary-image get-template'.
    """
    binary_export(config, output, keep_padding, output_format)


def binary_export(
    config: Config, output: str, keep_padding: bool, output_format: str = "BIN"
) -> None:
    """Export merged binary images together by description in YAML/JSON configuration."""
    image = BinaryImage.load_from_config(config)
    if not keep_padding:
        image.update_offsets()
        if image.offset:
            logger.info(f"Adjusting image offsets by zeroing base offset: {image.offset}")
            image.offset = 0

    try:
        image.validate()
    except SPSDKError as exc:
        click.echo(f"Image Validation fail:\n{image.draw()}")
        raise SPSDKError(f"Image validation failed: {exc}") from exc

    # Export data and save in the requested format
    image.save_binary_image(output, file_format=output_format)

    logger.info(f"Merged Image:\n{str(image)}")
    logger.info(f"Merged Image:\n{image.draw()}")
    click.echo(
        f"Success. (Merged image: {get_printable_path(output)} created in {output_format} format.)"
    )


@bin_image_group.command(name="extract", no_args_is_help=True)
@click.option(
    "-b",
    "--binary",
    type=click.Path(exists=True, readable=True),
    required=True,
    help="Path to binary file to be used to extract chunk from.",
)
@click.option(
    "-a",
    "--address",
    type=str,
    required=True,
    help="Address of extracted chunk.",
)
@click.option(
    "-s",
    "--size",
    type=str,
    required=True,
    help="Size of extracted chunk. For '0' it extract rest of the file from given address.",
)
@spsdk_output_option()
def binary_extract_command(binary: str, address: str, size: str, output: str) -> None:
    """Extract chunk from binary file."""
    binary_extract(binary, address, size, output)


def binary_extract(binary: str, address: str, size: str, output: str) -> None:
    """Extract chunk from binary file."""
    bin_data = load_binary(binary)
    start = value_to_int(address)
    size_int = value_to_int(size)
    if not size_int:
        size_int = len(bin_data) - start
    end = start + size_int

    if end > len(bin_data):
        click.echo(f"The required binary chunk is out of [{binary}] file space.")
        return
    write_file(bin_data[start:end], output, mode="wb")
    click.echo(f"Success. (Extracted chunk: {get_printable_path(output)} created.)")


@bin_image_group.command(name="convert", no_args_is_help=True)
@click.option(
    "-i",
    "--input-file",
    type=click.Path(exists=True, readable=True),
    required=True,
    help="Path to BIN/HEX/S19/ELF file to be converted.",
)
@click.option(
    "-p",
    "--keep-padding",
    is_flag=True,
    default=False,
    help="Preserve initial padding before the first image region instead of trimming it (default behavior).",
)
@click.option(
    "-s",
    "--split-image",
    is_flag=True,
    default=False,
    help="Split the output into individual sub-image files in the same directory as the output file.",
)
@click.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["BIN", "HEX", "S19"], case_sensitive=False),
    required=True,
    help="Output format.",
)
@spsdk_output_option()
def binary_convert_command(
    input_file: str, keep_padding: bool, split_image: bool, output_format: str, output: str
) -> None:
    """Convert input data file into selected format."""
    binary_convert(input_file, keep_padding, split_image, output_format, output)


def binary_convert(
    input_file: str, keep_padding: bool, split_image: bool, output_format: str, output: str
) -> None:
    """Convert input data file into selected format."""
    image = BinaryImage.load_binary_image(input_file)
    if not keep_padding:
        image.update_offsets()
        if image.offset:
            image.offset = 0

    logger.info(image.draw())
    if image.offset:
        click.echo(f"Image base offset: {hex(image.offset)} ({image.offset} bytes)")
    if split_image:
        if len(image.sub_images) > 1:
            logger.info(f"Image contains {len(image.sub_images)} sub images.")
            for sub_img in image.sub_images:
                sub_img_path = _update_path_with_address(output, sub_img.offset)
                sub_img.save_binary_image(sub_img_path, file_format=output_format)
                click.echo(
                    f"Success. (Converted sub-image: {get_printable_path(sub_img_path)} created.)"
                )
            return
        logger.warning("Image contains only one sub-image. Skipping split.")
    image.save_binary_image(output, file_format=output_format)
    click.echo(f"Success. (Converted image: {get_printable_path(output)} created.)")


def _update_path_with_address(file_path: str, address: int) -> str:
    # Split the path into directory, filename, and extension
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)

    # Create new filename with address
    new_filename = f"{name}_0x{address:X}{ext}"

    # Join directory with new filename
    return os.path.join(directory, new_filename)


@bin_image_group.command(name="get-template", no_args_is_help=True)
@spsdk_output_option(force=True)
def binary_get_template_command(output: str) -> None:
    """Create template of configuration in YAML format.

    The template file name is specified as argument of this command.
    """
    binary_get_template(output)


def binary_get_template(output: str) -> None:
    """Create template of configuration in YAML format."""
    click.echo(f"Creating {get_printable_path(output)} template file.")
    write_file(BinaryImage.get_config_template(), output)


@bin_image_group.command(name="align", no_args_is_help=True)
@click.option(
    "-i",
    "--input-file",
    type=click.Path(file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
    help="Binary file name to be aligned.",
)
@spsdk_output_option(
    required=False,
    help="Aligned file name. If not specified, input file will be updated.",
)
@click.option(
    "-a",
    "--alignment",
    default=1,
    type=INT(),
    help="Alignment size.",
)
@click.option(
    "-p",
    "--pattern",
    type=str,
    default="zeros",
    help="Pattern of used padding ('zeros', 'ones', 'rand', 'inc' or any number value).",
)
def binary_align_command(input_file: str, output: str, alignment: int, pattern: str) -> None:
    """Align binary file to provided alignment and padded with specified pattern."""
    binary_align(input_file, output, alignment, pattern)


def binary_align(
    input_file: str, output: Optional[str] = None, alignment: int = 1, pattern: str = "zeros"
) -> None:
    """Align binary file to provided alignment and padded with specified pattern.

    :param input_file: Input file name.
    :param output: Output file name. If not specified, input file will be updated.
    :param alignment: Size of alignment block.
    :param pattern: Padding pattern.

    :raises SPSDKError: Invalid input arguments.
    """
    if not input_file or not os.path.isfile(input_file):
        raise SPSDKError("Binary file alignment: Invalid input file")
    if alignment <= 0:
        raise SPSDKError("Binary file alignment: Alignment value must be 1 or greater.")
    if not output:
        output = input_file
    binary = align_block(data=load_binary(input_file), alignment=alignment, padding=pattern)
    write_file(binary, output, mode="wb")
    click.echo(
        f"The {input_file} file has been aligned to {len(binary)} ({hex(len(binary))}) bytes \
            and stored into {output}"
    )


@bin_image_group.command(name="pad", no_args_is_help=True)
@click.option(
    "-i",
    "--input-file",
    type=click.Path(file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
    help="Binary file name to be padded.",
)
@spsdk_output_option(
    required=False,
    help="Padded file name. If not specified, input file will be updated.",
)
@click.option(
    "-s",
    "--size",
    required=True,
    type=INT(),
    help="Result file size.",
)
@click.option(
    "-p",
    "--pattern",
    type=str,
    default="zeros",
    help="Pattern of used padding ('zeros', 'ones', 'rand', 'inc' or any number value).",
)
def binary_pad_command(input_file: str, output: str, size: int, pattern: str) -> None:
    """Pad binary file to provided final size with specified pattern."""
    binary_pad(input_file, output, size, pattern)


def binary_pad(
    input_file: str, output: Optional[str] = None, size: int = 1, pattern: str = "zeros"
) -> None:
    """Pad binary file to provided final size with specified pattern.

    :param input_file: Input file name.
    :param output: Output file name. If not specified, input file will be updated.
    :param size: Final size of file.
    :param pattern: Padding pattern.

    :raises SPSDKError: Invalid input arguments.
    """
    if not input_file or not os.path.isfile(input_file):
        raise SPSDKError("Binary file alignment: Invalid input file")
    if not output:
        output = input_file
    binary = load_binary(input_file)
    if len(binary) < size:
        binary = align_block(data=binary, alignment=size, padding=pattern)
    write_file(binary, output, mode="wb")

    click.echo(
        f"The '{input_file}' file has been padded to {len(binary)} ({hex(len(binary))}) byte size and "
        f"stored into '{output}'"
    )


@nxpimage_utils_group.group(name="convert", cls=SpsdkClickGroup)
def convert() -> None:  # pylint: disable=unused-argument
    """Conversion utilities."""


@convert.command(name="hex2bin", no_args_is_help=True)
@click.option(
    "-i",
    "--input-file",
    type=click.Path(exists=True, readable=True),
    required=True,
    help="Path to text file with hexadecimal string to be converted to binary.",
)
@click.option(
    "-r",
    "--reverse",
    is_flag=True,
    help="The resulting binary bytes will be stored in reverse order (for example SBKEK in elftosb requires that).",
)
@spsdk_output_option()
def convert_hex2bin_command(input_file: str, reverse: bool, output: str) -> None:
    """Convert file with hexadecimal string into binary file with optional reverse order of stored bytes."""
    convert_hex2bin(input_file, reverse, output)


def convert_hex2bin(input_file: str, reverse: bool, output: str) -> None:
    """Convert file with hexadecimal string into binary file with optional reverse order of stored bytes."""
    try:
        value = bytearray.fromhex(load_text(input_file))
    except (SPSDKError, ValueError) as e:
        raise SPSDKAppError(f"Failed loading hexadecimal value from: {input_file}") from e
    if reverse:
        value.reverse()
    write_file(value, output, mode="wb")
    click.echo(f"Success. Converted file: {output}")


@convert.command(
    name="bin2hex",
    no_args_is_help=True,
    short_help="Convert binary file to hexadecimal text file.",
    help="Convert binary file into hexadecimal text file with optional reverse order of stored bytes.",
)
@click.option(
    "-i",
    "--input-file",
    type=click.Path(exists=True, readable=True),
    required=True,
    help="Path to binary file with to be converted to hexadecimal text file.",
)
@click.option(
    "-r",
    "--reverse",
    is_flag=True,
    help="The result binary bytes will be stored in reverse order (for example SBKEK in elftosb this required).",
)
@spsdk_output_option()
def convert_bin2hex_command(input_file: str, reverse: bool, output: str) -> None:
    """Convert binary file into hexadecimal text file with optional reverse order of stored bytes."""
    convert_bin2hex(input_file, reverse, output)


def convert_bin2hex(input_file: str, reverse: bool, output: str) -> None:
    """Convert binary file into hexadecimal text file with optional reverse order of stored bytes."""
    value = bytearray(load_binary(input_file))
    if reverse:
        value.reverse()
    write_file(value.hex(), output, mode="w")
    click.echo(f"Success. Converted file: {output}")


@convert.command(name="bin2carr", no_args_is_help=True)
@click.option(
    "-i",
    "--input-file",
    type=click.Path(exists=True, readable=True),
    required=True,
    help="Path to binary file to be converted to C array.",
)
@click.option(
    "-n",
    "--name",
    type=str,
    help="The output C array name, if not specified the name of input file will be used.",
)
@click.option(
    "-t",
    "--type",
    "output_type",
    type=click.Choice(["uint8_t", "uint16_t", "uint32_t", "uint64_t"], case_sensitive=False),
    default="uint8_t",
    help="The output C array type.",
)
@click.option(
    "-e",
    "--endian",
    type=click.Choice(Endianness.values(), case_sensitive=False),
    default=Endianness.BIG.value,
    help="The binary input file endian.",
)
@click.option(
    "-p",
    "--padding",
    type=str,
    help="The padding value in case of non aligned binary image.",
)
@click.option(
    "-c",
    "--count-per-line",
    type=click.IntRange(1, 1024),
    default=8,
    help="The array items count per line.",
)
@click.option(
    "--tab",
    type=click.IntRange(0, 32),
    default=4,
    help="The tabulator size for new line.",
)
@spsdk_output_option(
    required=False,
    help=(
        "Path to output text file with created C array, "
        "if not specified the output will be printed into standard output."
    ),
)
def convert_bin2carr(
    input_file: str,
    name: str,
    output_type: str,
    endian: str,
    padding: str,
    count_per_line: int,
    tab: int,
    output: str,
) -> None:
    """Convert binary file into C array string.

    Default output is byte representation, but it could be
    converted to 16/32 or 64 bit unsigned types with specified endianness.
    """
    raw_binary = load_binary(input_file)
    width = {"uint8_t": 1, "uint16_t": 2, "uint32_t": 4, "uint64_t": 8}[output_type]

    if len(raw_binary) != align(len(raw_binary), width) and padding is None:
        raise SPSDKAppError("Unaligned binary image, if still to be used, define '-p' padding.")

    binary = align_block(
        data=raw_binary, alignment=width, padding=BinaryPattern(padding) if padding else None
    )
    rest_bytes = len(binary)
    count = rest_bytes // width
    name = name or os.path.splitext(os.path.basename(input_file))[0]
    index = 0
    ret = f"const {output_type} {name}[{count}] = {{\n"
    while rest_bytes:
        line_cnt = min(count_per_line, rest_bytes // width)
        comment = f"// 0x{index:09_X}"
        ret += " " * tab
        for _ in range(line_cnt):
            data = bytearray(binary[index : index + width])
            if endian.lower() == Endianness.LITTLE:
                data.reverse()
            ret += "0x" + data.hex() + ", "
            index += width
            rest_bytes -= width
        ret += f" {comment}\n"
    ret += "};\n"

    if output:
        write_file(ret, output)
        click.echo(f"Success. Created C file: {output}")
    else:
        click.echo(ret)
