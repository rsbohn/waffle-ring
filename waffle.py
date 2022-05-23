# SPDX-FileCopyrightText: Copyright (c) 2022 Randall Bohn (dexter)
# SPDX-License-Identifier: MIT
import binascii
import os
import random
import time
import board
import busio
import microcontroller
import neopixel
"""
Experimental UART ring network for microcontrollers.

Wiring:
=======
[node-a]  [node-b]   [node-c]
TX -----> RX  TX --> RX
RX <---------------- TX
GND ----- GND ------ GND

Frame Format:
FC[MM][AAAAAA][NNNN][CCCCCCCC]<payload>FC
M: message type
A: origin address (0x800000 is 'anonymous')
N: length of <payload>
C: crc-32
"""

# Circuitpython: Metro-M4 or Feather RP2040 etc
uart = busio.UART(tx=board.TX, rx=board.RX, baudrate=115200, bits=8, parity=None, stop=1)
np = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1)
np.fill(0x999999)

LE = "little"
MAC = microcontroller.cpu.uid[-3:]
def encode(message_type: byte, payload: bytearray):
    header = bytearray(12)
    header[0] = 0xFC
    header[1] = message_type & 0xFF
    header[2:5] = MAC
    header[5:7] = len(payload).to_bytes(2,LE)
    header[7:11] = binascii.crc32(payload).to_bytes(4,LE)
    eb = b'\xFC'
    return header+payload+eb

def validate(frame):
    if frame[0] != 0xFC or frame[-1] != 0xFC: return False, "invalid frame"
    frame_length = int.from_bytes(frame[5:7],LE)
    body = frame[12:-1]
    if len(body) < frame_length: return False, "frame truncated"
    crca = binascii.crc32(body)
    crcb = int.from_bytes(frame[7:11],LE)
    if crca != crcb:
        return False, f"crc32 error: expected={crcb:X} actual={crca:X}"
    return True, None
def print_frame(frame):
    "print the frame"
    valid, reason = validate(frame)
    if valid:
        message_type = frame[1]
        origin = int.from_bytes(frame[2:5],LE)
        n = int.from_bytes(frame[5:7],LE)
        crc = int.from_bytes(frame[7:11],LE)
        eb = frame[-1]
        print(f"mt={message_type:X} origin={origin:X} len={n} crc32={crc:X}")
        print("OK ",frame[12:-1])
    else:
        print("ERR",reason)
def get_origin(frame):
    return frame[2:5]

last_packet_time = time.monotonic()
while True:
    now = time.monotonic()
    print("*****",now)
    np.fill(0x000000)
    n = uart.in_waiting
    if n > 0:
        np.fill(0x999900)
        f = uart.read(n)
        last_packet_time = time.monotonic()
        print_frame(f)
        if get_origin(f) == MAC:
            np.fill(0x000099)
            message=os.uname().machine
            uart.write(encode(0x80, message.encode("utf-8")))
        else:
            valid, reason = validate(f)
            if valid:
                np.fill(0x003300)
                uart.write(f)
            else:
                np.fill(0x990000)
                uart.write(encode(0x81, reason.encode("utf-8")))
    if now - last_packet_time > 2:
        np.fill(0x999999)
        uart.write(encode(0x80,"begin".encode("utf-8")))
    time.sleep(1)
