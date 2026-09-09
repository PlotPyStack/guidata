:tocdepth: 3

.. automodule:: guidata.dataset.dataitems

Histogram range context
-----------------------

``HistogramRangeItem`` consumes a plain mapping with uniformly spaced histogram
``counts``, a finite ordered ``domain`` pair, and an ``active`` boolean. Optional
``bin_edges`` has one more entry than ``counts``; adjacent edges may coincide after
float rounding. Optional ``y_max`` and ``minimum_width`` must be positive and finite.
Optional ``auto_range`` and ``reset_range`` are finite ordered pairs. Additional
keys are preserved for the caller. An empty mapping represents unavailable context.

The default ``display.presentation`` is ``"range"``. The only specialization is
``"brightness_contrast"``; unknown modes and links to anything other than two
distinct ``FloatItem`` fields fail explicitly when constructing/exporting the form.
See :ref:`examples` for a complete, tested duration-selection example and the live
callback/Cancel contract.
