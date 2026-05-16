with open("style.css", "r") as f:
    content = f.read()

new_css = """
/* App Toggle Button */
.app-toggle-btn {
    border: 1px solid @outline_variant;
    border-radius: 4px;
    background-color: transparent;
    color: @on_surface_variant;
}
.app-toggle-btn.active {
    background-color: @primary;
    border-color: @primary;
    color: @on_primary;
}
"""

if "/* App Toggle Button */" not in content:
    with open("style.css", "a") as f:
        f.write(new_css)
