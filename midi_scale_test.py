import time
import rtmidi


# Define the MIDI commands for a C-major scale
notes = [60, 62, 64, 65, 67, 69, 71, 72]  # MIDI note numbers for C4 to B4

out = rtmidi.MidiOut()
ports = out.get_ports()
print(ports)

out.open_port(1)

for note in notes:
    note_on = [0x94, note, 100] #0x94 is send a note (0x9_) to channel 5 (0x_4)
    note_off= [0x84, note, 100] #0x84 is stop a note (0x8_) to channel 5 (0x_5)
    out.send_message(note_on)
    time.sleep(0.1)
    out.send_message(note_off)
    time.sleep(0.1)
    