waffle-ring
===========

A UART ring network for microcontrollers

Why build a waffle-ring?
------------------------

- You need more processing power

You can use one microcontroller for the 'UI' and pass the processing to one or more coprocessors.

- Concurrent multiprocessing

Spread your application to multiple 'threads'.

- Why not?

It might be fun.

The Protocol
----

Physical Layer:

The physical layer is a ring network using UARTs running at 115200 baud. Refer to the Phase 1 description (below).

Data Link Layer:

Responsible for transfer of frames from one node to the next.

A frame consists of a 12 byte header and a variable length payload. Fields in the header are arranged little endian, with the least significant byte first.

[0:1] Frame Type
[2:5] Source MAC
[5:7] Length of payload
[7:11] 32 bit CRC of payload

Each frame is preceded by a one byte FRAME_BEGIN code (0xFC).

Each frame is followed by a two byte FRAME_END code (0xFF 0xFF).

Frame Reception:

- Seek the FRAME_BEGIN code
- Read the 12 byte header
- Check that (N= payload length) <= max, else raise ValueError "payload size > max"
- Read N bytes for the payload
- Read the FRAME_END code else raise "unterminated frame"
- Validate the CRC else raise "invalid CRC"
- Return the frame.

Idle Frames: 0x8100

When a node receives a packet that it sent (the frame source MAC is the node's MAC)
it should send an Idle frame. The frame type should be 0x8100.
The payload can be anything, usually twelve bytes or less.

Advertisement Frames: 0x8000

If a node has no pending messages when it receives an idle frame
it should send an advertisement.

Frame Type: 0x8000 Payload: Name of the node.

Nodes will use the advertisement frames to build a list of all nodes on the network.

Error Frames: 0x8200

Nodes may send error frames to signal error conditions.

Message Frames: type < 0x8000

Message frames cary the data of higher network layers.

0x4000 Watchdog/Synchronization services
0x4100 File services
0x4200 Real Time Clock




Reference Implementation
----

### Phase 0

Raspberry Pi Pico, loopback connection

The network can run in loopback mode using a single Raspberry Pi Pico.

### Phase 1

A three node network for mainline development.

Node 0: Adafruit Feather RP-2040

Node 1: Raspberry Pi Pico

Node 2: Raspberry Pi Pico

Wiring: 

- common ground connection
- node0 tx -> node1 rx (GP13)
- node1 tx (GP12) -> node2 rx (GP13)
- node2 tx (GP12) -> node0 rx
- power: node0 USB -> node1 VBUS -> node2 VBUS

### Phase 2 (future)

- Custom carrier board with space for one Feather board and four Picos.
- One Featherwing 'slot'
