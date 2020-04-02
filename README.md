# PyACTUp 1.0.2

### What's new
This version adds spreading activation term, some properties for Imaginal Buffer, and add Importance term


To make everything easier, I didn't change much about old methods, instead I added new ones, such as information first needs to be attended, then cleared from Imaginal buffer, then copied to declarative memory buffer. The chunk in Imaginal buffer should be **spreading** to all chunks in declarative memory buffer. Moreover, when successfully retrieving a memory, model should re-encode this memory. 

The imaginal buffer could set **importance** parameter. By default, it would add a uniformly distributed value from 0-2 to Activation. When importance is set to a high value, it would be added to chunk's Activation and take over the retrieval process.

Both spreading activation and importance term could be found in _activation_history dict.


### Spreading Activation Mechanisms and Equations

The chunks in the buffers provide a context in which to perform a retrieval. Those chunks can spread activation to the chunks in declarative memory based on the contents of their slots. Those slot contents spread an amount of activation based on their relation to the other chunks, which we call their strength of association. This essentially results in increasing the activation of those chunks which are related to the current context. (See ACTR Tutorial Unit 5 for full explanations)

By default, only imaginal buffer serves as source of activation. The $W_{imaginal}$ (Imaginal Activation Parameter) is default to 1. In this version, I only implemented the default case and the equation for the activation $A_i$ of a chunk i including spreading activation could be simplified as:

$$A_i = B_i + \sum_{j} W_j * S_{ji} +  e$$


$W$: imaginal activation parameter (default 1)
$W_j$: $W/n$ (n is the number of slots in current imaginal buffer chunk)

The strength of association, $S_{ji}$, between two chunks j and chunk i is 0 if chunk j is not the value of a slot of chunk i and j and i are not the same chunk. Otherwise, it is set using this equation:

$$ S_{ji} = S – ln(fan_j) $$

$S$: the maximum associative strength (set with the mas parameter, suggested default is 1.6)
$fan_j$: the number of chunks in declarative memory in which j is the value of a slot plus one.


### Emotional Component Mechanisms and Equations

The emotional component implemented in this version is based on Stocco's PTSD model (2020). See full explanation here: 

The effects of emotion on declarative memory is represented by the scalar value I(m) for every memory m created. Every time a new memory is added, its value I(m) is computed and recorded. By default, it adds a uniformly distributed value from 0-2 to $A_i$. When importance parameter is set to a high value, it would be added to chunk's Activation and take over the retrieval process.

The new term I(m) can be broadly interpreted as the degree of importance (needed for survival) of this memory, or specifically can be interpreted as emotional processing. Memories that are associated with different emotions, or to the same emotion but to a different degree, should also differ in importance value. Admittedly, there could be many factors that determine how important one memory is, but here we make a simple approximation, the term I(m) can be interpreted as a single measure capturing the emotional intensity of memory.

The equation of Importance term is expressed as one chunk's posterior probability multiplied by its importance $I_m / I_{¬m}$

$$ A_i = \log( \frac{P(m|Q)} {P(¬m|Q)} *  \frac{I_m} {I_{¬m})} ) = \log( \frac{P(m)} {P(¬m)}) + \sum_q{\log(\frac{P(q|m)}{P(q)})} + \log(I_m) = ...$$

Finally, 
$$ A_i = B_i + S_ +   \sum_{j} W_j*S_{ji} + e + \log(I_m) - \log(\bar{I})$$



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

