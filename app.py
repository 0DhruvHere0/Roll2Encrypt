try:
    from flask import Flask, request, jsonify, render_template
except Exception:
    Flask = None
    class _Dummy:
        pass
    request = _Dummy()
    def jsonify(x):
        return x
    def render_template(x, **kw):
        return ''

from collections import Counter
import heapq
import random

app = Flask(__name__) if Flask else None

class Node:
    def __init__(self, char=None, freq=0):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(text):
    freq = Counter(text)
    heap = [Node(ch, fr) for ch, fr in freq.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(freq=left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)
    return heap[0]

def generate_codes(node, current="", code_map=None):
    if code_map is None:
        code_map = {}
    if node is None:
        return code_map
    if node.char is not None:
        code_map[node.char] = current if current != "" else "0"
    generate_codes(node.left, current + "0", code_map)
    generate_codes(node.right, current + "1", code_map)
    return code_map

def encode_ludo_style(binary):
    result = []
    for bit in binary:
        color = random.choice(['R', 'G', 'B', 'Y'])
        dice = random.randint(1, 99)
        result.append(f"{color}{dice:02}{bit}")
    return ''.join(result)

def extract_binary(encoded):
    bits = []
    n = len(encoded)
    for i in range(0, n, 4):
        if i + 3 < n:
            b = encoded[i + 3]
            if b in '01':
                bits.append(b)
            else:
                continue
    return ''.join(bits)

def decode_huffman(binary, code_map):
    class TrieNode:
        def __init__(self):
            self.children = {}
            self.char = None
    root = TrieNode()
    for char, code in code_map.items():
        node = root
        for bit in code:
            if bit not in node.children:
                node.children[bit] = TrieNode()
            node = node.children[bit]
        node.char = char
    node = root
    result = ''
    for bit in binary:
        if bit not in node.children:
            return '[Decode error: invalid bit sequence]'
        node = node.children[bit]
        if node.char:
            result += node.char
            node = root
    return result

if app:
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/encrypt", methods=["POST"])
    def encrypt():
        text = request.json.get("text", "")
        if not text:
            return jsonify({"error": "Text is empty"}), 400
        root = build_huffman_tree(text)
        code_map = generate_codes(root)
        binary = ''.join(code_map[ch] for ch in text)
        ludo_encoded = encode_ludo_style(binary)
        return jsonify({
            "hash": ludo_encoded,
            "codes": code_map
        })

    @app.route("/decrypt", methods=["POST"])
    def decrypt():
        encoded = request.json.get("hash", "")
        code_map = request.json.get("codes", {})
        if not encoded or not code_map:
            return jsonify({"error": "Missing hash or code map"}), 400
        binary = extract_binary(encoded)
        original = decode_huffman(binary, code_map)
        return jsonify({
            "original": original
        })

    if __name__ == "__main__":
        app.run(debug=True)
