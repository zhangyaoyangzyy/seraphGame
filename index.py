from flask import Flask, request, jsonify
import ddddocr
import base64
from PIL import Image
import io

app = Flask(__name__)


def correct_padding(base64_str):
    return base64_str + '=' * (-len(base64_str) % 4)


@app.route('/match', methods=['POST'])
def match():
    try:
        target_base64 = request.json.get('target')
        background_base64 = request.json.get('background')

        if not target_base64 or not background_base64:
            return jsonify({'error': 'Missing target or background image data'}), 400

        if target_base64.startswith('data:image'):
            target_base64 = target_base64.split(',')[1]
        if background_base64.startswith('data:image'):
            background_base64 = background_base64.split(',')[1]

        target_base64 = correct_padding(target_base64)
        background_base64 = correct_padding(background_base64)

        try:
            target_bytes = base64.b64decode(target_base64)
            background_bytes = base64.b64decode(background_base64)

            target_image = Image.open(io.BytesIO(target_bytes))
            background_image = Image.open(io.BytesIO(background_bytes))
        except Exception as e:
            return jsonify({'error': 'Failed to decode base64 data or convert to image', 'message': str(e)}), 400

        try:
            target_buffer = io.BytesIO()
            background_buffer = io.BytesIO()
            target_image.save(target_buffer, format="PNG")
            background_image.save(background_buffer, format="PNG")
            target_bytes = target_buffer.getvalue()
            background_bytes = background_buffer.getvalue()
        except Exception as e:
            return jsonify({'error': 'Failed to convert images to bytes', 'message': str(e)}), 400

        det = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)

        res = det.slide_match(target_bytes, background_bytes, simple_target=True)

        target_position = res['target'][:2]
        return jsonify({
            'target_x': target_position[0],
            'target_y': target_position[1]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
