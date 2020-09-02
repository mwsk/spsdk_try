#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2020 NXP
#
# SPDX-License-Identifier: BSD-3-Clause

"""Common utils for DAT module."""
import contextlib
import math
import os
from typing import Union, Iterator

from spsdk import crypto
from spsdk.crypto import utils_cryptography


def reconstruct_signature(signature_bytes: bytes) -> bytes:
    """Reconstructs signature.

    :param signature_bytes: signature's bytes
    :return: reconstructed signature
    """
    r_bytes = signature_bytes[:66]
    r = int.from_bytes(r_bytes, 'big')
    s_bytes = signature_bytes[66:132]
    s = int.from_bytes(s_bytes, 'big')
    signature = utils_cryptography.encode_dss_signature(r, s)
    return signature


def ecc_public_numbers_to_bytes(public_numbers: crypto.EllipticCurvePublicNumbers, length: int = 66) -> bytes:
    """Converts public numbers from ECC key into bytes.

    :param public_numbers: instance of ecc public numbers
    :param length: length of bytes object to use
    :return: bytes representation
    """
    x = public_numbers.x
    y = public_numbers.y
    length = length or math.ceil(x.bit_length() / 8)
    x_bytes = x.to_bytes(length, 'big')
    y_bytes = y.to_bytes(length, 'big')
    return x_bytes + y_bytes


def rsa_key_to_bytes(key: Union[crypto.RSAPublicKey, crypto.RSAPrivateKeyWithSerialization],
                     exp_length: int = None,
                     modulus_length: int = None) -> bytes:
    """Converts RSA key into bytes.

    :param key: Union of types: RSAPublicKey, RSAPrivateKeyWithSerialization
    :param exp_length: Length of exponent's bytes to use if none it will be calculated
    :param modulus_length: Length of modulus's bytes to use if none it will be calculated
    :return: Combined modulus and exponent bytes
    """
    exp_rotk = key.public_numbers().e  # type: ignore
    mod_rotk = key.public_numbers().n  # type: ignore
    exp_length = exp_length or math.ceil(exp_rotk.bit_length() / 8)
    modulus_length = modulus_length or math.ceil(mod_rotk.bit_length() / 8)
    exp_rotk_bytes = exp_rotk.to_bytes(exp_length, 'big')
    mod_rotk_bytes = mod_rotk.to_bytes(modulus_length, 'big')
    return mod_rotk_bytes + exp_rotk_bytes


def ecc_key_to_bytes(key: crypto.EllipticCurvePublicKey, length: int = 66) -> bytes:
    """Converts key into bytes.

    :param key: instance of ECC Public Key
    :param length: length of bytes object to use
    :return: bytes representation
    """
    public_numbers = key.public_numbers()
    return ecc_public_numbers_to_bytes(public_numbers=public_numbers,
                                       length=length)


@contextlib.contextmanager
def use_working_directory(path: str) -> Iterator[None]:
    # pylint: disable=missing-yield-doc
    """Execute the block in given directory.

    Cd into specific directory.
    Execute the block.
    Change the directory back into the original one.

    :param path: the path, where the current directory will be changed to
    """
    current_dir = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(current_dir)
        assert os.getcwd() == current_dir
