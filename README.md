# Usage

```python
python midi_parser.py [midi out port] [.mid file name]
python midi_parser.py 0 canyon.mid
```

Current limitation: only works with 1 track (which can have multiple channels) songs (midi file type 0) so far.
Glitches during key signature meta events (dunno why yet)
