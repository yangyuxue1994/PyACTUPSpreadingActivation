# PyACTUp 1.0.2
### Required Packages and Python Version
Consistent with PyACTUP 1.0.1, this version requires Python 3.6.9+
<<<<<<< HEAD
=======

>>>>>>> 09af13dac4596c4252affc71e6f34fda46ed75c1
In addition, it requires numpy packages 1.18.1+ 

### What's new
This version adds spreading activation term, importance term, some properties for Imaginal Buffer


To make everything easier, I didn't change much about old methods, instead I added new ones, such as information first needs to be attended, then cleared from Imaginal buffer, then copied to declarative memory buffer. The chunk in Imaginal buffer should be **spreading** to all chunks in declarative memory buffer. Moreover, when successfully retrieving a memory, model should re-encode this memory. 

The imaginal buffer could set **importance** parameter. By default, it would add a uniformly distributed value from 0-2 to Activation. When importance is set to a high value, it would be added to chunk's Activation and take over the retrieval process. (Details about the definition and theory behind **impotance** could be found here: https://github.com/UWCCDL/PTSD) 
<<<<<<< HEAD

Both spreading activation and importance term could be checked in _activation_history.
=======

Both spreading activation and importance term could be checked in _activation_history.


### Spreading Activation Mechanisms and Equations

The chunks in the buffers provide a context in which to perform a retrieval. Those chunks can spread activation to the chunks in declarative memory based on the contents of their slots. Those slot contents spread an amount of activation based on their relation to the other chunks, which we call their strength of association. This essentially results in increasing the activation of those chunks which are related to the current context. (See ACTR Tutorial Unit 5 for full explanations)

By default, only imaginal buffer serves as source of activation. The W_imaginal (Imaginal Activation Parameter) is default to 1. In this version, I only implemented the default case and the equation for the activation Ai of a chunk i including spreading activation could be simplified as:


