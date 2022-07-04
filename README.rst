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
- power: nod0 USB -> node1 VBUS -> node2 VBUS

### Phase 2 (future)

- Custom carrier board with space for one Feather board and four Picos.
- One Featherwing 'slot'
