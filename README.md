# Treemendous
Treemendous is an accessible tree creation and exploration tool especially designed for blind and vision impaired practitioners and students of linguistics and computer science.

![A screenshot of the Treemendous interface showing a syntax tree of the sentence "I touch the cactus" alongside a graphical rendering of the tree.](https://user-images.githubusercontent.com/2476107/144321528-087596c4-c583-466d-a2fc-1fd924d921e9.png)

## Getting Treemendous
The [latest version of Treemendous](https://github.com/codeofdusk/treemendous/releases/latest) and sample trees in Treemendous format are available on GitHub. Windows is the recommended operating system for which binary installer and portable packages are provided. Some support for non-Windows systems may be available, but it is incomplete and requires running Treemendous from source.

## Using Treemendous
### Opening a tree
On launch, Treemendous opens to an empty tree. A Treemendous file can be opened by selecting "open" from the file menu, pressing the standard <kbd>Ctrl</kbd>+<kbd>o</kbd> keyboard shortcut, or, if file associations were selected at install time, directly from Windows Explorer.

#### Sample trees
[Examples of completed tree diagrams in Treemendous format](https://github.com/codeofdusk/treemendous/releases/latest) taken from linguistics and computer science are available on GitHub. To view or edit one of the sample files, simply open it as described above.

### Exploring the tree
When Treemendous opens, focus is set to a tree control containing the tree's contents. To explore the tree, use the arrow keys, mouse, or, if on MacOS, the VoiceOver cursor (including VO+backslash to expand/collapse a node). If using a screen reader, based on screen reader configuration, the currently focused level, location, and expanded/collapsed state will be reported as you navigate.

### Adding a node
To add a new node, press the "add" button in the window or use the keyboard shortcut <kbd>Alt</kbd>+<kbd>a</kbd>. If the tree is currently empty, a dialog box for adding a root node will be displayed. Otherwise, a menu of node locations will appear containing the following options:

* Child: The newly added node will be contained by the current selection.
* Parent: The newly added node will contain the current selection.
* Sibling: The newly added node will be placed at the same level as the current selection.

Once a node location has been selected, the "add node" dialog will appear, containing fields for label and value. In computer science, the label and value of a node might represent the key and value, respectively, of a key–value pair represented by the newly added node. In a syntax tree, the label might contain the name of a syntactic category, such as N, and the represented word would be entered into the value field. If this node does not represent such a pair though, simply enter the node text into the label field and leave the value blank. When finished, press OK to add the new node to the tree.

### Editing a node
To edit the currently selected node, press <kbd>F2</kbd> or select "edit node" from the <kbd>Shift</kbd>+<kbd>F10</kbd>/right click context menu. An edit node dialog will appear, from which the node's label and value can be changed. Press OK to save changes or cancel to close the dialog without saving.

### HTML-like formatting
The following HTML-like tags can be placed anywhere in a node's label or value to produce formatted text. For ease of editing, raw tags are shown in the Treemendous interface. However, well-formed formatted text will appear when the tree is exported to an alternative format.

Tag | Description | Example
--- | --- | ---
b | Bold | `<b>This text is bold</b>`
i | Italic | `<i>This text is in italics</i>`
u | Underline | `The word <u>underlined</u> is underlined`
sup | Superscript | `D<sup>i</sup> has a superscript i`
sub | Subscript | `x<sub>1</sub> has a subscript 1`
null | Empty set symbol | `<null/>`
bar | Superscript prime symbol, used in [X-bar theory](https://en.wikipedia.org/wiki/X-bar_theory) | `X<bar/>`

### Moving a node
To adjust the position of a node within its parent, use the move up/move down options in the node's <kbd>Shift</kbd>+<kbd>F10</kbd>/right click context menu, or <kbd>Alt</kbd>+up/down arrows.

The selected subtree (node and all descendants) can be copied and pasted both within the current Treemendous tree and across other opened files, as long as all trees are opened in the same Treemendous process (second, third, etc. instances created by selecting "new" from the file menu). To mark the current selection for copying, press <kbd>Ctrl</kbd>+<kbd>c</kbd> or select "copy" from the edit menu on the menu bar. Then, at the point where you wish to paste, press <kbd>Ctrl</kbd>+<kbd>v</kbd> or select "paste" from the edit menu.

### Deleting nodes
To delete the currently selected subtree (node and all descendants), select delete from the <kbd>Shift</kbd>+<kbd>F10</kbd>/right click menu, or press <kbd>Del</kbd> on the keyboard.

### Notes
It may be helpful to include notes in a Treemendous file, such as the sentence from which a syntactic tree was generated or source attributions. To show or hide the notes field, select "notes" from the view menu on the menu bar. When shown, the notes field can be focused with the tab key or the keyboard shortcut <kbd>Alt</kbd>+<kbd>n</kbd>.

### Saving
To save the currently opened tree, select "save" or "save as" from the file menu on the menu bar, or use the standard <kbd>Ctrl</kbd>+<kbd>s</kbd> keyboard shortcut for save or <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>s</kbd> for save as. Trees can be saved in the following formats, either by selecting from the "save as type" combo box or naming the file with the associated file extension:

Format | File extension | Description
--- | --- | ---
Treemendous | .treemendous | Used for viewing and editing the tree in an accessible format using Treemendous.
Graphviz | .gv | A plain text representation of the tree for use with [Graphviz](https://graphviz.org/).
PNG | .png | The [portable network graphics](https://en.wikipedia.org/wiki/Portable_Network_Graphics) image format.

### Visual representation
To view a graphical representation of the opened Treemendous tree, for instance to aid collaboration with sighted colleagues/instructors, select "visual" from the view menu on the menu bar. Press <kbd>Esc</kbd> to close the visual view and return to Treemendous.

### LaTeX representation
To view a plain text representation of the currently opened Treemendous tree for inclusion in a [LaTeX](https://www.latex-project.org/) document, select LaTeX from the view menu on the menu bar. Note that the [Qtree](https://ctan.org/pkg/qtree) package is required and must be included in the document preamble. Press <kbd>Esc</kbd> to close the LaTeX view and return to Treemendous.

## Developing Treemendous
Note: The following assumes that `python` and `pip` refer to Python version 3.6 or later. On some systems, you may need to run `python3` or `pip3` instead.

### Running from source
From the root of the repo, install dependancies with `pip install -Ur requirements.txt`, then run `python src/treemendous.py` to start the GUI.

### Running unit tests
To run unit tests for the `tree` module, run `python src/test_tree.py`.
