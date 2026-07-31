import os
import re

replacements = {
    r"bg-white/5": "bg-white",
    r"bg-white/10": "bg-white",
    r"border-white/20": "border-edge",
    r"border-white/10": "border-edge",
    r"text-white/70": "text-primary-700",
    r"text-white/50": "text-primary-500",
    r"text-white/40": "text-primary-400",
    r"text-white": "text-primary-900",
    r"backdrop-blur-\w+": "",
    r"shadow-\[inset_0_1px_1px_rgba\(255,255,255,0\.4\),0_8px_32px_rgba\(0,0,0,0\.5\)\]": "shadow-card",
    r"shadow-\[0_4px_30px_rgba\(0,0,0,0\.1\)\]": "shadow-card",
    r"bg-glass-bg": "bg-surface",
    r"text-1": "text-primary-900",
    r"text-2": "text-primary-700",
    r"text-3": "text-primary-500",
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for pattern, repl in replacements.items():
        new_content = re.sub(pattern, repl, new_content)
        
    # Also strip inline backdropFilter styles
    new_content = re.sub(r"backdropFilter:\s*'[^\']+',?", "", new_content)
    new_content = re.sub(r"WebkitBackdropFilter:\s*'[^\']+',?", "", new_content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated: {filepath}")

def main():
    src_dir = os.path.join("d:\\zylo\\New folder", "frontend-src", "src")
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith((".jsx", ".js", ".css")):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