![alt text](https://lh3.googleusercontent.com/ABVsgSQ0KneRZUL9PDXuYPKroQsutzg_5qMQ_NZEQfBX-wdly-aMd3v99ZBqjSu7LTL9ShwJMSscKsPLmjssHG9oLZO7z0-ToO70sXyL5Bs0bj-Xv67rY_ZsjxFPBzNClG6q-AG7 "Eq.1")


- W: imaginal activation parameter (default 1)
- Wj: W/n (n is the number of slots in current imaginal buffer chunk)

The strength of association, Sji, between two chunks j and chunk i is 0 if chunk j is not the value of a slot of chunk i and j and i are not the same chunk. Otherwise, it is set using this equation:


![alt text](https://lh6.googleusercontent.com/QWeGhjzUmkKDXFr0Xq_84IZ6umbdSCa8bzsPbtYaMsBF98ZSbYji7F8YDIHcQpWPT2l_SaSCLhaoaBYeCKjSco3J6EsRfGE0PByHGIQvJjiF7cnP3YiAlnNfSO489xGLuZF6pNMJ)

- S: the maximum associative strength (set with the mas parameter, suggested default is 1.6)
- fan(j): the number of chunks in declarative memory in which j is the value of a slot plus one.

![alt text](https://lh3.googleusercontent.com/d9JBhD-RpoTNefBu7gnRPL0D3mqhc_MtXXUGTjMulCcUvSIMoQlhU6S-kiN4B8Z4mF_rNGTwrelV4UICcqoe-1LoHnCEwPgQRdeDXIe3GET65aUAvNi6-tv7VTH5qRedVQozWedS "Spreading Activation Example")

>>>>>>> 09af13dac4596c4252affc71e6f34fda46ed75c1


### Spreading Activation Mechanisms and Equations

The chunks in the buffers provide a context in which to perform a retrieval. Those chunks can spread activation to the chunks in declarative memory based on the contents of their slots. Those slot contents spread an amount of activation based on their relation to the other chunks, which we call their strength of association. This essentially results in increasing the activation of those chunks which are related to the current context. (See ACTR Tutorial Unit 5 for full explanations)

By default, only imaginal buffer serves as source of activation. The $W_{imaginal}$ (Imaginal Activation Parameter) is default to 1. In this version, I only implemented the default case and the equation for the activation $A_i$ of a chunk i including spreading activation could be simplified as:


![alt text](https://lh3.googleusercontent.com/ABVsgSQ0KneRZUL9PDXuYPKroQsutzg_5qMQ_NZEQfBX-wdly-aMd3v99ZBqjSu7LTL9ShwJMSscKsPLmjssHG9oLZO7z0-ToO70sXyL5Bs0bj-Xv67rY_ZsjxFPBzNClG6q-AG7 "Eq.1")


- W: imaginal activation parameter (default 1)
- Wj: W/n (n is the number of slots in current imaginal buffer chunk)

The strength of association, Sji, between two chunks j and chunk i is 0 if chunk j is not the value of a slot of chunk i and j and i are not the same chunk. Otherwise, it is set using this equation:


![alt text](https://lh6.googleusercontent.com/QWeGhjzUmkKDXFr0Xq_84IZ6umbdSCa8bzsPbtYaMsBF98ZSbYji7F8YDIHcQpWPT2l_SaSCLhaoaBYeCKjSco3J6EsRfGE0PByHGIQvJjiF7cnP3YiAlnNfSO489xGLuZF6pNMJ)

- S: the maximum associative strength (set with the mas parameter, suggested default is 1.6)
- fan(j): the number of chunks in declarative memory in which j is the value of a slot plus one.

![alt text](https://lh3.googleusercontent.com/d9JBhD-RpoTNefBu7gnRPL0D3mqhc_MtXXUGTjMulCcUvSIMoQlhU6S-kiN4B8Z4mF_rNGTwrelV4UICcqoe-1LoHnCEwPgQRdeDXIe3GET65aUAvNi6-tv7VTH5qRedVQozWedS "Spreading Activation Example")




### Emotional Component Mechanisms and Equations

The emotional component implemented in this version is based on Stocco's PTSD model (2020). See full explanation here: https://github.com/UWCCDL/PTSD

The effects of emotion on declarative memory is represented by the scalar value I(m) for every memory m created. Every time a new memory is added, its value I(m) is computed and recorded. By default, it adds a uniformly distributed value from 0-2 to Ai. When importance parameter is set to a high value, it would be added to chunk's Activation and take over the retrieval process.

The new term I(m) can be broadly interpreted as the degree of importance (needed for survival) of this memory, or specifically can be interpreted as emotional processing. Memories that are associated with different emotions, or to the same emotion but to a different degree, should also differ in importance value. Admittedly, there could be many factors that determine how important one memory is, but here we make a simple approximation, the term I(m) can be interpreted as a single measure capturing the emotional intensity of memory.

![alt text](https://lh3.googleusercontent.com/PgI6peikKtHoKhjGSehkbs5xND0XdGzqFV4BHdPvLt_awR-WgwYjvcAghR1zh-BhKYwfqzyzKaFCPfwdYx-IuUkd9jyznaGzHqwak1ll "Importance Term")

The equation of Importance term is expressed as one chunk's posterior probability multiplied by its importance 
                        I(m) / I(¬m)

![alt_text](https://lh3.googleusercontent.com/cbBNm4HAtUPOg6txP2Z_izOf-3AgYypYN7y8DFoVHJhaJeSc1OJRsNDdYgjTnUB4x9CILa1fIYSxmbbzFsjbv2f-L0ArhsWUj9L6FsKm)

Finally, 

![alt_text](https://lh3.googleusercontent.com/4YDvx-hpHNoMz4LD05al9FmHpmZsrkY_GwAorIKrS2NNFhqfvvlHtAtkE57J5B9Z_5QeaoPhb3sYC_bsFTDS30C50SewXft2ULhRRV1klPEaYclTgdY3Iif0BHX9UR7spRATJ2Z5)

### Emotional Component Mechanisms and Equations

The emotional component implemented in this version is based on Stocco's PTSD model (2020). See full explanation here: https://github.com/UWCCDL/PTSD

The effects of emotion on declarative memory is represented by the scalar value I(m) for every memory m created. Every time a new memory is added, its value I(m) is computed and recorded. By default, it adds a uniformly distributed value from 0-2 to Ai. When importance parameter is set to a high value, it would be added to chunk's Activation and take over the retrieval process.

The new term I(m) can be broadly interpreted as the degree of importance (needed for survival) of this memory, or specifically can be interpreted as emotional processing. Memories that are associated with different emotions, or to the same emotion but to a different degree, should also differ in importance value. Admittedly, there could be many factors that determine how important one memory is, but here we make a simple approximation, the term I(m) can be interpreted as a single measure capturing the emotional intensity of memory.

![alt text](https://lh3.googleusercontent.com/PgI6peikKtHoKhjGSehkbs5xND0XdGzqFV4BHdPvLt_awR-WgwYjvcAghR1zh-BhKYwfqzyzKaFCPfwdYx-IuUkd9jyznaGzHqwak1ll "Importance Term")

The equation of Importance term is expressed as one chunk's posterior probability multiplied by its importance 
                        I(m) / I(¬m)

![alt_text](https://lh3.googleusercontent.com/JOhd2plJV7SKOAgNHGhTTKrRnJq1v9iCB4CRWfF-yEZ5kyqo23E6aLLBCDJmKOZgFNRZ-GR7SiFHPv_MvuOn7QMqeyCccuELKqxtPFit)

Finally, 

![alt_text](https://lh5.googleusercontent.com/Eia8Vt1LQEY4jeGSeUYd6ppac8zx2YsUhwcbwgGzpI4xUpzRO8r9wtXj4U8DsVCJ2EBh2IiZ0ODRVcrEQXxea_-M7Wto5E_9hKCY9YU)

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
    
    ### set mismatch param = 100 for partial matching
    dm_buffer.mismatch=100
    imaginal_buffer.learn(color='red', size=1)
    ichunk=imaginal_buffer._curr_chunk(0)
    
    result = dm_buffer.retrieve(ichunk, partial=True)
    dm_buffer.advance(2)

### What's NEXT?
- Add Emotinal term - DONE
- Implement partial match - DONE
<<<<<<< HEAD
=======
- Time. dm_buffer and imaginal buffer each has a clock. Need to fix this issue. 
>>>>>>> 09af13dac4596c4252affc71e6f34fda46ed75c1

