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
FC[MM][AAAAAA][NNNN][CCCCCCCC]<payload>FD
M: message type
A: origin address (0x800000 is 'anonymous')
N: length of <payload>
C: crc-32
"""

# Metro-M4 or Feather RP2040
if hasattr(board, "NEOPIXEL"):
    uart = busio.UART(tx=board.TX, rx=board.RX, baudrate=115200, bits=8, parity=None, stop=1)
    np = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1)
else:
    uart = busio.UART(tx=board.GP12, rx=board.GP13, baudrate=115200, bits=8, parity=None, stop=1)
    np = neopixel.NeoPixel(board.GP14, 4, brightness=0.1)
np.fill(0x999999)

BE = "big"
LE = "little"
MAC = microcontroller.cpu.uid[-3:]
TRAP_ON_FAULT=False
DUMP_INVALID_FRAMES=True
def encode(message_type: int, payload: bytearray):
    header = bytearray(12)
    header[0] = 0xFC
    header[1] = message_type & 0xFF
    header[2:5] = MAC
    header[5:7] = len(payload).to_bytes(2,LE)
    header[7:11] = binascii.crc32(payload).to_bytes(4,LE)
    eb = b'\xFD'
    return header+payload+eb

def validate(frame):
    if frame[0] != 0xFC: return False, "invalid frame"
    frame_length = int.from_bytes(frame[5:7],LE)
    bsize = len(frame)-12-1
    if bsize < frame_length: return False, "frame fragmented"
    if bsize > frame_length:
        print(f"*** expected {frame_length} found {bsize}")
        return False, "frame overrun"
    if frame[-1] != 0xFD: return False, "unterminated frame"
    body = frame[12:-1]
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
        print(f"mt={message_type:X} origin={origin:06X} len={n:03} crc32={crc:08X}", end=" ")
        print("OK ",frame[12:-1])
    else:
        print("ERR",reason)
def get_origin(frame):
    return frame[2:5]
def get_body_len(frame):
    return int.from_bytes(frame[5:7], LE)

def payloader():
    while True:
        yield os.uname().version
        yield os.uname().machine
payload = payloader()
last_packet_time = time.monotonic()

while True:
    now = time.monotonic()
    np.fill(0x000000)
    if uart.in_waiting > 0:
        np.fill(0x999900)
        head = uart.read(12)
        if head is None: continue
        seek = 0
        while len(head) > 1 and head[0] != 0xFC:
            b = uart.read(1)
            if b is None:
                np.fill(0)
            else:
                np.fill(0x990033)
                head = head[1:] + b
                seek+=1
            if seek > 12: break
        if head[0] != 0xFC:
            continue
        nBytes = get_body_len(head)+1
        np.fill(0x006633)
        body = b''
        while len(body) < nBytes:
            while uart.in_waiting < 1:
                time.sleep(0.01)
            b = uart.read(min(nBytes-len(body),8))
            if b is not None:
                body = body + b
        f = head + body
        last_packet_time = time.monotonic()
        print_frame(f)
        if get_origin(f) == MAC:
            np.fill(0x000099)
            message=next(payload)
            fnext=encode(0x80, message.encode("utf-8"))
            uart.write(fnext)
            time.sleep(0.03)
        else:
            valid, reason = validate(f)
            if valid:
                if f[1] <= 0x80:
                    np.fill(0x003300)
                else:
                    np.fill(0x663300)
                uart.write(f)
            else:
                np.fill(0x990000)
                if reason is None:
                    reason = "cosmic rays"
                else:
                    if DUMP_INVALID_FRAMES:
                        for x in range(0,len(f),4):
                            print(hex(int.from_bytes(f[x:x+4],BE)),end=' ')
                    if TRAP_ON_FAULT: break
                uart.write(encode(0x81, reason.encode("utf-8")))

    if now - last_packet_time > 2:
        print("no traffic")
        np.fill(0x996699)
        uart.write(encode(0x80,"begin".encode("utf-8")))
        last_packet_time = time.monotonic()
