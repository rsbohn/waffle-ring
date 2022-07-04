# SPDX-FileCopyrightText: Copyright (c) 2022 Randall Bohn (dexter)
# SPDX-License-Identifier: MIT
import board
import busio
import neopixel
import waffle
import time

if hasattr(board, "NEOPIXEL"):
    uart = busio.UART(tx=board.TX, rx=board.RX, baudrate=115200, bits=8, parity=None, stop=1)
    np = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1)
else:
    uart = busio.UART(tx=board.GP12, rx=board.GP13, baudrate=115200, bits=8, parity=None, stop=1)
    np = neopixel.NeoPixel(board.GP14, 4, brightness=0.1)
np.fill(0x999999)

ring = waffle.Ring(uart)

while True:
    np.fill(0x333300)
    frame = ring.receive()
    print(hex(int.from_bytes(frame.header[:2],waffle.BE)),
        hex(int.from_bytes(frame.header[2:5],waffle.LE)),
        int.from_bytes(frame.header[5:7],waffle.LE),
        frame.payload.decode(),
        hex(frame.footer[0]))
    if frame.is_mine():
        np.fill(0x000066)
        ring.send("hello ring")
    else:
        np.fill(0x006600)
        ring.forward(frame)
    time.sleep(0.5)
