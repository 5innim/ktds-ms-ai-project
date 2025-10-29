from tree_sitter import Parser, Language
import tree_sitter_java as tsjava

JAVA_LANGUAGE = Language(tsjava.language())
parser = Parser(JAVA_LANGUAGE)


def make_documents_tree(documents):
    project_trees = {}
    
    for doc in documents:
        file_path = doc.metadata['path']
        content = doc.page_content
    
        if file_path.endswith(".java"):
            print(f"[Java] 파싱 중: {file_path}")
            # Java 파서는 bytes를 입력받음
            tree = parser.parse(bytes(content, "utf8"))
            project_trees[file_path] = tree.root_node
        
    return project_trees

def print_tree_recursive(node, depth=0):
    indent = "  " * depth  # 들여쓰기
    
    # 1. 노드 타입 출력
    print(f"{indent}- Type: {node.type}", end="")

    # 2. 자식이 없는 노드(리프 노드)이거나, 'identifier'처럼
    #    텍스트가 중요한 노드면 실제 텍스트도 함께 출력합니다.
    if node.child_count == 0 or node.type in ['identifier', 'string_fragment']:
        # .text는 bytes이므로 .decode()가 필요합니다.
        print(f"  [Text: '{node.text.decode('utf8')}']")
    else:
        # 자식이 있는 노드는 줄바꿈만 합니다.
        print()

    # 3. 모든 자식 노드에 대해 재귀 호출
    for child in node.children:
        print_tree_recursive(child, depth + 1)
        
