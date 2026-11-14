"""The window.  Model-View-Presenter with a passive view.

``presenter`` decides, ``view`` (a Protocol) says what a window must be able to
show, ``main_window`` is the one Qt implementation.  The presenter never imports
Qt, so its tests need no window.
"""
