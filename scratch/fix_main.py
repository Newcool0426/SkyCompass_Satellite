import re

with open("src/main.cpp", "r", encoding="utf-8") as f:
    content = f.read()

# Remove showRecommendations block
# The block starts with "if (showRecommendations) {"
# And ends before "// Draw Time Machine at bottom right"
content = re.sub(r'if \(showRecommendations\) \{[\s\S]*?\}[\s\n]*// Draw Time Machine', '// Draw Time Machine', content)

# Fix stray '}' at the very end
content = re.sub(r'\}\s*\}\s*$', '}\n', content)

with open("src/main.cpp", "w", encoding="utf-8") as f:
    f.write(content)
