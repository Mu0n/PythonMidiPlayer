#
#	Copyright (c) 2024 Michaël Juneau, anybitfeverdreams@gmail.com
#
#	Permission is hereby granted, free of charge, to any person obtaining a copy
#	of this software and associated documentation files (the "Software"), to deal
#	in the Software without restriction, including without limitation the rights
#	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#	copies of the Software, and to permit persons to whom the Software is
#	furnished to do so, subject to the following conditions:
#
#	The above copyright notice and this permission notice shall be included in
#	all copies or substantial portions of the Software.
#
#	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#	SOFTWARE.
#
#     midi_parser.py
#   Simple python program that opens a MIDI 1.0 .mid file, parses
#   its midi command and sets them up in a multitrack structure, ready to be played
#   back using an opened midi port. If you're unsure of which port you should use,
#   a list of available ports will be printed out upon executing
#
#     Usage:
#   python midi_parser.py <portNum> <.mid filename>
#

import time
import rtmidi
from sys import argv

# --- MIDI spec hard coded values ---
# good reference is here: https://www.music.mcgill.ca/~ich/classes/mumt306/StandardMIDIfileformat.html#BM1_1
# from the midi.org itself: https://midi.org/summary-of-midi-1-0-messages

MetaEndOfTrack     = 0x2F
MetaSequence       = 0x00
MetaText           = 0x01
MetaCopyright      = 0x02
MetaTrackName      = 0x03
MetaInstrumentName = 0x04
MetaLyrics         = 0x05
MetaMarker         = 0x06
MetaCuePoint       = 0x07
MetaChannelPrefix  = 0x20
MetaEndOfTrack     = 0x2F
MetaSetTempo       = 0x51
MetaSMPTEOffset    = 0x54
MetaTimeSignature  = 0x58
MetaKeySignature   = 0x59
MetaSequencerSpecific = 0x7F

class aMIDIEvent:
    deltaToGo = 0
    statusB = 0x00
    dataB = None #list can't be initialized here
    
class trackEvents:
    eventList = None #list can't be initialized here


    

# --- Opening a port to MIDI out ---
# using the rtmidi package to fetch and open a MIDI out port.
# note: you may need to use another port number than mine depending on your system
# I expect Windows' typical port 0 is the GS Synth driver that's used to approximate midi sounds, 
# used by Windows Media Player when playing .mid files
def read_until_mthd(file):
    i=0 #index
    buffer = b"" # Initialize an empty buffer to store the encountered bytes
    try:
        with open(file, 'rb') as ff:
            raw_data = bytearray(ff.read())
            ff.seek(0)
            data_buffer_len = len(bytearray(ff.read()))
            ff.seek(0)
            
            print("MIDI file name: ",file)
            print("-------------")
            # Define the target sequence of bytes: MThd
            target_bytes = b"MThd"
            # Iterate through the input byte data
            for byte in raw_data:
                # Append the current byte to the buffer
                buffer += bytes([byte])
                i+=1
                # Check if the buffer contains the target sequence
                if buffer.endswith(target_bytes):
                    # Found the target sequence, break the loop
                    break
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except Exception as e:
        print(f"Error reading the file: {e}")
    return raw_data[(i-4):]
    
  
    
# --- Parsing a midi file specified by the 1st argument upon execution

