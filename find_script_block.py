file_path = r'E:\Keperluan Webiste\Green Productions\app\templates\qc\monitoring.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '{% block scripts %}' in line:
        print(f"Found block scripts at line {i+1}")
    if '<script>' in line:
        print(f"Found <script> at line {i+1}")
