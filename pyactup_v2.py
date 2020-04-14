# Copyright (c) 2018-2019 Carnegie Mellon University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""PyACTUp is a lightweight Python implementation of a subset of the ACT-R cognitive
architecture’s Declarative Memory, suitable for incorporating into other Python models and
applications. It is inspired by the ACT-UP cognitive modeling toolbox.

Typically PyACTUp is used by creating an experimental framework, or connecting to an
existing experiment, in the Python programming language, using one or more PyACTUp
:class:`Memory` objects. The framework or experiment asks these Memory objects to add
chunks to themselves, describing things learned, and retrieves these chunks or values
derived from them at later times. A chunk, a learned item, contains one or more slots or
attributes, describing what is learned. Retrievals are driven by matching on the values of
these attributes. Each Memory object also has a notion of time, a non-negative, real
number that is advanced as the Memory object is used. Time in PyACTUp is a dimensionless
quantity whose interpretation depends upon the model or system in which PyACTUp is being
used. There are also several parameters controlling these retrievals that can be
configured in a Memory object, and detailed information can be extracted from it
describing the process it uses in making these retrievals. The frameworks or experiments
may be strictly algorithmic, may interact with human subjects, or may be embedded in web
sites.
"""

__version__ = '1.2.0'
'''This version adds spread() for spreading activation term, adds importance term for emotional valence.
Moreover, it allows user to create its own customized spreading activation function by calling 
set_sji_function()'''

import collections
import collections.abc as abc
import math
import numbers
import random
import sys
import numpy as np

from collections import OrderedDict
from warnings import warn

__all__ = ("Memory", "set_similarity_function", "use_actr_similarity", 
           "set_sji_function", "use_actr_sji", "set_matching_source2chunk_function", "use_actr_matching_source2chunk")

DEFAULT_NOISE = 0.25
DEFAULT_DECAY = 0.5
DEFAULT_THRESHOLD = -10.0

MINIMUM_TEMPERATURE = 0.01

TRANSCENDENTAL_CACHE_SIZE = 1000

"""for spreading activation param"""
DEFAULT_W = 1.0 # W
DEFAULT_MAS = 1.6 # maximum associative strength

class Memory(dict):
    """A cognitive entity containing a collection of learned things, its chunks.
    A Memory object also contains a current time, which can be queried as the :attr:`time`
    property.

    The number of distinct chunks a Memory contains can be determined with Python's
    usual :func:`len` function.

    A Memory has several parameters controlling its behavior: :attr:`noise`, :attr:`decay`,
    :attr:`temperature`, :attr:`threshold`, :attr:`mismatch` and :attr:`optimized_learning`.
    All can be queried, and most set, as properties on the Memory object. When creating
    a Memory object their initial values can be supplied as parameters.

    A Memory object can be serialized with
    `pickle <https://docs.python.org/3.6/library/pickle.html>`_, allowing Memory objects
    to be saved to and restored from persistent storage.

    If, when creating a ``Memory`` object, any of *noise*, *decay* or *mismatch* are
    negative, or if *temperature* is less than 0.01, a :exc:`ValueError` is raised.
    """

    def __init__(self,
                 noise=DEFAULT_NOISE,
                 decay=DEFAULT_DECAY,
                 temperature=None,
                 threshold=DEFAULT_THRESHOLD,
                 mismatch=None,
                 optimized_learning=False,
                 W=DEFAULT_W, 
                 mas=DEFAULT_MAS):
        self._temperature_param = 1 # will be reset below, but is needed for noise assignment
        self.noise = noise
        self._decay = None
        self.decay = decay
        self.temperature = temperature
        self.threshold = threshold
        self.mismatch = mismatch
        self.W = W  #for spreading activation param W
        self.mas = mas  #for spreading activation param S
        self._activation_history = None
        self.reset(bool(optimized_learning))

    def __repr__(self):
        return f"<Memory {dict(self.values())}>"

    def __str__(self):
        return f"<Memory {id(self)}>"

    def reset(self, optimized_learning=None):
        """Deletes all the Memory's chunks and resets its time to zero.
        If *optimized_learning* is not None it sets the Memory's :attr:`optimized_learning`
        parameter; otherwise it leaves it unchanged. This Memory's :attr:`noise`,
        :attr:`decay`, :attr:`temperature`, :attr:`threshold` and :attr:`mismatch`
        parameters are left unchanged.
        """
        if optimized_learning and self._decay >= 1:
            raise RuntimeError(f"Optimized learning cannot be enabled if the decay, {self._decay}, is not less than 1")
        self.clear()
        self._time = 0
        if optimized_learning is not None:
            self._optimized_learning = bool(optimized_learning)

    def advance(self, amount=1):
        """Adds the given *amount* to this Memory's time, and returns the new, current time.
        Raises a :exc:`ValueError` if *amount* is negative, or not a real number.
        """
        if amount < 0:
            raise ValueError(f"Time cannot be advanced backward ({amount})")
        self._time += amount
        return self._time

    @property
    def time(self):
        """This Memory's current time.
        Time in PyACTUp is a dimensionless quantity, the interpretation of which is at the
        discretion of the modeler.
        """
        return self._time

    @property
    def noise(self):
        """The amount of noise to add during chunk activation computation.
        This is typically a positive, floating point, number between about 0.1 and 1.5.
        It defaults to 0.25.
        If zero, no noise is added during activation computation.
        If an explicit :attr:`temperature` is not set, the value of noise is also used
        to compute a default temperature for blending computations.
        Attempting to set :attr:`noise` to a negative number raises a :exc:`ValueError`.
        """
        return self._noise

    @noise.setter
    def noise(self, value):
        if value < 0:
            raise ValueError(f"The noise, {value}, must not be negative")
        if self._temperature_param is None:
            t = Memory._validate_temperature(self._temperature_param, value)
            if not t:
                warn(f"Setting noise to {value} will make the temperature too low; setting temperature to 1")
                self.temperature = 1
            else:
                self._temperature = t
        self._noise = value

    @property
    def decay(self):
        """Controls the rate at which activation for previously chunks in memory decay with the passage of time.
        Time in this sense is dimensionless.
        The :attr:`decay` is typically between about 0.1 and 2.0.
        The default value is 0.5. If zero memory does not decay.
        Attempting to set it to a negative number raises a :exc:`ValueError`.
        It must be less one 1 if this memory's :attr:`optimized_learning` parameter is set.
        """
        return self._decay

    @decay.setter
    def decay(self, value):
        if value < 0:
            raise ValueError(f"The decay, {value}, must not be negative")
        if value < 1:
            self._ln_1_mius_d = math.log(1 - value)
        elif self._optimized_learning:
            self._ln_1_mius_d = "illegal value" # ensure error it attempt to use this
            raise ValueError(f"The decay, {value}, must be less than one if optimized_learning is True")
        self._expt_cache = [None]*TRANSCENDENTAL_CACHE_SIZE
        self._ln_cache = [None]*TRANSCENDENTAL_CACHE_SIZE
        self._decay = value

    @property
    def temperature(self):
        """The temperature parameter used for blending values.
        If ``None``, the default, the square root of 2 times the value of
        :attr:`noise` will be used. If the temperature is too close to zero, which
        can also happen if it is ``None`` and the :attr:`noise` is too low, or negative, a
        :exc:`ValueError` is raised.
        """
        return self._temperature_param

    _SQRT_2 = math.sqrt(2)

    @temperature.setter
    def temperature(self, value):
        if value is None or value is False:
            value = None
        else:
            value = float(value)
        t = Memory._validate_temperature(value, self._noise)
        if not t:
            raise ValueError(f"The temperature, {value}, must not be less than {MINIMUM_TEMPERATURE}.")
        self._temperature_param = value
        self._temperature = t

    @staticmethod
    def _validate_temperature(temperature, noise):
        if temperature is not None:
            t = temperature
        else:
            t = Memory._SQRT_2 * noise
        if t < MINIMUM_TEMPERATURE:
            return None
        else:
            return t

    @property
    def threshold(self):
        """The minimum activation value required for a retrieval.
        If ``None`` there is no minimum activation required.
        The default value is ``-10``.
        Attempting to set the ``threshold`` to a value that is neither ``None`` nor a
        real number raises a :exc:`ValueError`.
        """
        if self._threshold == -sys.float_info.max:
            return None
        else:
            return self._threshold

    @threshold.setter
    def threshold(self, value):
        if value is None or value is False:
            self._threshold = -sys.float_info.max
        else:
            self._threshold = float(value)

    @property
    def mismatch(self):
        """The mismatch penalty applied to partially matching values when computing activations.
        If ``None`` no partial matching is done.
        Otherwise any defined similarity functions (see :func:`set_similarity_function`)
        are called as necessary, and
        the resulting values are multiplied by the mismatch penalty and subtracted
        from the activation.
        Attempting to set this parameter to a value other than ``None`` or a real number
        raises a :exc:`ValueError`.
        """
        return self._mismatch

    @mismatch.setter
    def mismatch(self, value):
        if value is None or value is False:
            self._mismatch = None
        elif value < 0:
            raise ValueError(f"The mismatch penalty, {value}, must not be negative")
        else:
            self._mismatch = float(value)

    @property
    def activation_history(self):
        """A :class:`MutableSequence`, typically a :class:`list`,  into which details of the computations underlying PyACTUp operation are appended.
        If ``None``, the default, no such details are collected.
        In addition to activation computations, the resulting retrieval probabilities are
        also collected for blending operations.
        The details collected are presented as dictionaries.
        The ``references`` entries in these dictionaries are sequences of times the
        corresponding chunks were learned, if :attr:`optimizied_learning` is off, and
        otherwise are counts of the number of times they have been learned.

        If PyACTUp is being using in a loop, the details collected will likely become
        voluminous. It is usually best to clear them frequently, such as on each
        iteration.

        Attempting to set :attr:`activation_history` to anything but ``None`` or a
        :class:`MutableSequence` raises a :exc:`ValueError`.

        >>> m = Memory()
        >>> m.learn(color="red", size=3)
        True
        >>> m.advance()
        1
        >>> m.learn(color="red", size=5)
        True
        >>> m.advance()
        2
        >>> m.activation_history = []
        >>> m.blend("size", color="red")
        4.483378114110536
        >>> pprint(m.activation_history)
        [OrderedDict([('name', '0002'),
                      ('creation_time', 0),
                      ('attributes', (('color', 'red'), ('size', 3))),
                      ('references', (0,)),
                      ('base_activation', -0.3465735902799726),
                      ('activation_noise', 0.10712356940903703),
                      ('activation', -0.23945002087093556),
                      ('retrieval_probability', 0.25831094294473195)]),
         OrderedDict([('name', '0003'),
                      ('creation_time', 1),
                      ('attributes', (('color', 'red'), ('size', 5))),
                      ('references', (1,)),
                      ('base_activation', 0.0),
                      ('activation_noise', 0.13346608542692032),
                      ('activation', 0.13346608542692032),
                      ('retrieval_probability', 0.741689057055268)])]
        """
        return self._activation_history

    @activation_history.setter
    def activation_history(self, value):
        if value is None or value is False:
            self._activation_history = None
        elif isinstance(value, abc.MutableSequence):
            self._activation_history = value
        else:
            raise ValueError(
                f"A value assigned to activation_history must be a MutableSequence ({value}).")

    @property
    def optimized_learning(self):

        """A boolean indicating whether or not this Memory is configured to use optimized learning.
        Cannot be set directly, but can be changed when calling :meth:`reset`.
        """
        return self._optimized_learning

    _use_actr_similarity = False
    _minimum_similarity = 0
    _maximum_similarity = 1
    _similarity_functions = {}

    def _similarity(self, x, y, attribute):
        if x == y:
            return 0
        fn = self._similarity_functions.get(attribute)
        if fn:
            result = fn(x, y)
        else:
            result = None
        if result is not None:
            if result < Memory._minimum_similarity:
                warn(f"similarity value is less than the minimum allowed, {Memory._minimum_similarity}, so that minimum value is being used instead")
                result = Memory._minimum_similarity
            elif result > Memory._maximum_similarity:
                warn(f"similarity value is greater than the maximum allowed, {Memory._maximum_similarity}, so that maximum value is being used instead")
                result = Memory._maximum_similarity
            if not Memory._use_actr_similarity:
                result -= 1
            return result
        else:
            return -1

    @property
    def W(self):
        """The W, default to be 1"""
        return self._W

    @W.setter
    def W(self, value):
        if value is None or value is False:
            self._W = None
        elif value < 0:
            raise ValueError(f"The W, {value}, must not be negative")
        else:
            self._W = float(value)
            
    @property
    def mas(self):
        """The maximum association strength S, default to be 1.6"""
        return self._mas

    @mas.setter
    def mas(self, value):
        if value is None or value is False:
            self._mas = None
        elif value < 0:
            raise ValueError(f"The maximum association strength, {value}, must not be negative")
        else:
            self._mas = float(value)

    """Modified: add a parameter importance"""
    def learn(self, importance=0, **kwargs):
        """Adds, or reinforces, a chunk in this Memory with the attributes specified by *kwargs*.
        The attributes, or slots, of a chunk are described using Python keyword arguments.
        The attribute names must conform to the usual Python variable name syntax, and may
        not be Python keywords. Their values must be :class:`Hashable`.

        Returns ``True`` if a new chunk has been created, and ``False`` if instead an
        already existing chunk has been re-experienced and thus reinforced.

        Note that time must be advanced by the programmer with :meth:`advance` following
        any calls to ``learn`` before calling :meth:`retrieve` or :meth:`blend`. Otherwise
        the chunk learned at this time would have infinite activation.

        Raises a :exc:`TypeError` if an attempt is made to learn an attribute value that
        is not :class:`Hashable`.

        >>> m = Memory()
        >>> m.learn(color="red", size=4)
        True
        >>> m.learn(color="blue", size=4)
        True
        >>> m.learn(color="red", size=4)
        False
        >>> m.advance()
        1
        >>> m.retrieve(color="red")
        <Chunk 0000 {'color': 'red', 'size': 4}>
        """
        if not kwargs:
            raise ValueError(f"No attributes to learn")
        created = False
        signature = tuple(sorted(kwargs.items()))
        chunk = self.get(signature)
        if not chunk:
            chunk = Chunk(self, kwargs)
            self[signature] = chunk
            created = True
        if self._optimized_learning:
            chunk._references += 1
        else:
            chunk._references.append(self._time)
        # set importance
        chunk.importance=importance 
        return created

    def forget(self, when, **kwargs):
        """Undoes the operation of a previous call to :meth:`learn`.

        .. warning::
            Normally this method should not be used. It does not correspond to a
            biologically plausible process, and is only provided for esoteric purposes.

        The *kwargs* should be those supplied fro the :meth:`learn` operation to be
        undone, and *when* should be the time that was current when the operation was
        performed. Returns ``True`` if it successfully undoes such an operation, and
        ``False`` otherwise.
        """
        if not kwargs:
            raise ValueError(f"No attributes to forget")
        signature = tuple(sorted(kwargs.items()))
        chunk = self.get(signature)
        if not chunk:
            return False
        if self._optimized_learning:
            chunk._references -= 1
        else:
            try:
                chunk._references.remove(when)
            except ValueError:
                return False
        if not chunk._references:
            del self[signature]
        return True
    
    def retrieve(self, partial=False, **kwargs):
        """Returns the chunk matching the *kwargs* that has the highest activation greater than this Memory's :attr:`threshold`.
        If there is no such matching chunk returns ``None``.
        Normally only retrieves chunks exactly matching the *kwargs*; if *partial* is
        ``True`` it also retrieves those only approximately matching, using similarity
        (see :func:`set_similarity_function`) and :attr:`mismatch` to determine closeness
        of match.

        The returned chunk is a dictionary-like object, and its attributes can be
        extracted with Python's usual subscript notation.

        >>> m = Memory()
        >>> m.learn(widget="thromdibulator", color="red", size=2)
        True
        >>> m.advance()
        1
        >>> m.learn(widget="snackleizer", color="blue", size=1)
        True
        >>> m.advance()
        2
        >>> m.retrieve(color="blue")["widget"]
        'snackleizer'
        """
        # self._spreading(kwargs)       
        if partial:
            return self._partial_match(kwargs)
        else:
            return self._exact_match(kwargs)

    def _exact_match(self, conditions):
        # Returns a single chunk matching the given slots and values, that has the
        # highest activation greater than the threshold parameter. If there are no
        # such chunks returns None.
        best_chunk = None
        best_activation = self._threshold
        for chunk in self.values():
            if not conditions.keys() <= chunk.keys():
                continue
            for key, value in conditions.items():
                if chunk[key] != value:
                    break
            else:   # this matches the for, NOT the if
                a = chunk._activation()
                if a >= best_activation:
                    best_chunk = chunk
                    best_activation = a
        return best_chunk

    def _make_noise(self):
        if not self._noise:
            return 0
        p = random.uniform(sys.float_info.epsilon, 1 - sys.float_info.epsilon)
        return self._noise * math.log((1.0 - p) / p)
    
    ###New function for spreading activation
    def spread(self, auto_clear=False, **kwargs):
        """ This new method will reformat kwargs to sources, spread activation 
        to chunks in m (self). 
        By default, the spreading activation value is None. Everytime spread() is called, 
        new value will be added to the chunk cumulatively. It could be set to None by calling clear_spread().
        By defualt, PyACTUP uses fan function to calculate sji. The equation used is: 
            spreading activation = sum(wj * sji)
                wj = W/n;
                sji = S-ln(fan);
        Any defined sji functions (see :func:`set_sji_function`) are called as necessary
        """
        if not kwargs:
            raise ValueError(f"No attributes to spread")
        # automatically clear spreading activation value
        if auto_clear:
            self.clear_spread()
            
        # iterate through all chunks
        spreading_activation_vector = self._compute_spreading_activation_vec(kwargs)
        if spreading_activation_vector is None or len(spreading_activation_vector)!=len(self.values()):
            raise RuntimeError("Failed to spread.")
        index_chunk = 0
        for chunk in self.values():
            chunk.spreading_activation=spreading_activation_vector[index_chunk]
            index_chunk=index_chunk+1
    
    """HELPER Functions"""
    def _actr_matching_source2chunk(self, conditions):
        """compare conditions(M) to chunks(N) in m.
        Spliting chunk into n sources, and compare sources to chunk
        Return an NxM matrix
        Each row represents a chunk
        Each col represents a source
        Each cell is T/F indicating whether source's value is matching
        """
        result=[]
        ### iterate through all slot-value pair in conditions
        for cslot, cvalue in conditions.items():
            ### iterate through all slot-value pair in m
            temp=[]
            for chunk in self.values():
                temp.append(cvalue in chunk.values()) #check if value occurs in chunk's values, regardless of slot names
            result.append(temp)
        """[[True  True]
            [True  False]
            [False True]]
        """
        return np.array(result)
    
    def _actr_sji(self, match_matrix):
        """Use default fan() function to compute sji
        sji = S - log(fan)
        """
        # use default function _fan()
        fan=np.sum(match_matrix, axis=1)+1 # return a vector of fan number, size=num of 
        
        # compute sji = S - ln(fan)
        ## mas: maximum associative strength
        sji = self.mas-np.log(fan)
        return sji
    
    _use_actr_matching_source2chunk = True
    _matching_source2chunk_function = None

    def _matching_source2chunk(self, conditions):
        """decide whether to use default _matching_source2chunk functon or customized function"""
        if not self._use_actr_matching_source2chunk:
            try:
                result = self._matching_source2chunk_function(conditions)
                return result
            except:
                warn(f"new _matching_source2chunk func has not been correctly defined. Using default")
                pass
        result=self._actr_matching_source2chunk(conditions)
        return result
    
    _use_actr_sji = True
    #_minimum_sji = 0
    #_maximum_sji = 1
    _sji_function = None

    def _sji(self, match_matrix):
        """decide whether to use default sji or customized sji function"""
        if not self._use_actr_sji:
            try:
                result = self._sji_function(match_matrix)
                return result
            except:
                warn(f"sji func has not been correctly defined. Using default sji fn")
                pass
        result=self._actr_sji(match_matrix)
        # print('in _sji (defualt): ', result)
        return result
        
    def _compute_spreading_activation_vec(self, conditions):
        """Calculate the spreading activation for chunks in m
        conditions ->(spreading to) m
        Return a vector of spreading activation"""
        # get match_matrix
        match_matrix=self._matching_source2chunk(conditions)
        
        # compute wj = W/n
        wj=self.W * np.ones(len(conditions.items()))/len(conditions.items())
        
        # cumpute sji = S - ln(fan)
        sji =self._sji(match_matrix)
        
        # compute sji for each chunk
        result=np.sum(wj*sji*match_matrix.T, axis=1)
        #print("res: ", result)
        return result
    """HELPER Functions Finished"""
    
    def clear_spread(self):
        """undo spreading by assigning None to chunk.spreading_activation xs"""
        index_chunk = 0
        for chunk in self.values():
            chunk.spreading_activation=None
            index_chunk=index_chunk+1 
            

    class _Activations(abc.Iterable):

        def __init__(self, memory, conditions):
            self._memory = memory
            self._conditions = conditions

        def __iter__(self):
            self._chunks = self._memory.values().__iter__()
            return self

        def __next__(self):
            while True:
                chunk = self._chunks.__next__()             # pass on up the Stop Iteration
                if self._conditions.keys() <= chunk.keys(): # subset
                    if self._memory._mismatch is not None:
                        activation = chunk._activation(True)
                        mismatch = self._memory._mismatch * sum(self._memory._similarity(c, chunk[s], s)
                                                                for s, c in self._conditions.items())
                        total = activation + mismatch
                        if self._memory._activation_history is not None:
                            history = self._memory._activation_history[-1]
                            history["mismatch"] = mismatch
                            history["activation"] = total
                        return (chunk, total)
                    else:
                        if not all(chunk[a] == v for a, v in self._conditions.items()):
                            continue
                        activation = chunk._activation(True)
                        if self._memory._activation_history is not None:
                            self._memory._activation_history[-1]["activation"] = activation
                        return (chunk, activation)

    def _activations(self, conditions):
        return self._Activations(self, conditions)

    def _partial_match(self, conditions):
        best_chunk = None
        best_activation = self._threshold
        for chunk, activation in self._activations(conditions):
            if activation >= self._threshold:
                best_chunk = chunk
                best_activation = activation
        return best_chunk

    def blend(self, outcome_attribute, **kwargs):
        """Returns a blended value for the given attribute of those chunks matching *kwargs*, and which contains *outcome_attribute*.
        Returns ``None`` if there are no matching chunks that contains
        *outcome_attribute*. If any matching chunk has a value of *outcome_attribute*
        value that is not a real number a :exc:`TypeError` is raised.

        >>> m = Memory()
        >>> m.learn(color="red", size=2)
        True
        >>> m.advance()
        1
        >>> m.learn(color="blue", size=30)
        True
        >>> m.advance()
        2
        >>> m.learn(color="red", size=1)
        True
        >>> m.advance()
        3
        >>> m.blend("size", color="red")
        1.1548387620911693

        """
        weights = 0.0
        weighted_outcomes = 0.0
        if self._activation_history is not None:
            chunk_weights = []
        for chunk, activation in self._activations(kwargs):
            if outcome_attribute not in chunk:
                continue
            weight = math.exp(activation / self._temperature)
            if self._activation_history is not None:
                chunk_weights.append((self._activation_history[-1], weight))
            weights += weight
            weighted_outcomes += weight * chunk[outcome_attribute]
        if self._activation_history is not None:
            for history, w in chunk_weights:
                try:
                    history["retrieval_probability"] = w / weights
                except ZeroDivisionError:
                    history["retrieval_probability"] = None
        try:
            return weighted_outcomes / weights
        except ZeroDivisionError:
            return None
        
@property
def use_actr_similarity():
    """Whether to use "natural" similarity values, or traditional ACT-R ones.
    PyACTUp normally uses a "natural" representation of similarities, where two values
    being completely similar, identical, has a value of one; and being completely
    dissimilar has a value of zero; with various other degrees of similarity being
    positive, real numbers less than one. Traditionally ACT-R instead uses a range of
    similarities with the most dissimilar being a negative number, usually -1, and
    completely similar being zero.
    """
    return Memory.use_actr_similarity

@use_actr_similarity.setter
def use_actr_similarity(value):
    if value:
        Memory._minimum_similarity = -1
        Memory._maximum_similarity =  0
    else:
        Memory._minimum_similarity =  0
        Memory._maximum_similarity =  1
    Memory._use_actr_similarity = bool(value)

def set_similarity_function(function, *slots):
    """Assigns a similarity function to be used when comparing attribute values with the given names.
    The function should take two arguments, and return a real number between 0 and 1,
    inclusive.
    The function should be commutative; that is, if called with the same arguments
    in the reverse order, it should return the same value.
    It should also be stateless, always returning the same values if passed
    the same arguments.
    No error is raised if either of these constraints is violated, but the results
    will, in most cases, be meaningless if they are.

    >>> def f(x, y):
    ...     if y < x:
    ...         return f(y, x)
    ...     return 1 - (y - x) / y
    >>> set_similarity_function(f, "length", "width")
    """
    for s in slots:
        Memory._similarity_functions[s] = function

@property
def use_actr_sji():
    return Memory.use_actr_sji
    
@use_actr_sji.setter
def use_actr_sji(value):
    Memory._use_actr_sji = bool(value)

def set_sji_function(function):
    """Assigns a sji function to be used when calculate sji.
    The function should take two arguments Memory obejct and macth_matrix,
    match_matrxi is a matrix of T/F, which comapres source and chunk in DM
    see _matching_source2chunk()
    For example, if DM contains 3 chunks, source contains 2 slots, 
    macth_matrix is like 
            [[True  True]
            [True  False]
            [False True]]
    and return a vector of sji, N length (N=number of memory items in DM)
    The function should be commutative; that is, if called with the same arguments
    in the reverse order, it should return the same value.
    It should also be stateless, always returning the same values if passed
    the same arguments.
    >>> def f(m, match_matrix):
    ...     fan=np.sum(match_matrix, axis=1)+1
    ...     sji=Memory.mas - np.log(fan * 100)
    ...     return sji
    >>> set_sji_function(f)
    """
    Memory._sji_function = function


@property
def use_actr_matching_source2chunk():
    return Memory.use_actr_matching_source2chunk

@use_actr_matching_source2chunk.setter
def use_actr_matching_source2chunk(value):
    Memory._use_actr_matching_source2chunk = bool(value)

def set_matching_source2chunk_function(function):
    Memory._matching_source2chunk_function = function


class Chunk(dict):

    __slots__ = ["_name", "_memory", "_creation", "_references",
                 "_base_activation_time", "_base_activation",
                 "_spreading_activation", "_importance"] # added new properties

    _name_counter = 0;

    def __init__(self, memory, content):
        self._name = f"{Chunk._name_counter:04d}"
        Chunk._name_counter += 1
        self._memory = memory
        self.update(content)
        self._creation = memory._time
        self._references = 0 if memory._optimized_learning else []
        self._base_activation_time = None
        self._base_activation = None
        self._spreading_activation = None
        self._importance = 0

    def __repr__(self):
        return "<Chunk {} {}>".format(self._name, dict(self))

    def __str__(self):
        return self._name

    def _activation(self, for_partial=False):
        # Does not include the mismatch penalty component, that's handled by the caller.
        base = self._get_base_activation()
        noise = self._memory._make_noise()
        spreading_activation = self._spreading_activation if self._spreading_activation else 0 # m spreads to chunk(self)
        importance = self._importance
        result = base + spreading_activation + importance + noise 
        if self._memory._activation_history is not None:
            history = OrderedDict(name=self._name,
                                  creation_time=self._creation,
                                  attributes=tuple(self.items()),
                                  references=(self._references
                                              if self._memory.optimized_learning
                                              else tuple(self._references)),
                                  base_activation=base,
                                  activation_noise=noise,
                                  spreading_activation=self._spreading_activation,
                                  importance=importance)
            if not for_partial:
                history["activation"] = result
            self._memory._activation_history.append(history)
        return result

    # Note that memoizing expt and ln doesn't make much difference, but it does speed
    # things up a tiny bit, most noticeably under PyPy
    def _cached_expt(self, base):
        try:
            result = self._memory._expt_cache[base]
            if result is None:
                result = math.pow(base, -self._memory._decay)
                self._memory._expt_cache[base] = result
            return result
        except (IndexError, TypeError):
            return math.pow(base, -self._memory._decay)

    def _cached_ln(self, arg):
        try:
            result = self._memory._ln_cache[arg]
            if result is None:
                result = math.log(arg)
                self._memory._ln_cache[arg] = result
            return result
        except (IndexError, TypeError):
            return math.log(arg)

    def _get_base_activation(self):
        if self._base_activation_time != self._memory.time:
            try:
                if self._memory._optimized_learning:
                    self._base_activation = (self._cached_ln(self._references)
                                             - self._memory._ln_1_mius_d
                                             - self._memory._decay * self._cached_ln(self._memory._time - self._creation))
                else:
                    base = sum(self._cached_expt(self._memory._time - ref)
                               for ref in self._references)
                    self._base_activation = math.log(base)
            except ValueError as e:
                if self._memory._time <= self._creation:
                    raise RuntimeError("Can't compute activation of a chunk at or before the time it was created")
                else:
                    raise e
            self._base_activation_time = self._memory.time
        return self._base_activation
    
    @property
    def spreading_activation(self):
        return self._spreading_activation

    @spreading_activation.setter
    def spreading_activation(self, value):
        """By default, spreading_activation is 0
        Chunk's spreading_activation is added when spreading() is called"""
        if value and self._spreading_activation:
            self._spreading_activation+=value
        else:
            self._spreading_activation=value
    
    @property
    def importance(self):
        return self._importance

    @importance.setter
    def importance(self, value):
        """By default, importance is uniformally distributed 0-2. Otherwise, it could be set to any value"""
        if value is None or value is False:
            p = random.uniform(sys.float_info.epsilon, 2 - sys.float_info.epsilon)
            self._importance = math.log(p)
        else:
            self._importance = float(value)

# Local variables:
# fill-column: 90
# End:
