# Demo recording with VHS (https://github.com/charmbracelet/vhs)
# Install: winget install charmbracelet.vhs  (or brew install vhs)
# Run:     vhs docs/demo.tape  -> docs/demo.gif

Output docs/demo.gif
Set FontSize 16
Set Width 900
Set Height 420
Set Theme "Dracula"

Type "r7z a demo.7z ./testdata/A/biglog.txt -m 5 -t 4"
Sleep 500ms
Enter
Sleep 3s
Type "r7z l demo.7z"
Sleep 500ms
Enter
Sleep 1s
Type "r7z x demo.7z -o extracted/ -t 4"
Sleep 500ms
Enter
Sleep 2s