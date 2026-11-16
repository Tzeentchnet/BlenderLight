# Copyright (C) 2026 Kenneth Peters
#
# SPDX-License-Identifier: GPL-3.0-or-later

import struct


class Chunk:
    """Read one word-aligned IFF chunk from a binary stream."""

    def __init__(self, stream):
        self.file = stream
        self.chunkname = stream.read(4)
        if len(self.chunkname) != 4:
            raise EOFError

        size_data = stream.read(4)
        if len(size_data) != 4:
            raise EOFError

        self.chunksize = struct.unpack(">I", size_data)[0]
        self.size_read = 0

    def read(self, size=-1):
        remaining = self.chunksize - self.size_read
        if size < 0 or size > remaining:
            size = remaining

        data = self.file.read(size)
        if len(data) != size:
            raise EOFError("Truncated IFF chunk")

        self.size_read += size
        if self.size_read == self.chunksize and self.chunksize % 2:
            if len(self.file.read(1)) != 1:
                raise EOFError("Truncated IFF chunk padding")
        return data

    def skip(self):
        remaining = self.chunksize - self.size_read
        if remaining:
            self.read(remaining)
