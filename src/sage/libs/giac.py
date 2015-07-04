# -*- coding: utf-8 -*-
"""
Wrappers for Giac functions

We provide a python function to compute and convert to sage a groebner basis using the giacpy
module.

AUTHORS:

- Martin Albrecht (2015-07-01): initial version
- Han Frederic (2015-07-01): initial version

EXAMPLES::

    sage: from sage.libs.giac import groebner_basis_libgiac # optional - giacpy
    sage: P = PolynomialRing(QQ, 6, 'x')
    sage: I = sage.rings.ideal.Cyclic(P)
    sage: B = groebner_basis_libgiac(I.gens()) # optional - giacpy, random
    sage: B # optional - giacpy
    Polynomial Sequence with 45 Polynomials in 6 Variables
"""

#*****************************************************************************
#       Copyright (C) 2013 Frederic Han <frederic.han@imj-prg.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************

from sage.structure.proof.all import polynomial as proof_polynomial
from sage.rings.polynomial.multi_polynomial_sequence import PolynomialSequence


#  Remarks for doctests:
#     1) The first time that the c++ library giac is loaded a message appears.
#        This message is version and arch dependant.
#     2) When proba_epsilon is too bad (>1e-6?) setting it to a better value
#        will give an additional message like the following one:
#       Restoring proba epsilon to 1e-6 from 1e-12
#       (it looks like  in internal giac changes this also to not work with a too bad probability)


class GiacSettingsDefaultContext:
    """
    Context preserve libgiac settings.
    """

    def __enter__(self):
        """
        EXAMPLE::

           sage: from sage.libs.giac import GiacSettingsDefaultContext  # optional - giacpy
           sage: from giacpy import giacsettings # optional - giacpy
           sage: giacsettings.proba_epsilon = 1e-16 # optional - giacpy
           sage: with GiacSettingsDefaultContext(): giacsettings.proba_epsilon = 1e-12 # optional - giacpy
           sage: giacsettings.proba_epsilon < 1e-14 # optional - giacpy
           True

        """
        try:
            from giacpy import giacsettings, libgiac
        except ImportError:
            raise ImportError("""One of the optional packages giac or giacpy is missing""")

        self.proba_epsilon = giacsettings.proba_epsilon
        self.threads = giacsettings.threads
        # Change the debug level at the end to not have messages at each modification
        self.debuginfolevel = libgiac('debug_infolevel()')

    def __exit__(self, typ, value, tb):
        """
        EXAMPLE::

           sage: from sage.libs.giac import GiacSettingsDefaultContext  # optional - giacpy
           sage: from giacpy import giacsettings # optional - giacpy
           sage: giacsettings.proba_epsilon = 1e-16 # optional - giacpy
           sage: with GiacSettingsDefaultContext(): giacsettings.proba_epsilon = 1e-30 # optional - giacpy
           sage: giacsettings.proba_epsilon < 1e-20 # optional - giacpy
           False

        """
        try:
            from giacpy import giacsettings, libgiac
        except ImportError:
            raise ImportError("""One of the optional packages giac or giacpy is missing""")

        # Restore the debug level first to not have messages at each modification
        libgiac('debug_infolevel')(self.debuginfolevel)
        # NB: giacsettings.epsilon has a different meaning that giacsettings.proba_epsilon.
        giacsettings.proba_epsilon = self.proba_epsilon
        giacsettings.threads = self.threads

def local_giacsettings(func):
    """
    Decorator to preserve Giac's proba_epsilon and threads settings.

    EXAMPLE::

    """
    from sage.misc.decorators import sage_wraps

    @sage_wraps(func)
    def wrapper(*args, **kwds):
        """
        Execute function in ``GiacSettingsDefaultContext``.
        """
        with GiacSettingsDefaultContext():
            return func(*args, **kwds)

    return wrapper


