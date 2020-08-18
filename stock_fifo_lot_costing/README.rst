Stock FIFO Lot Costing
======================

This module changes the FIFO costing methods so that if a lot/serial is
specified in a move, the cost of that lot/serial is used.  Without this module,
the cost of the first in lot/serial would be used, regardless of which
lot/serial is being moved.

In order to get the correct cost of a lot, we add field remaining_qty to the
stock.move.line model.
