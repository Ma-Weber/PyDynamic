# -*- coding: utf-8 -*-
"""
The :mod:`PyDynamic.uncertainty.interpolation` module implements methods for
the propagation of uncertainties in the application of standard interpolation methods
as provided by :class:`scipy.interpolate.interp1d`.

This module contains the following function:

* :func:`interp1d_unc`: Interpolate arbitrary time series considering the associated
  uncertainties
"""

from typing import Optional, Tuple

import numpy as np
from scipy.interpolate import interp1d

__all__ = ["interp1d_unc"]


def interp1d_unc(
    t_new: np.ndarray,
    t: np.ndarray,
    y: np.ndarray,
    uy: np.ndarray,
    kind: Optional[str] = "linear",
    bounds_error: Optional[bool] = None,
    fill_value: Optional[bool] = np.nan,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    r"""Interpolate a 1-D function considering the associated uncertainties

    t and y are arrays of values used to approximate some function :math:`f \colon y
    = f(x)`.

    Note that calling :func:`interp1d_unc` with NaNs present in input values
    results in undefined behaviour.

    At least two of each of the original timestamps (or frequencies), values and
    associated uncertainties are required and an equal number of each of these three.

    Parameters
    ----------
        t_new : (M,) array_like
            A 1-D array of real values representing the timestamps (or frequencies) at
            which to evaluate the interpolated values.
        t : (N,) array_like
            A 1-D array of real values representing timestamps (or frequencies) in
            ascending order.
        y : (N,) array_like
            A 1-D array of real values. The length of y must be equal to the length
            of t_new
        uy : (N,) array_like
            A 1-D array of real values representing the uncertainties associated with y.
        kind : str, optional
            Specifies the kind of interpolation for y as a string ('previous',
            'next', 'nearest' or 'linear'). Default is ‘linear’.
        bounds_error : bool, optional
            If True, a ValueError is raised any time interpolation is attempted on a
            value outside of the range of x (where extrapolation is necessary). If
            False, out of bounds values are assigned fill_value. By default, an error
            is raised unless `fill_value="extrapolate"`.
        fill_value : array-like or (array-like, array_like) or “extrapolate”, optional

            - if a ndarray (or float), this value will be used to fill in for
              requested points outside of the data range. If not provided, then the
              default is NaN.
            - If a two-element tuple, then the first element is used as a fill value
              for `t_new < t[0]` and the second element is used for `t_new > t[-1]`.
              Anything that is not a 2-element tuple (e.g., list or ndarray, regardless
              of shape) is taken to be a single array-like argument meant to be used
              for both bounds as `below, above = fill_value, fill_value`.
            - If “extrapolate”, then points outside the data range will be extrapolated.

    Returns
    -------
        t_new : (M,) array_like
            interpolation timestamps
        y_new : (M,) array_like
            interpolated measurement values
        uy_new : (M,) array_like
            interpolated measurement values' uncertainties

    References
    ----------
        * White [White2017]_
    """
    # Check for ascending order of timestamps.
    if not np.all(t[1:] >= t[:-1]):
        raise ValueError("Array of timestamps needs to be in ascending order.")
    # Check for proper dimensions of inputs which are not checked as desired by SciPy.
    if not len(y) == len(uy):
        raise ValueError(
            "Array of associated measurement values' uncertainties must be same length "
            "as array of measurement values."
        )

    if kind in ("previous", "next", "nearest"):
        # Look up values.
        interp_y = interp1d(
            t, y, kind=kind, bounds_error=bounds_error, fill_value=fill_value
        )
        y_new = interp_y(t_new)
        # Look up uncertainties.
        interp_uy = interp1d(
            t, uy, kind=kind, bounds_error=bounds_error, fill_value=fill_value
        )
        uy_new = interp_uy(t_new)
    elif kind == "linear":
        # This following section is taken from scipy.interpolate.interp1d.

        # 2. Find where in the original data, the values to interpolate
        #    would be inserted.
        #    Note: If t_new[n] == t[m], then m is returned by searchsorted.
        t_new_indices = np.searchsorted(t, t_new)

        # 3. Clip x_new_indices so that they are within the range of
        #    self.x indices and at least 1.  Removes mis-interpolation
        #    of x_new[n] = x[0]
        t_new_indices = t_new_indices.clip(1, len(t) - 1).astype(int)

        # 4. Calculate the slope of regions that each x_new value falls in.
        lo = t_new_indices - 1
        hi = t_new_indices

        t_lo = t[lo]
        t_hi = t[hi]
        y_lo = y[lo]
        y_hi = y[hi]

        # Note that the following two expressions rely on the specifics of the
        # broadcasting semantics.
        slope = (y_hi - y_lo) / (t_hi - t_lo)[:, None]

        # 5. Calculate the actual value for each entry in x_new.
        y_new = slope * (t_new - t_lo)[:, None] + y_lo

        # 6. Now we extend the interpolation from scipy.interpolate.interp1d by
        # computing the associated interpolated uncertainties following White, 2017.
        uy_prev_sqr = uy[t_new_indices - 1] ** 2
        uy_next_sqr = uy[t_new_indices] ** 2

        uy_new = np.sqrt(
            (t_new - t_hi) ** 2 * uy_prev_sqr + (t_new - t_lo) ** 2 * uy_next_sqr
        ) / (t_hi - t_lo)
    else:
        raise NotImplementedError(
            "%s is unsupported yet. Let us know, that you need it" % kind
        )

    return t_new, y_new, uy_new
