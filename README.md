# PyACTUp 1.0.3 

### What's new
This version adds spreading activation term, some properties for Imaginal Buffer, and add Importance term


To make everything easier, I didn't change much about old methods, instead I added new ones, such as information first needs to be attended, then cleared from Imaginal buffer, then copied to declarative memory buffer. The chunk in Imaginal buffer should be **spreading** to all chunks in declarative memory buffer. Moreover, when successfully retrieving a memory, model should re-encode this memory. 

The imaginal buffer could set **importance** parameter. By default, it would add a uniformly distributed value from 0-2 to Activation. When importance is set to a high value, it would be added to chunk's Activation and take over the retrieval process.

Both spreading activation and importance term could be found in _activation_history dict.



### Code Example
ATTEND: In Imaginal buffer, learn() means attending to the info (color='red', size=1)

    import pyactup_v2 as pya
    imaginal_buffer=pya.Memory() 
	
	imaginal_buffer.learn(color='red', size=1)

ENCODE: In declarative buffer, encode() means storing information to the LTM

    dm_buffer.encode(imaginal_buffer._curr_chunk(0))
    dm_buffer.advance(2)
    imaginal_buffer.reset() 
    

RETRIEVE: first attending to the info, and then trying to retrieve. If succeed, re-encode, otherwise, do nothing 

    imaginal_buffer.learn(color='red', size=1)
    result = dm_buffer.retrieve(imaginal_buffer._curr_chunk(0))

### What's NEXT?
- Haven't implement partial match. TODO
- Add emotional term - DONE

