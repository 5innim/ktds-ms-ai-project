import re
from tree_sitter import Parser, Language, QueryCursor, Query
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
import tree_sitter_java as tsjava

JAVA_LANGUAGE = Language(tsjava.language())
parser = Parser(JAVA_LANGUAGE)

def parse_java_code(content: str):
    """Parses Java code using tree-sitter."""
    return parser.parse(bytes(content, "utf8"))

def node_text(node, source_bytes):
    return source_bytes[node.start_byte:node.end_byte].decode('utf-8')

def get_class_and_method_chunks(doc: Document) -> list[Document]:
    """Extracts classes and methods as separate Document chunks from a Java file."""
    if not doc.page_content:
        return []
        
    tree = parse_java_code(doc.page_content)
    root_node = tree.root_node
    
    chunks = []
    
    # Tree-sitter query to find all class and method declarations
    query_string = """
    (class_declaration) @class
    (method_declaration) @method
    """
    
    query = Query(JAVA_LANGUAGE, query_string)
    cursor = QueryCursor(query)
    captures = cursor.captures(root_node)
    
    source_bytes = doc.page_content.encode()

    try:
        for class_node in captures['class']:
            chunk_content = node_text(class_node, source_bytes)
            symbol_name = node_text(class_node.child_by_field_name('name'), source_bytes)
            chunk_metadata = doc.metadata.copy()
            chunk_metadata.update({
                "symbol_name": symbol_name,
                "symbol_type": "class",
                "start_line": class_node.start_point[0],
                "end_line": class_node.end_point[0],
            })

            chunks.append(Document(
                page_content=chunk_content,
                metadata=chunk_metadata
            ))
    except KeyError:
        print("No class captures found.")

    try:
        for method_node in captures['method']:
            chunk_content = node_text(method_node, source_bytes)
            symbol_name = node_text(method_node.child_by_field_name('name'), source_bytes)
            chunk_metadata = doc.metadata.copy()
            chunk_metadata.update({
                "symbol_name": symbol_name,
                "symbol_type": "method",
                "start_line": method_node.start_point[0],
                "end_line": method_node.end_point[0],
            })

            chunks.append(Document(
                page_content=chunk_content,
                metadata=chunk_metadata
            ))
    except KeyError:
        print("No method captures found.")
        
    print(f"return chunks!: {len(chunks)}")
        
    return chunks

def _find_symbols_for_lines(tree, line_numbers: set, page_content: str) -> set:
    """Finds class/method symbols in a tree that contain the given line numbers."""
    root_node = tree.root_node
    changed_symbols = set()
    
    query_string = """
    (class_declaration) @class
    (method_declaration) @method
    """
    
    query = Query(JAVA_LANGUAGE, query_string)
    cursor = QueryCursor(query)
    captures = cursor.captures(root_node)
    source_bytes = page_content.encode()
    
    try:
        for class_node in captures['class']:
            start_line = class_node.start_point[0]
            end_line = class_node.end_point[0]

            if any(line_num in range(start_line, end_line + 1) for line_num in line_numbers):
                symbol_name_node = class_node.child_by_field_name('name') 
                if symbol_name_node:
                    symbol_name = node_text(symbol_name_node, source_bytes)
                    changed_symbols.add(symbol_name)

    except KeyError:
        print("No class captures found.")

    try:
        for method_node in captures['method']:
            start_line = method_node.start_point[0]
            end_line = method_node.end_point[0]

            if any(line_num in range(start_line, end_line + 1) for line_num in line_numbers):
                symbol_name_node = method_node.child_by_field_name('name') 
                if symbol_name_node:
                    symbol_name = node_text(symbol_name_node, source_bytes)
                    changed_symbols.add(symbol_name)
    except KeyError:
        print("No method captures found.")

    print('--------------')
    print(changed_symbols)
    return changed_symbols

