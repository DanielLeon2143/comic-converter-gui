"""Explanations of the options, shown by the ? icons and in the tutorial.

HELP: option key -> (title, explanation). TUTORIAL: the sections of the tutorial window; the
options of each Settings tab are listed from HELP, so the two never disagree.
"""

HELP = {
    # Export panel and General tab
    "output_dir": ("Output folder",
                   "Where the EPUB files are written. Leave it empty to write each EPUB next to its comic "
                   "(same folder, same name, .epub)."),
    "profile": ("Device",
                "The e-reader you will read on. It sets the size of the pages, and what the device supports "
                "(color, manga mode, JPEG XL...). Pick your exact model for the best result."),
    "mode": ("Reading mode",
             "Comic: pages read left to right. Manga: right to left (the double pages are cut in the "
             "other order). Webtoon: for long vertical strips: the images of each folder are joined and cut into "
             "pages in the gaps between panels (crop, double page and blank page options are not used)."),
    "format": ("Image format",
               "JPEG: small files, a tiny loss of quality (best for most comics). PNG: no loss, bigger files. "
               "JPEG XL: smaller and better, Apple Books only. Copy: keeps the source images as they are, no processing."),
    "quality": ("Quality",
                "Quality of the JPEG and JPEG XL images, from 1 to 100. 85 is a good balance; 90+ for sharper "
                "pages and bigger files. 100 makes JPEG XL lossless."),
    "limitmb": ("Split every (MB)",
                "Maximum size of each EPUB: a bigger comic is split into parts (\"Part 1 of 3\"). 0 = never "
                "split, minimum 20. Send to Kindle accepts 200 MB on its website, 50 MB by email or app."),
    "title": ("Title",
              "Title of the EPUB in your library. Empty: the name of the folder or file. Used only when there is "
              "one comic in the list."),
    "author": ("Author", "Author shown in your e-reader's library."),
    "grayscale": ("Grayscale",
                  "Converts the pages to shades of gray: smaller files, and what eInk screens show anyway. It can "
                  "only be turned off with a color device."),
    "grayscale-mode": ("Grayscale mode",
                       "How colors become gray. Normal: the usual formula. Average: the average of red, green and blue. "
                       "Luminance: follows the brightness the eye perceives, often the best on eInk."),
    "autocontrast": ("Auto contrast",
                     "Stretches the tones of each page so the darkest part becomes black and the lightest white. "
                     "Good for faded scans."),
    "noblankimage": ("Remove blank images", "Drops the pages that are completely blank."),
    "presets": ("Quality presets",
                "Shortcuts that set several options at once. Good: grayscale JPEG q90. Great: the same, not "
                "resized. Best: color JPEG q100, not resized. Max: color PNG, not resized. No filter: turns off "
                "crop, contrast and blank page removal."),
    # Image tab
    "brightness": ("Brightness", "Lightens (above 0) or darkens (below 0) every page, from -100 to 100."),
    "contrast": ("Contrast", "More (above 0) or less (below 0) contrast on every page, from -100 to 100."),
    "resize": ("Reduce large images",
               "Shrinks the pages bigger than the screen of the device: much smaller files, no visible loss."),
    "zoom": ("Zoom",
             "Stores the pages bigger than the screen, for a sharper image when you zoom in. 0 = the default of the "
             "device (1.5 for Apple Books, 1 for the others), otherwise 1 to 3. The size of the EPUB grows a lot."),
    "aspect-ratio": ("Aspect ratio",
                     "Shape of the pages (height divided by width), from 0.5 to 3. -1 = the shape of the device's "
                     "screen, 0 = the shape of each source page (not for webtoon), 1.6 = Amazon's advice for Kindle."),
    "jxl-effort": ("JPEG XL effort", "Only for JPEG XL: 1 encodes fast, 7 makes the smallest files but is slower."),
    "foreground-color": ("Foreground color",
                         "Color of the text of the title page and the cover caption, in hexadecimal (000000 = black)."),
    "background-color": ("Background color",
                         "Color around the pages when they don't fill the screen, in hexadecimal (FFFFFF = white, "
                         "DDDDDD = light gray, 777777 = dark gray)."),
    # Crop tab
    "crop": ("Crop the margins",
             "Removes the white (or uniform) margins around each page, so the drawing fills more of the screen. "
             "A page with a crop box drawn in the preview is not auto-cropped."),
    "crop-ratio-left": ("Crop ratio left",
                        "How strict the margin detection is on the left: the share of non-blank pixels allowed in a "
                        "column that is still cut. Higher cuts more (and may cut into the drawing)."),
    "crop-ratio-up": ("Crop ratio top", "Same as the left ratio, for the top margin."),
    "crop-ratio-right": ("Crop ratio right", "Same as the left ratio, for the right margin."),
    "crop-ratio-bottom": ("Crop ratio bottom",
                          "Same as the left ratio, for the bottom margin (3 by default: page numbers often sit there)."),
    "crop-limit": ("Crop limit (%)",
                   "The most that can be cut from a page, in percent of its size. 0 = no limit."),
    "crop-skip-if-limit-reached": ("Skip if the limit is reached",
                                   "When the crop would go over the limit, the page is not cropped at all, "
                                   "instead of cropped up to the limit."),
    # Pages & Layout tab
    "doublepagemode": ("Double pages",
                       "What happens to a page wider than tall (a spread, or a wraparound cover). Split: cut in two "
                       "pages. Split + rotate: the whole page turned sideways, then the two halves. Rotate: only the "
                       "whole page turned sideways. To keep only part of one page (e.g. the front of a cover), draw "
                       "a crop box on it in the preview."),
    "keepsplitdoublepageaspect": ("Keep the aspect of split double pages",
                                  "The two halves of a split double page keep the same size: best when you "
                                  "read in landscape."),
    "combinesplitdoublepage": ("Combine double pages split in 2 files",
                               "Finds spreads that were scanned as two files (their facing edges match) and joins "
                               "them into one double page."),
    "landscape": ("Landscape only (Kindle Scribe)",
                  "Spreads the pages left and right, as a book open in landscape. Kindle Scribe profiles only."),
    "strip": ("Strip the first folder of the table of contents",
              "When all the pages are in one folder, leaves it out of the table of contents."),
    "titlepage": ("Title page",
                  "Adds a page with the title before the cover. Never, Always, or only when the EPUB is split in "
                  "parts (to show \"Part 1 of 3\")."),
    "covercaption": ("Cover caption", "Writes \"Part X of Y\" on the cover when the EPUB is split in parts."),
    "sort": ("Sort files",
             "Order of the pages. Alphanumeric (path and file): numbers are compared by value, page2 before "
             "page10 (recommended). The other modes compare the file names, or all the names, as text."),
    "font": ("Font (.ttf)",
             "TrueType font of the title page and the cover caption. Empty: the embedded Literata font."),
    # Advanced tab
    "exe": ("go-comic-converter",
            "The converter used. Leave empty to use the one built into the app (needed for the crop boxes)."),
    "workers": ("Workers", "Number of pages processed at the same time. The number of processor cores is a good value."),
    "extra_args": ("Extra arguments",
                   "Options passed as they are to go-comic-converter, for the rare cases not in the window, "
                   "e.g. -crop-limit=10."),
    "use_saved_config": ("Use the tool's saved config",
                         "Starts from the options saved by go-comic-converter -save (~/.go-comic-converter.yaml). "
                         "Off: only the options of this window count."),
    "open_folder_when_done": ("Open the output folder when done",
                              "Opens the folder of the EPUBs in Explorer once the whole list is converted."),
    "theme": ("Appearance", "Light, dark, or the same as Windows. Also switched with the switch at the top right."),
}

