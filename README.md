<div align="center">
  <img src="/photos/privmeta_banner.gif" alt="PrivMeta Banner" width="100%">
</div>

<table>
  <tr>
    <td valign="top">
      <strong>PrivMeta</strong> is a command-line utility for inspecting, cleaning, and modifying EXIF and metadata across images, PDFs, office documents, audio, and video files.<br><br>
      Metadata often contains more than you intend to share: exact GPS coordinates, timestamps, camera serial numbers, editing software history, and even embedded thumbnails of the original image. PrivMeta gives you full local control over this data layer. It makes no network requests, and it never modifies files without your explicit instruction.
    </td>
    <td valign="top" align="right" width="180">
      <img src="/photos/privmeta.png" alt="PrivMeta Logo" width="160">
    </td>
  </tr>
</table>

---

## [+] Features

| Command | Action | Supported Formats |
| :--- | :--- | :--- |
| `info` | Inspect metadata, tag counts, and raw segments. | JPEG, PNG, WebP, PDF, DOCX, XLSX, PPTX, MP3, FLAC, MP4, MOV |
| `clean` | Strip EXIF, GPS, XMP, IPTC, ICC, and comments. | JPEG, PNG, WebP |
| `fake` | Inject realistic camera, lens, and GPS metadata. | JPEG, PNG, WebP |
| `shred` | Metadata destruction, re-encoding, and overwrite passes. | JPEG, PNG, WebP, PDF, DOCX, XLSX, PPTX, MP3, FLAC, MP4, MOV |

**[+] What It Actually Does**

- **EXIF Stripping:** Removes camera make, model, software, ISO, aperture, shutter speed, and timestamps.
- **GPS Removal:** Removes latitude, longitude, altitude, and direction data.
- **XMP/IPTC Deletion:** Removes Adobe XMP XML segments and Photoshop IPTC blocks.
- **ICC Profile Removal:** Removes embedded color profiles, which may contain device-related information.
- **Comment Stripping:** Removes JPEG COM segments and PNG tEXt/zTXt chunks.
- **Thumbnail Destruction:** Removes embedded EXIF thumbnails, which may contain an image of the original scene even if the main image was cropped or edited.
- **Fake Camera Injection:** Generates plausible metadata using 15 camera profiles covering brands such as Sony, Canon, Nikon, Fujifilm, Leica, Apple, Samsung, Google, and Olympus.
- **GPS Spoofing:** Injects coordinates from 35 cities around the world, with configurable radius variance.
- **Timeline Simulation:** Distributes timestamps sequentially across multiple files to simulate a chronological event.
- **Anti-Forensic Shredding:** Re-encodes images to alter original quantization tables and encoder signatures.
- **Multi-Pass Overwrite:** Repeatedly writes and strips metadata to reduce residual metadata in the resulting file structure.

### [+] Performance & Security

- **Zero Network Calls:** Operates entirely offline. No analytics, crash reports, or external API calls.
- **In-Memory Streams:** Uses low-memory streaming where possible, helping it run on Termux and low-end devices.
- **Minimal Core Dependencies:** `clean` and `fake` require `piexif` and `Pillow`. PDF and audio support are optional add-ons.

---

## [>] Quick Install

### [i] Linux, macOS, and Termux

```bash
git clone https://github.com/tc4dy/privmeta.git
cd privmeta
./install.sh
```

### [i] Windows

```powershell
git clone https://github.com/tc4dy/privmeta.git
cd privmeta
.\install.ps1
```

### [i] Manual Installation

```bash
pip install .
privmeta --help
```

### [!] Optional Dependencies

- `pypdf` — PDF metadata support.
- `mutagen` — Audio metadata support.
- `ffmpeg` — Video metadata support (system package).

---

## [</>] Usage

Running `privmeta` without arguments opens an interactive menu. For scripting and automation, use the subcommands directly.

### [>] Example Output

**[i] Inspecting a file**

```text
$ privmeta info beach.jpg

──────────────────────────────────────
   PrivMeta EXIF/Metadata Privacy Tool
──────────────────────────────────────
   v0.1.1 | github.com/tc4dy

[+] beach.jpg [jpeg]
[>] 0th: 8 tags
[>] Exif: 14 tags
[>] GPS: 6 tags
[>] thumbnail: present
[>] segments: icc, xmp
```

**[i] Cleaning a file**

```text
$ privmeta clean --all beach.jpg

──────────────────────────────────────
   PrivMeta EXIF/Metadata Privacy Tool
──────────────────────────────────────
   v0.1.1 | github.com/tc4dy

[>] plan: exif, gps, xmp, iptc, icc, comments, thumbnail
[+] cleaned: beach.jpg -> beach_cleaned.jpg
[+] done: 1 ok, 0 failed, 0 skipped, 0 dry
```

### [i] Inspect

Check what metadata is attached to a file before modifying it.

```bash
privmeta info photo.jpg
```

Output lists the EXIF sections found, tag counts, the presence of a thumbnail, and raw metadata segments such as XMP and ICC.

