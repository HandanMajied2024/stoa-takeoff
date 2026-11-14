# Data and model licences

The code in this repository is separate from the data it was developed and evaluated on. The data is not
included, except for the few demo drawings bundled into the hosted demo (built by `deploy/build_demo.py`).

| What | Source | Licence |
|---|---|---|
| Swiss apartment plans (demo + benchmark) | Swiss Dwellings v3.0.0, Archilyse AG, https://doi.org/10.5281/zenodo.7788422; drawings rendered by the Junction dataset authors | CC BY 4.0 |
| BIM-Speed IFC models (Gdynia, Vitoria) | Garcia, A. G.; Hartmann, T. (2022), BIM-Speed Demonstration Projects, TU Berlin, https://doi.org/10.14279/depositonce-16441.2 | CC BY 4.0 |
| KIT IFC models (FZK-Haus, AC20 Institute) | Karlsruhe Institute of Technology, Institute for Automation and Applied Informatics | free for any use |
| Finnish scanned plans (demo + training) | CubiCasa5K, (c) 2019 CubiCasa; Kalervo et al., SCIA 2019, https://zenodo.org/records/2613548 | CC BY-NC-SA 4.0 |
| `models/cubicasa_symbols.pt` (symbol detector weights) | YOLO11s (Ultralytics, AGPL-3.0) fine-tuned on CubiCasa5K train/val | derived from CC BY-NC-SA 4.0 data and AGPL-3.0 software: **non-commercial use, share-alike** |

Commercial use of the scan detector requires retraining on data you have commercial rights to.