def parse(buffer):
    bpm = 0 #beat per minute
    ppq = 0 #ppq read from header
    tick = 0 #millisecond per tick
    
    trackcount = 0 #number of tracks detected
    finished_tracks = 0 #number of tracks that have been read so fa
    i = 0 #main array parsing index
            
    print("MIDI file header")
    print("-------------")
    hdrTag = buffer[i:(i+4)]
    i+=4
    print(hdrTag)
    size = buffer[i:(i+4)]
    print("size ",int.from_bytes(size))
   
    i+=4
    print("format type ",int.from_bytes(buffer[i:(i+2)]))
    i+=2
    trackcount = int.from_bytes(buffer[i:(i+2)])
    i+=2
    print("number of tracks ",trackcount)
    
    
    tdiv = buffer[i:(i+2)]
    i+=2
    
    if (tdiv[0] & 0x80) == 0x00:
        print("time division is ticks per beat, ticks=",int.from_bytes(tdiv))
        ppq = int.from_bytes(tdiv)
    elif (tdiv[0] & 0x80) == 0x80:
        print("time division is frames per s= ",int.from_bytes(tdiv[1])) 
    
    finished_tracks = 0
    tracklength = 1 #value of 1 by default, will get changed once a track header is read
    cementedStartI = i
    totalLen = len(buffer)
    while i < totalLen:
        print("i=",i)
        finished_tracks+=1
        track_hdr = buffer[i:(i+4)]
        i+=4
        print("-------------")
        print("Track header for track #", finished_tracks)
        print("-------------")
        print(track_hdr)

        tracklength = int.from_bytes(buffer[i:(i+4)])
        i+=4
        print("length: ",tracklength)
        print("-------------")
    
        last_cmd = 0x00
        while i < tracklength:
            nValue = 0
            nValue2 = 0
            nValue3 = 0
            nValue4 = 0
        
            status_byte = 0 #status byte for reading MIDI commands
            dataCombo = [] #data byte(s) read 
            
            recognizedCmdForPlayback = 0 #set to 1 if it must be put in the player
            forWhichChannel = 0x00
            
            #time delta reading. Assume it's at most 4 bytes (7 bits each, 
            #total max of 28 sign. bits with 4 extra padded 0's
            nValue = int.from_bytes(buffer[i:(i+1)])
            i+=1
            if nValue & 0x0080:
                nValue &= 0x007F # toss out the MSB
                nValue <<= 7     # shift it 7 positions to make room for the next 7bits
                nValue2 = int.from_bytes(buffer[i:(i+1)])
                i+=1
                if nValue2 & 0x0080:
                    nValue2 &= 0x007F # toss out the MSB
                    nValue2 <<= 7     # shift it 7 positions to make room for the next 7bits
                    nValue <<= 7      # shift it 7 positions to make room for the next 7bits
                    nValue3 = int.from_bytes(buffer[i:(i+1)])
                    i+=1
                    if nValue3 & 0x0080:
                        nValue3 &= 0x007F # toss out the MSB
                        nValue3 <<= 7     # shift it 7 positions to make room for the next 7bits
                        nValue2 <<= 7     # shift it 7 positions to make room for the next 7bits
                        nValue <<= 7      # shift it 7 positions to make room for the next 7bits
                        nValue4 = int.from_bytes(buffer[i:(i+1)])
                        i+=1
            timeDelta = nValue | nValue2 | nValue3 | nValue4
            
            
            #status byte / MIDI message reading
            status_byte = int.from_bytes(buffer[i:(i+1)])
            i+=1 
            
            #First, check for run-on commands that don't repeat the status_byte
            if (status_byte < 0x80):
                status_byte = last_cmd
                i-=1 #go back 1 spot so it can read the data properly
                
            #Second, deal with MIDI meta-event commands that start with 0xFF.
            if (status_byte & 0xFF) == 0xFF:
                meta_byte = int.from_bytes(buffer[i:(i+1)])
                i+=1
                if meta_byte == MetaSequence:
                    data1=buffer[i:(i+1)]
                    i+=1
                    data2=buffer[i:(i+1)]
                    i+=1
                    notemsg = [status_byte, meta_byte, data1, data2] 
                elif meta_byte == MetaText:
                    tLen = int.from_bytes(buffer[i:(i+1)])
                    i+=1
                    text = buffer[i:(i+tLen)]
                    i+=tLen
                    print("  ",text)                        
                elif meta_byte == MetaCopyright:
                    tLen = int.from_bytes(buffer[i:(i+1)])
                    i+=1
                    text = buffer[i:(i+tLen)]
                    i+=tLen
                    print("  ",text)  
                elif meta_byte == MetaTrackName:
                    tLen = int.from_bytes(buffer[i:(i+1)])
                    i+=1
                    text = buffer[i:(i+tLen)]
                    i+=tLen
                    print("  ",text)  	
                elif meta_byte == MetaInstrumentName:
                    tLen = int.from_bytes(buffer[i:(i+1)])
                    i+=1
                    text = buffer[i:(i+tLen)]
                    i+=tLen
                    print("  ",text)  	
                elif meta_byte == MetaLyrics:
                    tLen = int.from_bytes(buffer[i:(i+1)])
                    i+=1
                    text = buffer[i:(i+tLen)]
                    i+=tLen
                    print("  ",text)  	
                elif meta_byte == MetaMarker:
                    tLen = int.from_bytes(buffer[i:(i+1)])
                    i+=1
                    text = buffer[i:(i+tLen)]
                    i+=tLen
                    print("  ",text)  	
                elif meta_byte == MetaCuePoint:
                    tLen = int.from_bytes(buffer[i:(i+1)])
                    i+=1
                    text = buffer[i:(i+tLen)]
                    i+=tLen
                    print("  ",text)  	
                elif meta_byte == MetaChannelPrefix:
                    data1=buffer[i:(i+1)]
                    i+=1
                    data2=buffer[i:(i+1)]
                    i+=1	
                elif meta_byte == MetaEndOfTrack:
                    data1=buffer[i:(i+1)]
                    i+=1
                    print("--------------------------------------------------- END OF TRACK")
                    pass
                elif meta_byte == MetaSetTempo:
                    data1=buffer[i:(i+1)]
                    i+=1
                    data2=int.from_bytes(buffer[i:(i+1)])
                    i+=1
                    data3=int.from_bytes(buffer[i:(i+1)])
                    i+=1
                    data4=int.from_bytes(buffer[i:(i+1)])
                    i+=1
                    bpm = 6e7/(data2<<16 | data3 <<8 | data4)
                    tick = 60./(bpm*ppq)
                elif meta_byte == MetaSMPTEOffset:
                    data1=buffer[i:(i+1)]
                    i+=1
                    data2=buffer[i:(i+1)]
                    i+=1
                    data3=buffer[i:(i+1)]
                    i+=1
                    data4=buffer[i:(i+1)]
                    i+=1
                    data5=buffer[i:(i+1)]
                    i+=1
                    data6=buffer[i:(i+1)]
                    i+=1
                elif meta_byte == MetaTimeSignature:
                    data1=buffer[i:(i+1)]
                    i+=1
                    data2=buffer[i:(i+1)]
                    i+=1
                    data3=buffer[i:(i+1)]
                    i+=1
                    data4=buffer[i:(i+1)]
                    i+=1
                    data5=buffer[i:(i+1)]
                    i+=1	
                elif meta_byte == MetaKeySignature:
                    data1=buffer[i:(i+1)]
                    i+=1
                    data2=buffer[i:(i+1)]
                    i+=1
                    data3=buffer[i:(i+1)]
                    i+=1
                elif meta_byte == MetaSequencerSpecific:
                    pass	
                else:
                    print("Unrecognised MetaEvent: ")
                    
    #Third, deal with regular MIDI commands
    
    #MIDI commands with only 1 data byte
    # Program change   0xC_
    # Channel Pressure 0xD_
            elif 0xC0 <= status_byte <= 0xDF:
                dataCombo.append(buffer[i:(i+1)])
                i+=1
                recognizedCmdForPlayback=1
                forWhichChannel = status_byte & 0x0F
                
                         
    #MIDI commands with 2 data bytes
    # Note off   0x8_
    # Note on    0x9_
    # Polyphonic Key Pressure  0xA_ (Aftertouch)
    # Control Change           0xB_
    # (0xC_ and 0xD_ have been taken care of earlier already)
    # Pitch Bend               0xE_
            elif (0x80 <= status_byte <= 0xBF) or (0xE0 <= status_byte <= 0xEF):
                
   
                dataCombo.append(buffer[i:(i+1)])
                i+=1
                dataCombo.append(buffer[i:(i+1)])
                i+=1

                if (0x90 <= status_byte <= 0x9F) and dataCombo[1] == 0: 
                    status_byte&=0x8F #note on with velocity 0 is a note off
                    
                recognizedCmdForPlayback=1
                forWhichChannel = status_byte & 0x0F
                
            else:
                print("------unrecognized event ", status_byte)
            last_cmd = status_byte
        
            if(recognizedCmdForPlayback):
                
                if(timeDelta > 0):
                    time.sleep(tick*timeDelta)
                finalMsg = bytearray([status_byte])
                for item in dataCombo:
                    finalMsg.extend(item)
                out.send_message(finalMsg)
                '''
                newEvent = aMIDIEvent()
                newEvent.deltaToGo = tick*timeDelta
                newEvent.statusB = status_byte
                newEvent.dataB = []
                newEvent.dataB += dataCombo
                track1Events.eventList.append(newEvent)
                '''
            


def play():
    while True:
        a=0
        #check the lowest time delta of all the tracks
        #wait for that time and send the command
        #lower every pending event delta by that amount
        #if the event was an end track, then set boolean ended to true for that track
    
# --- Main entry point ---

out = rtmidi.MidiOut()
ports = out.get_ports()
print(ports)
print("port chosen: ",argv[1]) #which MIDI port is to be used (0,1,...)
out.open_port(int(argv[1]))
buf = read_until_mthd(argv[2]) #open midi file and get to MThd, ignore previous bytes; 2nd arg: .mid file name
parse(buf)  #parse the song and put it in a structure
#playback the song

#track1Events = trackEvents()
#track1Events.eventList = [] #init here
#print("track1 events ", len(track1Events.eventList))