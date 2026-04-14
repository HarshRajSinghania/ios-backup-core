"""
Protobuf wire-format string extraction.

Extracted from notes.py:NoteExtractor._extract_pb_strings().
Renamed to extract_protobuf_strings() as a module-level function.
Logic is unchanged — battle-tested against Notes gzip+proto blobs.
"""


def extract_protobuf_strings(data: bytes, depth: int = 0) -> list[str]:
    """Walk a protobuf blob and collect all UTF-8 string field values.

    Recursively follows length-delimited (wire type 2) fields so nested
    messages are also searched. Non-UTF-8 chunks are treated as nested
    protobuf messages and recursed into.

    Args:
        data:  Raw protobuf bytes (already decompressed if gzip-wrapped).
        depth: Recursion guard — stops at depth 8 to avoid runaway recursion.

    Returns:
        List of decoded UTF-8 strings containing meaningful alphabetic content
        (at least 3 alpha characters after stripping whitespace).
    """
    if depth > 8:
        return []

    strings: list[str] = []
    pos = 0
    data_len = len(data)

    while pos < data_len:
        # Decode tag varint
        tag = 0
        shift = 0
        valid = False
        while pos < data_len:
            b = data[pos]; pos += 1  # noqa: E702
            tag |= (b & 0x7F) << shift
            if not (b & 0x80):
                valid = True
                break
            shift += 7
            if shift >= 64:
                return strings
        if not valid:
            break

        wire_type = tag & 0x7

        if wire_type == 0:  # varint — skip
            while pos < data_len:
                b = data[pos]; pos += 1  # noqa: E702
                if not (b & 0x80):
                    break
        elif wire_type == 1:  # 64-bit — skip
            pos += 8
        elif wire_type == 2:  # length-delimited
            length = 0
            shift = 0
            valid = False
            while pos < data_len:
                b = data[pos]; pos += 1  # noqa: E702
                length |= (b & 0x7F) << shift
                if not (b & 0x80):
                    valid = True
                    break
                shift += 7
                if shift >= 64:
                    return strings
            if not valid or length < 0 or pos + length > data_len:
                break

            chunk = data[pos:pos + length]
            pos += length

            try:
                text = chunk.decode('utf-8')
                # Keep if it contains meaningful alphabetic content
                stripped = text.strip()
                if stripped and sum(1 for c in stripped if c.isalpha()) > 2:
                    strings.append(text)
                else:
                    # Short/non-alpha chunk may be a nested message — recurse
                    strings.extend(extract_protobuf_strings(chunk, depth + 1))
            except UnicodeDecodeError:
                # Binary data — try as nested protobuf
                strings.extend(extract_protobuf_strings(chunk, depth + 1))
        elif wire_type == 5:  # 32-bit — skip
            pos += 4
        else:
            break

    return strings
