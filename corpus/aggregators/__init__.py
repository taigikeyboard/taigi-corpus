"""Helpers for shared data aggregators that bundle multiple distinct works.

A typical pattern: one upstream project (e.g. ChhoeTaigi) curates many
separately-licensed works into a uniform on-disk format. Each work becomes
its own `sources/<id>/` folder (so license tracking stays clean), but they
share parsing logic that lives here.
"""
