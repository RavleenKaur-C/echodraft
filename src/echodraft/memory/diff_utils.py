import difflib

def line_level_diff(original: str, edited: str) -> list[str]:
    """
    Return simplified diff ops:
    - lines prefixed with "- " (deleted)
    - lines prefixed with "+ " (added)
    - lines prefixed with "~ FROM ==> TO" (changed heuristic for single-line changes)
    """
    diffs = []
    orig_lines = original.splitlines()
    edit_lines = edited.splitlines()
    sm = difflib.SequenceMatcher(a=orig_lines, b=edit_lines)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'delete':
            for l in orig_lines[i1:i2]:
                diffs.append(f"- {l}")
        elif tag == 'insert':
            for l in edit_lines[j1:j2]:
                diffs.append(f"+ {l}")
        elif tag == 'replace':
            # pair lines heuristically
            for l_old, l_new in zip(orig_lines[i1:i2], edit_lines[j1:j2]):
                diffs.append(f"~ {l_old} ==> {l_new}")
            # handle length mismatch
            for l in orig_lines[i1 + (j2-j1):i2]:
                diffs.append(f"- {l}")
            for l in edit_lines[j1 + (i2-i1):j2]:
                diffs.append(f"+ {l}")
    return diffs