@local_giacsettings
def groebner_basis_libgiac(gens, proba_epsilon=None, threads=None, prot=False, *args, **kwds):
    """
    Computes a Groebner Basis of an ideal using giacpy. The result is automatically converted to sage.

    INPUT:

    - ``gens`` - an ideal (or a list) of polynomials over a prime field of characteristic 0 or p<2^31

    - ``proba_epsilon`` - (default: None)
       majoration of the probability of a wrong answer when probabilistic algorithms are allowed.

        * if ``proba_epsilon`` is None, the value of ``sage.structure.proof.all.polynomial()`` is taken. If it is false then the global ``giacpy.giacsettings.proba_epsilon`` is used.

        * if ``proba_epsilon`` is 0, probabilistic algorithms are disabled.

    - ``threads`` - (default: None) Maximal number of threads allowed for giac. If None, the global ``giacpy.giacsettings.threads`` is considered.

    - ``prot`` - (default: False) if True print detailled informations

    OUTPUT:

    Polynomial sequence of the reduced Groebner basis.

    EXAMPLES::

        sage: from sage.libs.giac import groebner_basis_libgiac # optional - giacpy
        sage: P = PolynomialRing(GF(previous_prime(2**31)), 6, 'x') # optional - giacpy
        sage: I = sage.rings.ideal.Cyclic(P) # optional - giacpy
        sage: B=groebner_basis_libgiac(I.gens());B # optional - giacpy
        Polynomial Sequence with 45 Polynomials in 6 Variables
        sage: B.is_groebner() # optional - giac
        True

    Computations over QQ can benefit of

    * a probabilistic lifting,

    ::

        sage: P = PolynomialRing(QQ,5, 'x') # optional - giacpy
        sage: I = ideal([P.random_element(3,8) for j in range(5)]) # optional - giacpy
        sage: B1 = groebner_basis_libgiac(I.gens(),1e-16) # optional - giacpy
        Running a probabilistic check for the reconstructed Groebner basis.
        If successfull, error probability is less than 1e-16 ...
        sage: sage.structure.proof.all.polynomial(True) # optional - giacpy
        sage: B2 = groebner_basis_libgiac(I.gens()) # optional - giacpy
        sage: B1==B2 # optional - giacpy
        True

    * multi threaded operations

    ::

        sage: P = PolynomialRing(QQ, 8, 'x') # optional - giacpy
        sage: I=sage.rings.ideal.Cyclic(P) # optional - giacpy
        sage: time B = groebner_basis_libgiac(I.gens(),1e-6,threads=2) # doctest: +SKIP
        Running a probabilistic check for the reconstructed Groebner basis...
        Time: CPU 168.98 s, Wall: 94.13 s

    Get detailled information with ``prot``

    ::

        sage: I=sage.rings.ideal.Katsura(P) # optional - giacpy
        sage: groebner_basis_libgiac(I,prot=True)  # optional - giacpy, random
        9381383 begin computing basis modulo 535718473
        9381501 begin new iteration zmod, number of pairs: 8, base size: 8
        ...end, basis size 74 prime number 1
        G=Vector [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,...
        ...creating reconstruction #0
        ...
        ++++++++basis size 74
        checking pairs for i=0, j=
        checking pairs for i=1, j=2,6,12,17,19,24,29,34,39,42,43,48,56,61,64,69,
        ...
        checking pairs for i=72, j=73,
        checking pairs for i=73, j=
        Number of critical pairs to check 373
        +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++...
        Successfull check of 373 critical pairs
        12380865 end final check
        Polynomial Sequence with 74 Polynomials in 8 Variables


    TESTS::

        sage: from giacpy import libgiac # optional - giacpy
        sage: libgiac("x2:=22; x4:='whywouldyoudothis'") # optional - giacpy
        22,whywouldyoudothis
        sage: groebner_basis_libgiac(I) # optional - giacpy
        Traceback (most recent call last):
        ...
        ValueError: The variables names ['x2', 'x4'] will conflict in giac. Change this or try to purge this value in giac with libgiac.purge('x2')
        sage: libgiac.purge('x2'),libgiac.purge('x4')
        (22, whywouldyoudothis)
        sage: groebner_basis_libgiac(I) # optional - giacpy
        Polynomial Sequence with 74 Polynomials in 8 Variables

    """
    try:
        from giacpy import libgiac, giacsettings
    except ImportError:
        raise ImportError("""One of the optional packages giac or giacpy is missing""")

    try:
        iter(gens)
    except TypeError:
        gens = gens.gens()

    # get the ring from gens
    P = iter(gens).next().parent()
    K = P.base_ring()
    p = K.characteristic()

    # check for name confusions
    blacklist=['i']+[str(j) for j in libgiac.VARS()]
    problematicnames=list(set(P.gens_dict().keys()).intersection(blacklist))
    if(len(problematicnames)>0):
        raise ValueError("The variables names %s will conflict in giac. Change this or try to purge this value in giac with libgiac.purge(\'%s\')"%(problematicnames,problematicnames[0]))

    if K.is_prime_field() and p == 0:
        F = libgiac(gens)
    elif K.is_prime_field() and p < 2**31:
        F = (libgiac(gens) % p)
    else:
        raise NotImplementedError("Only prime fields of cardinal < 2^31 are implemented in Giac for Groebner bases.")

    if P.term_order() != "degrevlex":
        raise NotImplementedError("Only degrevlex term orderings are supported in Giac Groebner bases.")

    # proof or probabilistic reconstruction
    if proba_epsilon is None:
        if proof_polynomial():
            giacsettings.proba_epsilon = 0
        else:
            giacsettings.proba_epsilon = 1e-15
    else:
        giacsettings.proba_epsilon = proba_epsilon

    # prot
    if (prot==True):
        libgiac('debug_infolevel(2)')

    # threads
    if not (threads is None):
        giacsettings.threads=threads

    # compute de groebner basis with giac
    gb_giac = F.gbasis([P.gens()], "revlex")

    return PolynomialSequence(gb_giac, P, immutable=True)
