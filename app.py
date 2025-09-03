try:
    from flask import Flask, request, jsonify, render_template
except Exception:
    Flask = None
    class _Dummy:
        def __init__(self):
            self.json = {}
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
    if not text:
        return None
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
    # encoded is produced as segments of length 4: <Color(1)><Dice(2)><Bit(1)>
    bits = []
    n = len(encoded)
    for i in range(0, n, 4):
        if i + 3 < n:
            b = encoded[i + 3]
            if b in '01':
                bits.append(b)
            else:
                # malformed segment: skip
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
try:
    from flask import Flask, request, jsonify, render_template
except Exception:
    # Flask not available — provide minimal fallbacks so module can be imported
    Flask = None
    class _DummyRequest:
        def __init__(self):
            self.json = {}
    request = _DummyRequest()
    def jsonify(x):
        return x
    def render_template(x, **kw):
        return ''

import hmac
import hashlib
import os
from collections import Counter
import heapq
import random

# Allowed characters as requested (kept in a deterministic order)
CHARSET = list("~`!@#$%^&*()_+{}|:\"<>?-=[]\\;',./1234567890"
               "qwertyuiopasdfghjklzxcvbnm"
               "QWERTYUIOPASDFGHJKLZXCVBNM")
CHARSET_LEN = len(CHARSET)
KEY_LEN = 16

# Use a fixed secret for HMAC. In production replace with a secure secret or env var.
SECRET = os.environ.get('HASH_SECRET', 'change_this_secret')


def derive_token(message: bytes, length: int = KEY_LEN) -> str:
    """Deterministically derive a `length`-char token from message using HMAC-SHA256.

    Maps the HMAC output into our CHARSET by interpreting the digest as a large
    integer and converting it into base-CHARSET_LEN.
    """
    mac = hmac.new(SECRET.encode('utf-8'), message, hashlib.sha256).digest()
    # Interpret digest as big integer
    num = int.from_bytes(mac, 'big')
    out = []
    for _ in range(length):
        out.append(CHARSET[num % CHARSET_LEN])
        num //= CHARSET_LEN
    # Reverse so higher-order bits appear earlier
    return ''.join(reversed(out))


app = Flask(__name__) if Flask else None


def build_huffman_tree(text: str):
    """Build a Huffman tree and return its root. Returns None for empty text."""
    if not text:
        return None
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


class Node:
    def __init__(self, char=None, freq=0):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
    def __lt__(self, other):
        return self.freq < other.freq


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


if app:
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/encrypt', methods=['POST'])
    def encrypt():
        data = request.json or {}
        text = data.get('text', '')
        include_codes = bool(data.get('include_codes', False))
        if not isinstance(text, str):
            return jsonify({'error': 'text must be a string'}), 400

        token = derive_token(text.encode('utf-8'), KEY_LEN)
        resp = {'hash': token}

        if include_codes:
            # Build Huffman codes and include in response
            root = build_huffman_tree(text)
            codes = generate_codes(root)
            resp['codes'] = codes

        return jsonify(resp)

    @app.route('/decrypt', methods=['POST'])
    def decrypt():
        data = request.json or {}
        text = data.get('text', '')
        token = data.get('hash', '')
        # Optional: if codes provided, decode using them
        codes = data.get('codes')
        if not isinstance(text, str) or not isinstance(token, str):
            return jsonify({'error': 'text and hash must be strings'}), 400

        expected = derive_token(text.encode('utf-8'), KEY_LEN)
        ok = hmac.compare_digest(expected, token)
        out = {'valid': ok, 'expected': expected}

        if codes is not None:
            # Attempt to decode using provided codes (reverse mapping)
            # Build bitstring from codes
            try:
                # Recreate binary and decode if possible
                binary = ''.join(codes[ch] for ch in text)
                out['decoded_via_codes'] = text if binary == ''.join(codes[ch] for ch in text) else None
            except Exception:
                out['decoded_via_codes'] = None

        return jsonify(out)

    if __name__ == '__main__':
        app.run(debug=True)
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