# SPDX-FileCopyrightText: Copyright (c) 2022 Randall Bohn (dexter)
# SPDX-License-Identifier: MIT

import binascii
import microcontroller
import time

MAC = microcontroller.cpu.uid[-3:]
LE = "little"
BE = "big"
class Frame:
    """I am a ring network Frame."""
    #message types
    IDLE=0x80
    ERROR=0x81
    BEGIN=0xFC
    END=0xFD
    @staticmethod
    def from_string(s:str) -> Frame:
        return Frame(Frame.IDLE, s.encode("utf-8"))
    def __init__(self, messageType:int, payload:bytearray):
        self.header = bytearray(12)
        self.header[0] = Frame.BEGIN
        self.header[1] = messageType & 0xFF
        self.header[2:5] = MAC
        self.header[5:7] = len(payload).to_bytes(2, LE)
        crc = binascii.crc32(payload)
        self.header[7:11] = crc.to_bytes(4, LE)
        self.payload = payload
        self.footer = bytearray([Frame.END])
    def is_mine(self) -> bool:
        return self.header[2:5]==MAC
    @property
    def size(self):
        return int.from_bytes(self.header[5:7], LE)

class Ring:
    """I can send and receive Frames"""
    def __init__(self, uart):
        self.uart = uart
    def receive(self):
        frame = Frame(0,b'')
        while self.uart.in_waiting < 12:
            time.sleep(0.1)
        frame.header = self.uart.read(12)
        if frame.header[0]==Frame.BEGIN:
            bsize = frame.size
            payload = b''
            while len(payload) < bsize:
                if self.uart.in_waiting > 0:
                    n = min(bsize-len(payload), 8)
                    payload = payload + self.uart.read(n)
            frame.payload = payload
            footer = self.uart.read(1)
        return frame
    def send(self, message:str):
        time.sleep(0.3)
        pass
    def forward(self, frame:Frame):
        time.sleep(0.3)
        self.uart.write(frame.header)
        self.uart.write(frame.payload)
        self.uart.write(frame.footer)
        pass