# The tabs of the Settings window and their options, in the tutorial.
SETTINGS_TABS = [
    ("General", ["profile", "mode", "format", "quality", "limitmb", "presets", "title", "author", "grayscale",
                 "grayscale-mode", "autocontrast", "noblankimage"]),
    ("Image", ["brightness", "contrast", "resize", "zoom", "aspect-ratio", "jxl-effort", "foreground-color",
               "background-color"]),
    ("Crop", ["crop", "crop-ratio-left", "crop-ratio-up", "crop-ratio-right", "crop-ratio-bottom", "crop-limit",
              "crop-skip-if-limit-reached"]),
    ("Pages & Layout", ["doublepagemode", "keepsplitdoublepageaspect", "combinesplitdoublepage", "landscape", "strip",
                        "titlepage", "covercaption", "sort", "font"]),
    ("Advanced", ["exe", "workers", "extra_args", "use_saved_config", "open_folder_when_done", "theme"]),
]

# (heading, paragraphs); "options:<tab>" lists the options of a Settings tab.
TUTORIAL = [
    ("Welcome", [
        "Comic Converter turns folders of images, CBZ, ZIP, CBR, RAR and PDF files into EPUBs for your e-reader "
        "(Kindle, Kobo, reMarkable, Apple Books). It's made to convert many comics at once.",
        "Every option has a ? next to it: hover or click it for an explanation. This tutorial can be opened again "
        "with Help, at the top right.",
    ]),
    ("1. Add your comics", [
        "Drag and drop comics or folders anywhere on the window, or use Select Folder (Ctrl or Shift + click to "
        "pick several folders) and Select File.",
        "A folder of images becomes one comic; its subfolders become the chapters of the table of contents. When "
        "a folder contains CBZ/CBR/PDF files, you choose whether each file is a comic, or the folder as a whole.",
    ]),
    ("2. Check the pages in the preview", [
        "Pick a comic above the preview (the list, or ◀ ▶). Original shows the pages in the exact order they will "
        "have in the EPUB. Converted shows each page the way your e-reader's screen shows it, with your settings: "
        "the shape of the screen and the margins, crop, grayscale, split double pages (◧ and ◨ tell on which side "
        "of the spread each half goes), title page. It updates by itself when you change a setting.",
        "Click a page to open it bigger; the arrow keys go to the next and previous pages.",
    ]),
    ("3. Fix a page with a crop box", [
        "A page wider than tall is cut in two by default: a wraparound cover (back, spine and front) becomes the "
        "back cover, then the front cover. To fix it, open the page in the Original view and drag a rectangle "
        "around what you want to keep, e.g. the front cover. Left half and Right half do it in one click.",
        "A page with a crop box is exactly that rectangle, as one page: never split, not auto-cropped. Drag inside "
        "the box to move it, drag its edges to resize it, Delete or Remove crop to go back to normal. From the "
        "Converted view, Edit the crop of this page opens the original page.",
        "Crop boxes are remembered for each comic. Pages with one show ✂ in the preview, and the list of comics "
        "shows how many pages of each comic have one.",
    ]),
    ("4. Choose the export options", [
        "The panel on the right has the options used most: output folder, device, reading mode, format, quality, "
        "split size, title page, grayscale, contrast and crop. All the others are in Settings, at the top right.",
        "The options are the same for every comic of the list.",
    ]),
    ("5. Convert", [
        "Convert all converts the whole list, one comic after the other. The list shows the status and the EPUB "
        "of each comic, the bar shows the progress of the whole list, and the log at the bottom the details and "
        "the errors. Stop cancels.",
        "Dry run checks the options of every comic without converting. Command copies the go-comic-converter "
        "command line of these options. Clear finished removes the comics done; Open output folder shows the EPUBs.",
    ]),
    ("Settings: General", ["options:General"]),
    ("Settings: Image", ["options:Image"]),
    ("Settings: Crop", ["options:Crop"]),
    ("Settings: Pages & Layout", ["options:Pages & Layout"]),
    ("Settings: Advanced", ["options:Advanced"]),
    ("Tips", [
        "Kindle by email: set Split every to 40 MB. Kindle Scribe and other big screens: pick the exact device, "
        "the pages are made for its resolution.",
        "Pages out of order: number your files with leading zeros (page01, page02...) or keep Sort files on "
        "Alphanumeric (path and file).",
        "Faded scans: Auto contrast, or Grayscale mode Luminance. Margins cut into the drawing: lower the crop "
        "ratios, or turn Crop the margins off.",
    ]),
]
