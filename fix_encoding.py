import os

def fix_file(filepath):
    if not os.path.exists(filepath): return
    with open(filepath, 'rb') as f:
        content = f.read()
    
    try:
        text = content.decode('utf-8-sig') # Handle BOM if present
    except Exception as e:
        print(f'Error reading {filepath}: {e}')
        return
        
    replacements = {
        'Ã¢Å“â€¦': '✅',
        'Ã¢Å¡Â ': '⚠',
        'Ã¢Å¡Â ': '⚠',  
        'Ã¢Â Å’': '❌',
        'Ã°Å¸â€œâ€ž': '📄',
        'Ã°Å¸â€œâ€˜': '📑',
        'Ã°Å¸â€œâ€¹': '📋',
        'Ã¢Â¬â€ ': '⬆',
        'Ã¢Å“Â Ã¯Â¸Â ': '✏️',
        'Ã¢Â Â±Ã¯Â¸Â ': '⏱️',
        'Ã°Å¸â€œâ€š': '📂',
        'Ã¢â€ â‚¬': '─',
        'Ã¢Â â‚¬': ' ',
        'Ã°Å¸â€œÂ ': '📌',
        'Ã¢Å“Â¨': '✨',
        'Ã¢Å¡Â¡': '⚡',
        'Ã°Å¸â€™Â¾': '💾',
        'Ã°Å¸Å¡â‚¬': '🚀',
        'Ã¢Å¡â„¢Ã¯Â¸Â ': '⚙️',
        'Ã°Å¸â€œÅ ': '📊',
        'Ã¢ËœÂ ': '☁️',
        'â€': '-',
        'âœ…': '✅',
        'âš ï¸': '⚠',
        'âš ': '⚠',
        'âŒ': '❌',
        'âœ': '✏️',
        'ðŸ“„': '📄',
        'ðŸ“‘': '📑',
        'ðŸ“‹': '📋',
        'ðŸ“‚': '📂',
        'Ã¢Å“â€': '✅',
        'Ã¢â€”â€ ': '◈',
        'Ã¢Å“â€ ': '✅',
        'Ã¢ÂÅ½': '⎘',
        'Ã¢Å Âž': '⊞',
        'Ã¢Å“Â¦': '✦',
        'Ã¢â€šÂ¹': '₹',
        'Ã¢â€ â€': '⬈',
        'Ã¢â‚¬â€': '—'
    }
    
    original = text
    for bad, good in replacements.items():
        text = text.replace(bad, good)
        
    if text != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Fixed mojibake in {filepath}')
    else:
        print(f'No mojibake found in {filepath}')

fix_file('frontend/pages/tenderGeneration.py')
fix_file('frontend/pages/dashboard.py')
fix_file('frontend/pages/bidGeneration.py')
fix_file('frontend/pages/profile.py')
