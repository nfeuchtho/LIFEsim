class ErrorBudget:
    """
    Represents an instrumental error contribution that is added on top of a purely
    astrophysical noise term.

    An :class:`ErrorBudget` is evaluated as

    .. math::

        N_{\\mathrm{tot}} = N_{\\mathrm{astro}} \\cdot f_{\\mathrm{mult}}(\\mathrm{args})
                            + f_{\\mathrm{add}}(\\mathrm{args})

    where :math:`f_{\\mathrm{mult}}` and :math:`f_{\\mathrm{add}}` are the multiplicative and
    additive factor functions. By default, the multiplicative factor is ``1`` and the additive
    factor is ``0``, i.e. the budget has no effect and only the astrophysical noise is returned.

    The :class:`AgnosticMissionSimulator` (AMS) holds one :class:`ErrorBudget` instance for each
    of the noise contributions it tracks (stellar leakage, local zodi, exozodi, planet signal and
    planet noise). Each budget is connected to the AMS that uses it via :meth:`connect`.

    Parameters
    ----------
    additive_factor : callable, optional
        Function called as ``additive_factor(args)`` returning the additive noise contribution
        (in the same units as the astrophysical noise it is added to). Defaults to a function
        always returning :attr:`default_additive_factor`.
    multiplicative_factor : callable, optional
        Function called as ``multiplicative_factor(args)`` returning the (dimensionless) factor
        the astrophysical noise is multiplied with. Defaults to a function always returning
        :attr:`default_multiplicative_factor`.
    """

    default_additive_factor = 0
    default_multiplicative_factor = 1

    def __init__(self, additive_factor=lambda args: ErrorBudget.default_additive_factor,
                 multiplicative_factor=lambda args: ErrorBudget.default_multiplicative_factor):
        self.__additive_factor = additive_factor
        self.__multiplicative_factor = multiplicative_factor
        self.ams = None

    def connect(self, ams):
        """
        Connects this error budget to an :class:`AgnosticMissionSimulator` instance.

        Parameters
        ----------
        ams : AgnosticMissionSimulator
            The AMS instance using this error budget. Required before :meth:`update_factors` or
            :meth:`evaluate` can be called.
        """
        self.ams = ams

    def get_factors(self):
        """
        Returns
        -------
        tuple
            The current ``(additive_factor, multiplicative_factor)`` functions.
        """
        return self.__additive_factor, self.__multiplicative_factor

    def update_factors(self, additive_factor=None, multiplicative_factor=None):
        """
        Replaces the additive and/or multiplicative factor functions of this budget.

        Calling this method invalidates the SNR array cached on the connected AMS instance
        (:attr:`AgnosticMissionSimulator.snr_array_current` is set to ``False``), forcing the
        next :meth:`AgnosticMissionSimulator.run` to recompute the SNR for the full catalog.

        Parameters
        ----------
        additive_factor : callable, optional
            New additive factor function. Left unchanged if ``None``.
        multiplicative_factor : callable, optional
            New multiplicative factor function. Left unchanged if ``None``.

        Raises
        ------
        ValueError
            If this budget has not been connected to an AMS instance via :meth:`connect`.
        """
        if self.ams is None:
            raise ValueError('Error budget not initialized - budget not connected to AMS')
        if additive_factor is None and multiplicative_factor is None:
            return
        self.ams.snr_array_current = False
        if additive_factor is not None:
            self.__additive_factor = additive_factor
        if multiplicative_factor is not None:
            self.__multiplicative_factor = multiplicative_factor

    def evaluate(self, astro, *args):
        """
        Applies this error budget to an astrophysical noise contribution.

        Parameters
        ----------
        astro : numpy.ndarray
            The astrophysical noise contribution (e.g. photon flux from stellar leakage, local
            zodi, exozodi, or the planet signal/noise) before the budget is applied.
        *args
            Forwarded as a single tuple to the additive and multiplicative factor functions.
            The arguments passed by the AMS depend on the budget, but typically include the
            habitable-zone center, stellar distance and the wavelength bins.

        Returns
        -------
        numpy.ndarray
            ``astro * multiplicative_factor(args) + additive_factor(args)``

        Raises
        ------
        ValueError
            If this budget has not been connected to an AMS instance via :meth:`connect`.
        """
        if self.ams is None:
            raise ValueError('Error budget not initialized - budget not connected to AMS')
        return astro * self.__multiplicative_factor(args) + self.__additive_factor(args)