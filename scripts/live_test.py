import requests

health = requests.get('http://127.0.0.1:8000/health', timeout=10)
print('health', health.status_code, health.json())

img_path = r"E:\codex\signature-verification-cnn\data\raw\divyanshrai_handwritten-signatures\Dataset_Signature_Final\Dataset\dataset1\forge\02100001.png"
with open(img_path, 'rb') as f:
    files = {'file': ('sample.png', f, 'image/png')}
    pred = requests.post('http://127.0.0.1:8000/predict', files=files, timeout=30)
print('predict', pred.status_code, pred.json())