### [</>] Clean

Remove metadata without re-encoding the image, preserving the original image's pixel data.

```bash
privmeta clean photo.jpg
```

Remove specific fields while keeping others:

```bash
privmeta clean --drop gps,thumbnail photo.jpg
privmeta clean --keep exif photo.jpg
```

Strip metadata from files throughout a directory. Use `-r` to descend into subdirectories:

```bash
privmeta clean --all -r ~/Pictures/
```

**[+] Clean Options**

| Flag | Description |
| :--- | :--- |
| `--all` | Remove every supported metadata field or segment. |
| `--drop FIELD` | Remove specific fields: `exif`, `gps`, `xmp`, `iptc`, `icc`, `comments`, or `thumbnail`. |
| `--keep FIELD` | Keep only specified fields and remove the rest. |
| `-r, --recursive` | Descend into subdirectories. |
| `-o, --output-dir` | Write results to a specific directory. |
| `--inplace` | Overwrite the original file. |
| `--keep-backup` | Create a `.bak` copy before using `--inplace`. |
| `--rename` | Rename output files using a neutral pattern, such as `photo_0001.jpg`. |
| `--reset-time` | Reset filesystem modification timestamps to a neutral date. |
| `--dry-run` | Show what would be removed without writing changes. |
| `--fail-fast` | Stop processing after the first error. |

### [+] Fake

Inject synthetic metadata. This can be useful for testing pipelines, simulating camera output, or generating sample files with controlled metadata.

```bash
privmeta fake --camera sony_a7iv --city istanbul photo.jpg
```

Simulate a trip with sequentially increasing dates and a regenerated thumbnail:

```bash
privmeta fake --camera fuji_x100v --city tokyo --date-range 2024-05-01:2024-05-07 --timeline --thumbnail photo.jpg
```

**[+] Fake Options**

| Flag | Description |
| :--- | :--- |
| `--camera KEY` | Select a camera profile. If omitted, a random profile is chosen. |
| `--city KEY` | Inject GPS coordinates associated with a specific city. |
| `--radius KM` | Set the GPS variance radius around the city center. |
| `--date-range START:END` | Constrain timestamps to a specified ISO date range. |
| `--timeline` | Distribute timestamps sequentially across files. |
| `--preserve` | Merge new metadata with existing metadata instead of replacing it entirely. |
| `--thumbnail` | Regenerate the embedded EXIF thumbnail to match the newly injected metadata. |
| `--seed N` | Seed the random number generator for reproducible output. |

**[>] Available Camera Profiles**

`sony_a7iv`, `sony_a7iii`, `canon_r6`, `canon_r5`, `nikon_z6ii`, `nikon_z7ii`, `fuji_xt4`, `fuji_x100v`, `panasonic_s5`, `leica_q2`, `iphone_14_pro`, `iphone_13`, `samsung_s22`, `google_pixel_7`, `olympus_om1`

**[>] Available Cities**

`istanbul`, `ankara`, `izmir`, `bursa`, `antalya`, `london`, `paris`, `berlin`, `madrid`, `rome`, `amsterdam`, `vienna`, `prague`, `athens`, `lisbon`, `newyork`, `losangeles`, `chicago`, `toronto`, `mexicocity`, `tokyo`, `osaka`, `seoul`, `beijing`, `shanghai`, `singapore`, `bangkok`, `dubai`, `cairo`, `capetown`, `sydney`, `melbourne`, `buenosaires`, `saopaulo`, `moscow`

### [<>] Shred

Aggressive metadata destruction for scenarios where standard cleaning is insufficient. The command re-encodes images to alter original encoder signatures and performs multiple overwrite passes.

```bash
privmeta shred --passes 3 --check photo.jpg
```

Re-encode the image at a specified JPEG quality:

```bash
privmeta shred --quality 95 photo.jpg
```

**[+] Shred Options**

| Flag | Description |
| :--- | :--- |
| `--passes N` | Specify the number of overwrite cycles. More passes may increase processing time. |
| `--quality N` | Re-encode the image at a specified JPEG quality, altering its original encoding characteristics. |
| `--check` | Validate the resulting file for malformed metadata and inconsistent values. |

---

## [!] Privacy Notes

- **[!] ICC Profiles:** Removing an ICC profile can alter the perceived colors of an image, especially on wide-gamut displays. If color accuracy is important, use `--keep icc` when cleaning.
- **[!] Timestamps:** PrivMeta can reset metadata timestamps, but it cannot modify a file's inode change time (`ctime`) on Linux through ordinary file operations. This is an operating system restriction.
- **[!] Backups:** By default, output is written to a new file. If you use `--inplace`, consider enabling `--keep-backup` to retain the original.
- **[!] Shredding Limitations:** Re-encoding and overwriting data inside a file do not guarantee secure erasure of all previous copies. Filesystems, SSD wear-leveling, snapshots, backups, and journaling may preserve recoverable data outside the resulting file.
