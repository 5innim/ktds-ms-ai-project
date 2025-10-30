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

    print(f"Captures: {captures}")

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
            print(f"method chunk_metadata: {chunk_metadata}")

            chunks.append(Document(
                page_content=chunk_content,
                metadata=chunk_metadata
            ))
    except KeyError:
        print("No method captures found.")
        
    print(f"return chunks!: {len(chunks)}")
        
    return chunks

def get_changed_symbols_from_patch(patch: str, file_content: str) -> list[str]:
    """
    Identifies changed class or method symbols from a git patch using tree-sitter.
    """
    if not file_content:
        return []

    tree = parse_java_code(file_content)
    root_node = tree.root_node
    
    # --- 1. Parse line numbers from the patch ---
    changed_lines = set()
    # @@ -3,7 +3,7 @@
    for line in patch.split('\n'):
        if line.startswith('@@'):
            parts = line.split(' ')
            # parts[2] is like "+3,7"
            line_info = parts[2]
            start_line, num_lines = map(int, line_info.lstrip('+').split(','))
            for i in range(num_lines):
                changed_lines.add(start_line + i -1) # 0-indexed

    # --- 2. Find symbols that contain the changed lines ---
    changed_symbols = set()
    
    query_string = """
    (class_declaration) @class
    (method_declaration) @method
    """
    query = JAVA_LANGUAGE.query(query_string)
    captures = query.captures(root_node)

    for node, capture_name in captures:
        start_line = node.start_point[0]
        end_line = node.end_point[0]
        
        # Check if the node's line range intersects with changed lines
        if any(line_num in range(start_line, end_line + 1) for line_num in changed_lines):
            symbol_name_node = node.child_by_field_name('name')
            if symbol_name_node:
                symbol_name = symbol_name_node.text.decode('utf8')
                changed_symbols.add(symbol_name)

    return list(changed_symbols)
