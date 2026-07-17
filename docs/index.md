# Welcome to the `nomad-inl-base` documentation

**nomad-inl-base** is a [NOMAD](https://nomad-lab.eu) plugin developed at
[INL – International Iberian Nanotechnology Laboratory](https://www.inl.int)
for the **Sadewasser Reasearch Group** (Previously know as Laboratory for Nanostructured Solar Cells - LaNaSC) group.
It provides ELN (Electronic Lab Notebook) schemas and automatic normalization routines for thin-film research covering:

- **STAR (SpuTtering for Advanced Research) magnetron sputtering** – DC, RF, and reactive DC (pulsed Se) deposition; selenization annealing; substrate heating and rotation; target inventory tracking
- **METEOR (Metal EvaporaTion by Electron-beam for SOlar Research) e-beam evaporation** – Korvus Technology METEOR system with `.nbl` log parser, four-pocket management, QCM thickness monitoring, and automatic thin film creation
- **Batteries** – PC03 CathodeChamber and PC04 ElectrolyteChamber sputtering/annealing log parsers, with automatic sample creation and linking based on the sample name embedded in the log filename
- **Wet deposition** – spin coating, slot-die coating, blade coating, inkjet printing, spray pyrolysis, dip coating, and chemical bath deposition
- **Characterization** – XRD, UV-Vis transmission, 4-point probe, KLA-Tencor profilometry, EQE, solar cell IV, GDOES, SEM, EDX/EDS spectra, Bruker AFM/KPFM/cAFM, cyclic voltammetry (CV), linear-sweep voltammetry (IV), electrochemical impedance spectroscopy (EIS), and chronoamperometry
- **Analysis** – Jupyter notebook–based analysis for EQE, solar cell IV, GDOES, and XRD data, built on the `nomad-analysis` plugin
- **Shared entities** – substrates, thin films, thin-film stacks, instruments, selenium cells, and sample fragments referenced across all schemas

<div markdown="block" class="home-grid">
<div markdown="block">

### Tutorial

New to the plugin? The tutorial walks you through a complete experiment:
creating a substrate, running a spin-coating deposition, and recording an
XRD measurement – all linked together through shared entity references.

- [Start the tutorial](tutorial/tutorial.md)

</div>
<div markdown="block">

### How-to guides

Practical step-by-step instructions for common tasks:

- [Install this plugin](how_to/install_this_plugin.md)
- [Use this plugin](how_to/use_this_plugin.md)
- [Contribute to this plugin](how_to/contribute_to_this_plugin.md)
- [Contribute to the documentation](how_to/contribute_to_the_documentation.md)

</div>

<div markdown="block">

### Explanation

Background concepts: the Entity/Activity model, how ThinFilm chains work,
recipe-based automation, the target inventory system, and electrochemistry
schemas.

- [Read the explanation](explanation/explanation.md)

</div>
<div markdown="block">

### Reference

Complete schema reference with all quantities, units, and behavior for
each ELN entry type.

- [Entities](reference/entities.md)
- [STAR Sputtering](reference/sputtering.md)
- [METEOR E-Beam](reference/meteor.md)
- [Batteries](reference/batteries.md)
- [Wet Deposition](reference/wet_deposition.md)
- [Characterization](reference/characterization.md)
- [Analysis](reference/analysis.md)

</div>
</div>

## Schema overview

| Schema | Category | Entry type |
|--------|----------|------------|
| `INLSubstrate` | INL Entities | Entity |
| `INLThinFilm` | INL Entities | Entity |
| `INLThinFilmStack` | INL Entities | Entity |
| `INLInstrument` | INL Entities | Entity |
| `INLGraphiteBox` | INL Entities | Entity |
| `INLSampleFragment` | INL Entities | Entity |
| `SeleniumCell` | STAR | Entity |
| `SputteringTarget` | STAR | Entity |
| `StarCalibrationData` | STAR | Activity |
| `StarSputteringRecipe` | STAR | Template |
| `StarRFSputtering` | STAR | Activity |
| `StarDCSputtering` | STAR | Activity |
| `STARDCReactiveSputtering` | STAR | Activity |
| `STARSelenizationAnnealing` | STAR | Activity |
| `METEORDeposition` | METEOR | Activity |
| `METEORPocket` | METEOR | Sub-section |
| `METEORQCMMonitor` | METEOR | Sub-section |
| `PC03CathodeChamberDeposition` | Batteries | Activity |
| `PC04ElectrolyteChamberDeposition` | Batteries | Activity |
| `PC04SubstrateAnnealing` | Batteries | Activity |
| `WetDepositionRecipe` | INL Wet Deposition | Template |
| `INLSpinCoatingRecipe` | INL Wet Deposition | Template |
| `INLSpinCoating` | INL Wet Deposition | Activity |
| `INLSlotDieCoating` | INL Wet Deposition | Activity |
| `INLBladeCoating` | INL Wet Deposition | Activity |
| `INLInkjetPrinting` | INL Wet Deposition | Activity |
| `INLSprayPyrolysis` | INL Wet Deposition | Activity |
| `INLDipCoating` | INL Wet Deposition | Activity |
| `INLChemicalBathDeposition` | INL Wet Deposition | Activity |
| `INLXRayDiffraction` | INL Characterization | Measurement |
| `INLUVVisTransmission` | INL Characterization | Measurement |
| `INLFourPointProbe` | INL Characterization | Measurement |
| `INLKLATencorProfiler` | INL Characterization | Measurement |
| `INLEQE` | INL Characterization | Measurement |
| `INLSolarCellIV` | INL Characterization | Measurement |
| `INLGDOES` | INL Characterization | Measurement |
| `INLSEMSession` | INL Characterization | Measurement |
| `WorkingElectrode` | INL Characterization | Entity |
| `ElectrolyteSolution` | INL Characterization | Entity |
| `PotentiostatMeasurement` | INL Characterization | Measurement |
| `INLEDXSpectrum` | INL Characterization | Measurement |
| `ChronoamperometryMeasurement` | INL Characterization | Measurement |
| `EISMeasurement` | INL Characterization | Measurement |
| `EQEJupyterAnalysis` | Analysis using Jupyter notebooks | Analysis |
| `SolarCellJupyterAnalysis` | Analysis using Jupyter notebooks | Analysis |
| `GDOESJupyterAnalysis` | Analysis using Jupyter notebooks | Analysis |
| `INLXRDJupyterAnalysis` | Analysis using Jupyter notebooks | Analysis |
