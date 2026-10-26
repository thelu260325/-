# Official IEEE conference template: provenance and use

## Files retained without modification

- `IEEEtran.cls`: IEEEtran V1.8b, 26 August 2015, official IEEE journal/conference document class maintained by Michael Shell. This is the actual class, not an emulation of IEEE formatting.
- `bare_conf.tex`: the actual upstream conference sample/template shipped with IEEEtran. All original comments retained.
- `IEEEtran.bst`: IEEE reference bibliography style.
- `UPSTREAM_README.txt`: original upstream README (decompressed, content unmodified).
- `bare_conf.pdf`: successful compilation of the unmodified upstream conference template.

## Acquisition and integrity

Direct IEEE/CTAN hosts were blocked by the current network proxy. The genuine class/template was therefore obtained from the Debian TeX Live archive, without editing its contents or installing system packages:

- https://deb.debian.org/debian/pool/main/t/texlive-extra/texlive-publishers_2024.20250309-2_all.deb
- https://deb.debian.org/debian/pool/main/t/texlive-extra/texlive-publishers-doc_2024.20250309-2_all.deb

The Debian trixie `InRelease` signatures were verified with the machine's preinstalled `/usr/share/keyrings/debian-archive-keyring.pgp`. The `Packages.xz` SHA256 was verified against that signed Release metadata, and both package SHA256 values were verified against `Packages.xz`. No TLS, checksum or signature verification was disabled. The original signed `InRelease` and the relevant package checksum metadata are retained in this folder. Large download archives were deleted after extraction and verification.

SHA256 values of the actual retained source files:

```
IEEEtran.cls  da751920a317ed318b7b5cd7fa585a6cc7d28502d457856382e9be24b10a3bd7
IEEEtran.bst  314f0ece704568faf827011bac498650691b2b5ee06320720830e782416d5a5f
bare_conf.tex cc4fa258aa90115ad6afbd8ca5555f448880b29a971398bf1a20ee5f240b45f7
```

## Template reference for report reference [1]

IEEE, “Conference templates.” [Online]. Available: https://www.ieee.org/conferences/publishing/templates.html

This is the official IEEE template landing page. It is a public template reference, but its HTTP content could not be fetched inside the current restricted environment. The actual template source provided here was independently obtained from the authenticated Debian archive above. Do not claim the IEEE page was fetched successfully in this session.

## Compilation and formatting

The current environment has `pdflatex` and `latexmk`. `IEEEtran.cls` was not preinstalled globally, so keep the unmodified class beside the report `.tex` file, or run with the local template directory added to `TEXINPUTS`.

Example from `/workspace/assignment3`:

```
TEXINPUTS=./template//: pdflatex -interaction=nonstopmode -halt-on-error report.tex
TEXINPUTS=./template//: pdflatex -interaction=nonstopmode -halt-on-error report.tex
```

Or copy `IEEEtran.cls` beside `report.tex`. Start from the included `bare_conf.tex`, preserving `\documentclass[conference]{IEEEtran}`. Do not add geometry, manual font-size changes, margins, spacing or column-width overrides. The class supplies 10pt Times-style typography, letter paper and two columns. A smoke test and compilation of the original upstream `bare_conf.tex` both succeeded with the current TeX Live installation.

If using BibTeX, keep `IEEEtran.bst` beside the `.tex` or add the local template directory to `BSTINPUTS`. A manually ordered `thebibliography` environment is also valid; the assignment specifically requires the template link as reference [1].

## Declaration form

`Plagiarism_Declaration_Official_Blank.pdf` is the original blank plagiarism declaration extracted from page 2 of the user's supplied Assignment 1 PDF. No signature, student identity, date or claim of authorship was entered. Assignment 3 requires a declaration but supplies no separate form, so the report group should confirm the module accepts this shared form and complete it truthfully. For a three-person group, each member should complete a declaration if the module requires individual signatures; do not pre-sign on anyone's behalf.
