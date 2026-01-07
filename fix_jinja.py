import re

file_path = r'E:\Keperluan Webiste\Green Productions\app\templates\production\timeline.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix all the broken Jinja2 syntax
replacements = [
    ('{ { order.id } }', '{{order.id}}'),
    ('{ { order.get_production_progress() } }', '{{order.get_production_progress()}}'),
    ('{ { order.production_tasks.count() } }', '{{order.production_tasks.count()}}'),
    ("{ { order.production_tasks.filter_by(status = 'completed').count() } }", "{{order.production_tasks.filter_by(status='completed').count()}}"),
    ('} {% if not loop.last %}, {% endif %}', '}{% if not loop.last %},{% endif %}'),
]

for old, new in replacements:
    content = content.replace(old, new)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed Jinja2 syntax!')
