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
    out.open_port(0)
    try:
        with open(file, 'rb') as ff:
        
            data_buffer_len = len(bytearray(ff.read()))
            ff.seek(0)
            
            print("MIDI file name: ",file)
            print(ff.read(4))
            print("size ",int.from_bytes(ff.read(4)))
            print("format type ",int.from_bytes(ff.read(2)))
            print("number of tracks ",int.from_bytes(ff.read(2)))
            tdiv = ff.read(2)
            if (tdiv[0] & 0x80) == 0x00:
                print("time division is ticks per beat, ticks=",tdiv," int=",int.from_bytes(tdiv))
            elif (tdiv[0] & 0x80) == 0x80:
                print("time division is frames per s= ",int.from_bytes(tdiv[1])) 
            track_hdr = ff.read(4)
            print("NEW TRACK",track_hdr)
            tracklength = ff.read(4)
            print("length ",int.from_bytes(tracklength))
            
            i=21
            ff.seek(22)
            while i < data_buffer_len:
                #print(i)
                # time delta portion
                finalValue = 0
                nValue = 0
                nByte = 0
                
                nValue = ff.read(1)[0]
                #print("nValue ",nValue)
                i+=1
                
                if nValue & 0x80:
                    nValue &= 0x7F
                    while True:
                        nByte = ff.read(1)[0]
                        #print("nByte ",nByte)
                        i+=1
                        finalValue = (nValue << 7) | (nByte & 0x7F)
                        if not nByte & 0x80:
                            break
                    time.sleep(nValue/500)
                
                status_byte = ff.read(1)[0]
                #print("eventByte ",status_byte)
                i+=1                
                # MIDI Meta-event portion
                if (status_byte & 0xFF) == 0xFF:
                    meta_byte = int.from_bytes(ff.read(1))
                    print("Status Byte",status_byte,"Meta-Event",meta_byte)
                    i+=1
                    if meta_byte == MetaSequence:
                        data1=ff.read(1)
                        data2=ff.read(1)
                        #notemsg = [status_byte, meta_byte, data1, data2] 
                        #print ("message is ",notemsg)
                        #out.send_message(notemsg)
                        print("  Sequence Number: ", data1, data2)
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
                        data1=ff.read(1)
                        data2=ff.read(1)
                        #notemsg = [status_byte, meta_byte, data1, data2] 
                        #out.send_message(notemsg)
                        print("MIDI Channel Prefix: ", data1, data2)
                        i+=2	
                    elif meta_byte == MetaEndOfTrack:
                        data1=ff.read(1)
                        #notemsg = [status_byte, meta_byte, data1] 
                        #out.send_message(notemsg)
                        i+=1
                        print("*** END OF TRACK")
                    elif meta_byte == MetaSetTempo:
                        data1=ff.read(1)[0]
                        data2=ff.read(1)[0]
                        data3=ff.read(1)[0]
                        data4=ff.read(1)[0]
                        #notemsg = [status_byte, meta_byte, data1, data2,data3,data4] 
                        #out.send_message(notemsg)
                        print("  Tempo: ", data1, data2, data3, data4)
                        i+=4	
                    elif meta_byte == MetaSMPTEOffset:
                        data1=ff.read(1)[0]
                        data2=ff.read(1)[0]
                        data3=ff.read(1)[0]
                        data4=ff.read(1)[0]
                        data5=ff.read(1)[0]
                        data6=ff.read(1)[0]
                        #notemsg = [0xF0, meta_byte, data1, data2,data3,data4,data5,data6] 
                        #print ("SMTP message is ",notemsg)
                        #out.send_message(notemsg)
                        print("  SMPTE Offset: ", data1, data2, data3, data4, data5, data6)
                        i+=6	
                    elif meta_byte == MetaTimeSignature:
                        data1=ff.read(1)[0]
                        data2=ff.read(1)[0]
                        data3=ff.read(1)[0]
                        data4=ff.read(1)[0]
                        data5=ff.read(1)[0]
                        #notemsg = [status_byte, meta_byte, data1, data2,data3,data4,data5] 
                        #out.send_message(notemsg)
                        print("  Key Signature: ", data1, data2, data3, data4, data5)
                        i+=5	
                    elif meta_byte == MetaKeySignature:
                        data1=ff.read(1)[0]
                        data2=ff.read(1)[0]
                        data3=ff.read(1)[0]
                        #notemsg = [status_byte, meta_byte, data1, data2,data3] 
                        #out.send_message(notemsg)
                        print("  Key Signature: ", data1, data2, data3)
                        i+=3
                    elif meta_byte == MetaSequencerSpecific:
                        pass	
                    else:
                        print("Unrecognised MetaEvent: ")
                        
        # Program change   0xC_
        # Channel Pressure 0xD_
                elif 0xC0 <= status_byte <= 0xDF:
                    data1 = ff.read(1)[0]
                    notemsg = [status_byte,data1]
                    out.send_message(notemsg)
                    i+=1
        # Note off   0x8_
        # Note on    0x9_
                elif (0x80 <= status_byte <= 0x9F):
                    data1 = ff.read(1)[0]
                    data2 = ff.read(1)[0]
                    if status_byte==0x90 and data2 == 0:
                        status_byte=0x80
                    notemsg = [status_byte, data1, data2] 
                    print("note on ch ",status_byte & 0x0F, data1, data2)
                    out.send_message(notemsg)
                    i+=2
        # Polyphonic Key Pressure  0xA_ (Aftertouch)
        # Control Change           0xB_
        # (0xC_ and 0xD_ have been taken care of earlier already)
        # Pitch Bend               0xE_
                elif (0xA0 <= status_byte <= 0xBF) or (0xE0 <= status_byte <= 0xEF):
                    data1 = ff.read(1)[0]
                    data2 = ff.read(1)[0]
                    notemsg = [status_byte, data1, data2] 
                    out.send_message(notemsg)
                    i+=2
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except Exception as e:
        print(f"Error reading the file: {e}")
    
# --- Main entry point ---

parse(argv[1],argv[2])

       