def apply_patch(source_content: str, patch: str) -> str:
    """
    Apply a unified git patch to source_content.
    This implementation covers common cases but is still simplified compared to git-apply.
    Raises ValueError on malformed patch or when patch context doesn't match source.
    """
    source_lines = source_content.splitlines()
    patched_lines = []
    src_idx = 0

    patch_lines = patch.splitlines()
    i = 0
    # Skip possible file header lines (---/+++)
    while i < len(patch_lines) and not patch_lines[i].startswith('@@'):
        i += 1

    while i < len(patch_lines):
        line = patch_lines[i]
        if not line.startswith('@@'):
            i += 1
            continue

        m = re.match(r'^@@ -(\d+)(?:,(\d*))? \+(\d+)(?:,(\d*))? @@', line)
        if not m:
            raise ValueError(f"Malformed hunk header: {line}")

        old_start = int(m.group(1))
        old_count = int(m.group(2)) if m.group(2) not in (None, '') else 1
        new_start = int(m.group(3))
        new_count = int(m.group(4)) if m.group(4) not in (None, '') else 1

        # Add unchanged lines before this hunk (old_start is 1-based)
        pre_hunk_end = old_start - 1
        if pre_hunk_end < src_idx:
            raise ValueError("Patch hunks overlap or are out of order")
        patched_lines.extend(source_lines[src_idx:pre_hunk_end])
        src_idx = pre_hunk_end
        i += 1

        # Process hunk body
        old_consumed = 0
        new_consumed = 0
        while i < len(patch_lines) and not patch_lines[i].startswith('@@'):
            h = patch_lines[i]
            if h.startswith('+'):
                # addition: append the new line (without +)
                patched_lines.append(h[1:])
                new_consumed += 1
            elif h.startswith('-'):
                # deletion: consume one line from source but do not append
                if src_idx >= len(source_lines):
                    raise ValueError("Patch deletes beyond end of source")
                # optionally check that source line equals h[1:]? unified diff doesn't include original content for deletions prefixed with '-'
                src_idx += 1
                old_consumed += 1
            elif h.startswith(' '):
                # context line: must match source
                if src_idx >= len(source_lines):
                    raise ValueError("Patch context beyond end of source")
                src_line = source_lines[src_idx]
                patch_ctx = h[1:]
                if src_line != patch_ctx:
                    raise ValueError(f"Patch context mismatch at source line {src_idx+1}: expected {patch_ctx!r}, got {src_line!r}")
                patched_lines.append(src_line)
                src_idx += 1
                old_consumed += 1
                new_consumed += 1
            else:
                # ignore other lines (e.g., index/, ---/+++), but if encountered inside hunk treat as error
                raise ValueError(f"Unexpected line in hunk: {h!r}")
            i += 1

        # Optionally validate consumed counts against header (be lenient if headers used 0)
        if old_count != 0 and old_consumed != old_count:
            # allow mismatch if header omitted count (but header defaulted to 1 above), still warn via exception
            raise ValueError("Old count does not match hunk body")
        if new_count != 0 and new_consumed != new_count:
            raise ValueError("New count does not match hunk body")

    # Append remaining source lines
    patched_lines.extend(source_lines[src_idx:])

    # Preserve trailing newline semantics: if source_content ended with newline, ensure result does too
    if source_content.endswith('\n'):
        return '\n'.join(patched_lines) + '\n'
    else:
        return '\n'.join(patched_lines)

def get_changed_symbols_from_patch(patch: str, file_content: str) -> list[str]:
    """
    Identifies changed class or method symbols from a git patch using tree-sitter.
    It handles added and removed lines separately by analyzing the code before and after the patch.
    """
    if not file_content or not patch:
        return []

    # --- 1. Get content before and after patch ---
    content_before = file_content
    content_after = apply_patch(file_content, patch)

    # --- 2. Parse line numbers for additions and deletions ---
    added_lines = set()
    deleted_lines = set()
    hunk_re = re.compile(r'^@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@')

    current_old_line = 0
    current_new_line = 0

    for line in patch.split('\n'):
        if line.startswith('@@'):
            match = hunk_re.match(line)
            if match:
                current_old_line = int(match.group(1))
                current_new_line = int(match.group(3))
        elif line.startswith('-'):
            deleted_lines.add(current_old_line - 1) # 0-indexed
            current_old_line += 1
        elif line.startswith('+'):
            added_lines.add(current_new_line - 1) # 0-indexed
            current_new_line += 1
        elif line.startswith(' '): # Context line
            current_old_line += 1
            current_new_line += 1
            
    changed_symbols = set()

    # --- 3. Find symbols in "before" content for deleted lines ---
    if deleted_lines:
        tree_before = parse_java_code(content_before)
        changed_symbols.update(_find_symbols_for_lines(tree_before, deleted_lines, content_before))

    # --- 4. Find symbols in "after" content for added lines ---
    if added_lines:
        tree_after = parse_java_code(content_after)
        changed_symbols.update(_find_symbols_for_lines(tree_after, added_lines, content_after))

    return list(changed_symbols)
