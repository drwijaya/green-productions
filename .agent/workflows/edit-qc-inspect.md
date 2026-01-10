---
description: How to safely edit the QC inspect.html template
---

# Safe Editing of QC Inspect Template

The `app/templates/qc/inspect.html` file contains Jinja2 template syntax that can easily break during edits. Follow these guidelines to prevent template errors.

## Known Fragile Patterns

The following Jinja expressions are used in JavaScript and are prone to corruption:

1. **Line ~1023**: `const targetQty = {{ task.qty_target }};`
2. **Line ~1041**: `function addParameterRow(id, name, defaultQty = {{ task.qty_target }}, isCustom = false)`
3. **Line ~1108**: `const targetQty = parseInt(...) || {{ task.qty_target }};`

## Common Error Pattern

When this file is edited, the Jinja closing braces `}}` sometimes get split across lines like:
```
{{ task.qty_target }
};
```

This causes `TemplateSyntaxError: unexpected '}'`.

## Prevention Steps

1. **After ANY edit to this file**, run this verification command:
```powershell
Select-String -Path "app\templates\qc\inspect.html" -Pattern "task\.qty_target"
```

2. **Check that ALL occurrences show `}}` properly closed** (not split across lines)

3. **If broken, run this fix script**:
```powershell
python -c "
import re
path = r'app\templates\qc\inspect.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix broken Jinja patterns
content = re.sub(r'\{\{\s*task\.qty_target\s*\}\s*\n\s*\};', '{{ task.qty_target }};', content)
content = re.sub(r'\{\{\s*task\.qty_target\s*\}(?!\})', '{{ task.qty_target }}', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed!')
"
```

## Root Cause

The file edit tools sometimes:
- Split multi-character sequences like `}}` when the line is modified
- Create extra newlines within JavaScript statements
- Lose the second `}` when replacing content near Jinja expressions

## Best Practice

When adding JavaScript to this template:
1. Keep Jinja expressions on a single line
2. Always verify the file after edits
3. Use the fix script if errors occur
