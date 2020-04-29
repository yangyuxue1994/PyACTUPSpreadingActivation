# PyACTUp 1.0.2
### Required Packages and Python Version
Consistent with PyACTUP 1.0.1, this version requires Python 3.6.9+

In addition, it requires numpy packages 1.18.1+ 

### What's new
This version adds spreading activation term, importance term.  

You could set **importance** parameter. By default, it would add a uniformly distributed value from 0-2 to Activation. When importance is set to a high value, it would be added to chunk's Activation and take over the retrieval process. (Details about the definition and theory behind **impotance** could be found here: https://github.com/UWCCDL/PTSD) 

The function to calculate sji function could be customized. Both spreading activation and importance term could be checked in _activation_history.

### Spreading Activation Mechanisms and Equations

The chunks in the buffers provide a context in which to perform a retrieval. Those chunks can spread activation to the chunks in declarative memory based on the contents of their slots. Those slot contents spread an amount of activation based on their relation to the other chunks, which we call their strength of association. This essentially results in increasing the activation of those chunks which are related to the current context. (See ACTR Tutorial Unit 5 for full explanations)

By default, only imaginal buffer serves as source of activation. The W (Imaginal Activation Parameter) is default to 1. You could change use the customized sji function. (See test5)

Below is the function used for default sji calculation:

![alt text](https://lh3.googleusercontent.com/ABVsgSQ0KneRZUL9PDXuYPKroQsutzg_5qMQ_NZEQfBX-wdly-aMd3v99ZBqjSu7LTL9ShwJMSscKsPLmjssHG9oLZO7z0-ToO70sXyL5Bs0bj-Xv67rY_ZsjxFPBzNClG6q-AG7 "Eq.1")


- W: (default 1)
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

![alt text](https://lh3.googleusercontent.com/Bq7Ul8PxrDp4IRENfJIxCoUWRHlt0oetDGJFfaK2Dmd6_8TH3y2X-Vr6UnaBcVY5MU4Ku3GtmwWeXRm5qC5ZP6rOrAVdUFM-jM4XX2Zp "Importance Term")

The equation of Importance term is expressed as one chunk's posterior probability multiplied by its importance 
                        I(m) / I(¬m)

Finally, 

![alt_text](https://lh5.googleusercontent.com/1eAtAkKebiYqVc70u9Z8lpildhFlSkw-CH8KJ4AG00H-OUKeASHCl9AXgtvJZ5WG4mzLNE0BAayDW2GYzstM7meFRhXc8AY8Bt-8TwU)

### Spread() Example
      m.learn(color='red', size=1)
      m.advance()
      
      m.spread(color='red')
      m.retrieve(color='red', size=1)

### imporrtance Example
      m.learn(color='red', size=1, importance=100)
      m.advance()
### What's NEXT?
