.. |br| raw:: html

   <br/>

===================
User Guide - el2go
===================
This user’s guide describes how to interface with the *EdgeLock 2GO service* and *Edgelock 2GO NXP Provisioning Firmware* using the *el2go* application.

The *el2go* application is a command-line utility used on the host computer to act as an intermediate layer bertween Edgelock 2GO Service's REST API and Edgelock 2GO NXP Provisioning Firmware running on a device . The application only sends one command per invocation.

-------------
Prerequisites
-------------
#. Activate and configure your EdgeLock 2GO account (https://www.nxp.com/products/security-and-authentication/secure-service-2go-platform/edgelock-2go:EDGELOCK-2GO)
#. Any Serial communicator

----------------------------------
Setup of the EdgeLock 2GO platform
----------------------------------
In the documentation menu of your EdgeLock 2GO account available at https://www.edgelock2go.com you can find the documents which explain how to setup the EdgeLock 2GO Account to:

#. Create EdgeLock 2GO API key
#. Create device group
#. Create Secure Object
#. Assign Secure Object to Device Group

-------------
Communication
-------------

The *el2go* application communicates with the *EdgeLock 2GO API* over the host computer’s internet network and
with the *EdgeLock 2GO NXP Provisioning Firmware* over the host computer’s UART (Serial Port) or USB connections.

*EdgeLock 2GO NXP Provisioning Firmware* supports other peripherals such as I2C and SPI. However, the *el2go* application cannot interface with the MCU bootloader over these transports without external hardware.

el2go - USB
============

*el2go* could be connected to MCU Bootloader and EdgeLock 2GO NXP Provisioning Firmware over USB HID.

:ref:`USB device identification in SPSDK`

el2go - UART
=============

*el2go* could be connected to MCU bootloader and EdgeLock 2GO NXP Provisioning Firmware over UART.

:ref:`UART device identification in SPSDK`

el2go - BUSPAL
===============

The BusPal acts as a bus translator running on selected platforms. BusPal assists *el2go* in carrying out commands and responses from the target device through an established connection with *el2go* over UART, and the target device over I2C or SPI.

----------------------
Command line interface
----------------------
*el2go* consist of a set of sub-commands followed by options and arguments.

Some of these commands are used for communication with *EdgeLock 2GO* and others with the *EdgeLock 2GO NXP Provisioning Firmware* running on device.

.. click:: spsdk.apps.el2go:main
    :prog: el2go
    :nested: full

