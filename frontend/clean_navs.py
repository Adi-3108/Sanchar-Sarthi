import os
import re

files = [
    r'c:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock\frontend\app\simulation\page.tsx',
    r'c:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock\frontend\app\settings\page.tsx',
    r'c:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock\frontend\app\post-event-learning\page.tsx',
    r'c:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock\frontend\app\officer\page.tsx',
    r'c:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock\frontend\app\explorer\page.tsx',
    r'c:\Users\Hema\Downloads\FLipkart\FlipKart-Gridlock\frontend\app\events\[id]\page.tsx'
]

pattern = re.compile(r'\s*<nav className=\"flex flex-wrap gap-3\">.*?</nav>', re.DOTALL)

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    new_content = pattern.sub('', content)
    
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Updated {f}')
