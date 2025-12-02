#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ******************************************************************************
# ZYNTHIAN PROJECT: Zynthian Control Device Driver
#
# Zynthian Control Device Driver for "AKAI Professional MPK249"
#
# Copyright (C) 2025 Nathan Foster <code@forbesfoster.com>
#
# ******************************************************************************
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the LICENSE.txt file.
#
# ******************************************************************************

import logging
from time import monotonic

# Zynthian specific modules
from zyngine.ctrldev.zynthian_ctrldev_base import zynthian_ctrldev_zynmixer
from zyncoder.zyncore import lib_zyncore
from zynlibs.zynseq import zynseq

# ------------------------------------------------------------------------------
# AKAI MPK249 MIDI controller
#
# The APK249 is a hardware controller with 8 channels strips, each containing:
#   Fader (CC 12..19)
#   Pan (CC 22..29)
#
# This driver interfaces an MPK249 with the first 7 chains and main chain. Currently implemented are:
#   Fader
#   Pan
# ------------------------------------------------------------------------------

class zynthian_ctrldev_akai_mpk_249(zynthian_ctrldev_zynmixer):

    dev_ids = ["MPK249 IN 1", "MPK249 IN 2", "MPK249 IN 3", "MPK249 IN 4"]
    driver_name = "Akai MPK249"
    driver_description = "Interface for Akai MPK249"
    autoload_flag = False

    # Function to initialise class
    def __init__(self, state_manager, idev_in, idev_out=None):
        super().__init__(state_manager, idev_in, idev_out)
        self.midi_chan = 0  # Base channel for MIDI messages. +1 for +8 offset, +2 for +16 offset.
        self.chan2chain = {}
        self.last_store = monotonic()

    def set_param(self, cc, val, midi_chan):
        # Assign Faders F1 - F7 (Bank 1) to Faders on Zynthian Chains 1-7
        if  cc > 11 and cc < 19:
            self.zynmixer.set_level(cc - 12, val / 127.0, False)
            return False
        # Assign Fader F8 (Bank 1) to Main Zynthian Volume
        if cc == 19:
            # Main fader
            self.zynmixer.set_level(255, val / 127.0, False)
        # Assign Knobs K1 - K7 (Bank 1) to Balance on Zynthian Chains 1-7
        if  cc > 21 and cc < 29:
            self.zynmixer.set_balance(cc - 22, (val - 64) / 64, False)
            return False
        # Assign Knob K8 (Bank 1) to Main Zynthian Balance
        if cc == 29:
            # Main Knob
            self.zynmixer.set_balance(255, (val - 64) / 64, False)
        return True

    def midi_event(self, ev):
        evtype = (ev[0] >> 4) & 0x0F
        midi_chan = ev[0] & 0xF
        if midi_chan > 1:
            return False
        if evtype == 0xb:
            cc = ev[1] & 0x7F
            val = ev[2] & 0x7F

            return self.set_param(cc, val, midi_chan)
        return False

    def update_mixer_strip(self, chan, symbol, value):
        return
        if chan in self.chan2chain:
            match symbol:
                case "level":
                    lib_zyncore.dev_send_ccontrol_change(self.idev_out, self.midi_chan + int(chan / 8), 12 + chan % 8 , int(value * 127))
                case "balance":
                    lib_zyncore.dev_send_ccontrol_change(self.idev_out, self.midi_chan + int(chan / 8), 22 + chan % 8 , int(value * 64 + 64))

    def refresh(self):
        self.chan2chain = {}
        for chain_id, chain in self.chain_manager.chains.items():
            if chain.mixer_chan is not None and chain.mixer_chan < 16:
                self.chan2chain[chain.mixer_chan] = chain_id

# ------------------------------------------------------------------------------
'''
Presently unused code
        case 117:
            self._stop_all_sounds()
            return True
        case 118:
            self._libseq.togglePlayState(self._zynseq.bank, self._selected_seq)
            return True
        case 119:
            self._state_manager.send_cuia("TOGGLE_RECORD")
            return True

'''
