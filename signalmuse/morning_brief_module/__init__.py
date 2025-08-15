#!/usr/bin/env python3
"""
Morning Finance Brief Module

Generates comprehensive single-page morning finance briefs using the existing
pipeline and data sources. Follows the specified template format with market
summary, key indicators, headlines, economic data, Fed speak, and earnings.
"""

from .main import MorningBriefGenerator

__all__ = ['MorningBriefGenerator']
