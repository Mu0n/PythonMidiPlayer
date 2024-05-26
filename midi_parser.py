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


# --- Opening a port to MIDI out ---
# using the rtmidi package to fetch and open a MIDI out port.
# note: you may need to use another port number than mine depending on your system
# I expect Windows' typical port 0 is the GS Synth driver that's used to approximate midi sounds, 
# used by Windows Media Player when playing .mid files



# --- Parsing a midi file specified by the 1st argument upon execution

def parse(portNum,file):
    out = rtmidi.MidiOut()
    ports = out.get_ports()
    print(ports)
    print("port chosen: ",portNum)
    out.open_port(int(portNum))
    
    try:
        with open(file, 'rb') as ff:
            bpm = 0 #beat per minute
            ppq = 0 #ppq read from header
            tick = 0 #millisecond per tick
            
            status_byte = 0 #status byte for reading MIDI commands
            finished_tracks = 0 #number of tracks that have been read so far
            
            data_buffer_len = len(bytearray(ff.read()))
            ff.seek(0)
            
            print("MIDI file name: ",file)
            print("-------------")
            print("MIDI file header")
            print("-------------")
            print(ff.read(4))
            print("size ",int.from_bytes(ff.read(4)))
            print("format type ",int.from_bytes(ff.read(2)))
            print("number of tracks ",int.from_bytes(ff.read(2)))
            tdiv = ff.read(2)
            if (tdiv[0] & 0x80) == 0x00:
                print("time division is ticks per beat, ticks=",tdiv," int=",int.from_bytes(tdiv))
                ppq = int.from_bytes(tdiv)
            elif (tdiv[0] & 0x80) == 0x80:
                print("time division is frames per s= ",int.from_bytes(tdiv[1])) 
            track_hdr = ff.read(4)
            print("-------------")
            print("Track header")
            print("-------------")
            print(track_hdr)
            tracklength = ff.read(4)
            print("length: ",int.from_bytes(tracklength))
            print("-------------")
            
            i=21
            ff.seek(22)
            
            last_cmd = 0x00
            while i < data_buffer_len:
                nValue = 0
                nValue2 = 0
                nValue3 = 0
                nValue4 = 0
               
                #time delta reading. Assume it's at most 4 bytes (7 bits each, 
                #total max of 28 sign. bits with 4 extra padded 0's
                nValue = int.from_bytes(ff.read(1))
                i+=1
                if nValue & 0x0080:
                    nValue &= 0x007F # toss out the MSB
                    nValue <<= 7     # shift it 7 positions to make room for the next 7bits
                    nValue2 = int.from_bytes(ff.read(1))
                    i+=1
                    if nValue2 & 0x0080:
                        nValue2 &= 0x007F # toss out the MSB
                        nValue2 <<= 7     # shift it 7 positions to make room for the next 7bits
                        nValue <<= 7      # shift it 7 positions to make room for the next 7bits
                        nValue3 = int.from_bytes(ff.read(1))
                        i+=1
                        if nValue3 & 0x0080:
                            nValue3 &= 0x007F # toss out the MSB
                            nValue3 <<= 7     # shift it 7 positions to make room for the next 7bits
                            nValue2 <<= 7     # shift it 7 positions to make room for the next 7bits
                            nValue <<= 7      # shift it 7 positions to make room for the next 7bits
                            nValue4 = int.from_bytes(ff.read(1))
                            i+=1
                timeDelta = nValue | nValue2 | nValue3 | nValue4
                
                
                #status byte / MIDI message reading
                status_byte = ff.read(1)[0]
                i+=1 
                
                #First, check for run-on commands that don't repeat the status_byte
                if ( status_byte & 0x80) == 0x00:
                    status_byte = last_cmd
                    i-=1
                    ff.seek(i) #go back 1 spot so it can read the data properly
                    
                #Second, deal with MIDI meta-event commands that start with 0xFF.
                if (status_byte & 0xFF) == 0xFF:
                    meta_byte = int.from_bytes(ff.read(1))
                    i+=1
                    if meta_byte == MetaSequence:
                        data1=ff.read(1)[0]
                        data2=ff.read(1)[0]
                        notemsg = [status_byte, meta_byte, data1, data2] 
                        i+=2
                    elif meta_byte == MetaText:
                        tLen = int.from_bytes(ff.read(1))
                        i+=1
                        text = ff.read(tLen)
                        i+=tLen
                        print("  ",text)                        
                    elif meta_byte == MetaCopyright:
                        tLen = int.from_bytes(ff.read(1))
                        i+=1
                        text = ff.read(tLen)
                        i+=tLen
                        print("  ",text)  
                    elif meta_byte == MetaTrackName:
                        tLen = int.from_bytes(ff.read(1))
                        i+=1
                        text = ff.read(tLen)
                        i+=tLen
                        print("  ",text)  	
                    elif meta_byte == MetaInstrumentName:
                        tLen = int.from_bytes(ff.read(1))
                        i+=1
                        text = ff.read(tLen)
                        i+=tLen
                        print("  ",text)  	
                    elif meta_byte == MetaLyrics:
                        tLen = int.from_bytes(ff.read(1))
                        i+=1
                        text = ff.read(tLen)
                        i+=tLen
                        print("  ",text)  	
                    elif meta_byte == MetaMarker:
                        tLen = int.from_bytes(ff.read(1))
                        i+=1
                        text = ff.read(tLen)
                        i+=tLen
                        print("  ",text)  	
                    elif meta_byte == MetaCuePoint:
                        tLen = int.from_bytes(ff.read(1))
                        i+=1
                        text = ff.read(tLen)
                        i+=tLen
                        print("  ",text)  	
                    elif meta_byte == MetaChannelPrefix:
                        data1=ff.read(1)[0]
                        data2=ff.read(1)[0]
                        i+=2	
                    elif meta_byte == MetaEndOfTrack:
                        data1=ff.read(1)[0]
                        i+=1
                        print("--------------------------------------------------- END OF TRACK")
                    elif meta_byte == MetaSetTempo:
                        data1=ff.read(1)[0]
                        data2=ff.read(1)[0]
                        data3=ff.read(1)[0]
                        data4=ff.read(1)[0]
                        bpm = 6e7/(data2<<16 | data3 <<8 | data4)
                        tick = 60./(bpm*ppq)
                        i+=4	
                    elif meta_byte == MetaSMPTEOffset:
                        data1=ff.read(1)[0]
                        data2=ff.read(1)[0]
                        data3=ff.read(1)[0]
                        data4=ff.read(1)[0]
                        data5=ff.read(1)[0]
                        data6=ff.read(1)[0]
                        i+=6	
                    elif meta_byte == MetaTimeSignature:
                        data1=ff.read(1)[0]
                        data2=ff.read(1)[0]
                        data3=ff.read(1)[0]
                        data4=ff.read(1)[0]
                        data5=ff.read(1)[0]
                        i+=5	
                    elif meta_byte == MetaKeySignature:
                        data1=ff.read(1)[0]
                        data2=ff.read(1)[0]
                        data3=ff.read(1)[0]
                        i+=3
                    elif meta_byte == MetaSequencerSpecific:
                        pass	
                    else:
                        print("Unrecognised MetaEvent: ")
                        
        #Third, deal with regular MIDI commands
        
        #MIDI commands with only 1 data byte
        # Program change   0xC_
        # Channel Pressure 0xD_
                elif 0xC0 <= status_byte <= 0xDF:
                    data1 = ff.read(1)[0]
                    notemsg = [status_byte,data1]
                    if(timeDelta > 0):
                        time.sleep(tick*timeDelta)
                    out.send_message(notemsg)
                    i+=1
                    
        #MIDI commands for note on and note off with 2 data bytes
        # Note off   0x8_
        # Note on    0x9_
                elif (0x80 <= status_byte <= 0x9F):
                    data1 = ff.read(1)[0]
                    data2 = ff.read(1)[0]
                    if (0x90 <= status_byte <= 0x9F) and data2 == 0: 
                        status_byte&=0x8F #note on with velocity 0 is a note off
                    notemsg = [status_byte, data1, data2] 
                    if(timeDelta > 0):
                        time.sleep(tick*timeDelta)
                    out.send_message(notemsg)
                    i+=2
                    
        #MIDI commands with 2 data bytes
        # Polyphonic Key Pressure  0xA_ (Aftertouch)
        # Control Change           0xB_
        # (0xC_ and 0xD_ have been taken care of earlier already)
        # Pitch Bend               0xE_
                elif (0xA0 <= status_byte <= 0xBF) or (0xE0 <= status_byte <= 0xEF):
                    data1 = ff.read(1)[0]
                    data2 = ff.read(1)[0]
                    notemsg = [status_byte, data1, data2] 
                    if(timeDelta > 0):
                        time.sleep(tick*timeDelta)
                    out.send_message(notemsg)
                    i+=2
                else:
                    print("------unrecognized event ", status_byte)
                last_cmd = status_byte
                    
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except Exception as e:
        print(f"Error reading the file: {e}")
    
# --- Main entry point ---
parse(argv[1],argv[2])   #1st arg: which MIDI port is to be used (0,1,...); 2nd arg: .mid file name
