# How to Use Raman Spectroscopy Measurements

This guide walks you through the complete workflow for uploading and analyzing Raman spectroscopy data in NOMAD.

## Prerequisites

- Access to a Witec Raman spectrometer system
- NOMAD account with appropriate permissions
- Both `*_Spec.Data*.txt` and `*Information*.txt` files from a single measurement

## Step 1: Export Data from Witec Spectrometer

### Export Spectrum Data

1. Open Witec Project or data file in Witec software
2. Select the Raman spectrum measurement
3. Export as text file:
   - **Format**: ASCII/text (.txt)
   - **Includes**: Header section with metadata and Data section with spectrum
   - **Filename pattern**: `[SampleName]_Spec.Data [Number].txt`
   - **Example**: `260721D11 BCS_001_Spec.Data 1.txt`

### Export Measurement Information

1. Select the same measurement
2. Export metadata/configuration as text:
   - **Format**: ASCII/text (.txt)
   - **Includes**: All instrument settings by section
   - **Filename pattern**: `[SampleName] Information.txt`
   - **Example**: `260721D11 BCS_001 Information.txt`

**Important**: Both filenames must share the same base name (e.g., "260721D11 BCS_001") for automatic file pairing to work.

## Step 2: Prepare Files for Upload

1. Verify both files are present:
   - `*_Spec.Data*.txt`
   - `*Information*.txt`

2. Check file integrity:
   - Files are not corrupted
   - Both files are readable text format
   - File size is reasonable (typically 10 KB – 1 MB)

## Step 3: Upload to NOMAD

### Via Web Interface

1. Log in to your NOMAD instance
2. Navigate to **Upload** section
3. Create a new upload or use existing entry
4. Drag and drop both Raman files into the upload area
5. Click **Process** or **Upload**
6. NOMAD will automatically detect and parse the Raman files

### Via Command Line (if available)

```bash
nomad upload --user youruser@institution.org \
  "260721D11 BCS_001_Spec.Data 1.txt" \
  "260721D11 BCS_001 Information.txt"
```

## Step 4: Link to Sample (if needed)

1. After upload completes, navigate to the Raman measurement entry
2. In the **Samples** section, click **Add Sample**
3. Search for and select the corresponding sample entry
4. Save the entry

**Note**: Sample linking is optional but recommended for traceability.

## Step 5: Verify and Analyze

1. Check the **Raman Spectrum** plot:
   - X-axis: Raman Shift (cm⁻¹)
   - Y-axis: Intensity (CCD counts)
   - Should show expected spectral features

2. Review instrument configuration:
   - **Excitation Beam**: Wavelength, power
   - **Spectrometer**: Grating, center wavelength
   - **Detector**: Camera model, integration settings
   - **Objective**: Magnification, numerical aperture
   - **Sample Location**: Stage XYZ coordinates

3. Download raw data if needed:
   - Spectrum arrays (Raman shift and intensity)
   - All metadata fields

## Troubleshooting

### Files Not Recognized

**Problem**: Upload doesn't detect Raman files
- **Solution**: Verify filenames follow pattern: `*_Spec.Data*.txt` and `*Information*.txt`
- **Solution**: Ensure base name (before `_Spec.Data` or ` Information`) matches exactly

### Parser Errors

**Problem**: Parser fails with "could not find paired files"
- **Solution**: Both files must be uploaded together in the same upload
- **Solution**: Check file names for typos or extra spaces

**Problem**: Missing metadata fields
- **Solution**: Information file may not contain all expected sections
- **Solution**: Fields are optional; missing ones will be left blank

### Plot Not Generated

**Problem**: Spectrum plot doesn't appear
- **Solution**: Verify spectrum data section exists in `_Spec.Data` file
- **Solution**: Check that X and Y arrays have matching lengths
- **Solution**: Ensure values are numeric (not text)

## Best Practices

1. **Organize samples**: Keep measurements in project/group folders by sample name
2. **Consistent naming**: Use clear, systematic naming conventions
3. **Metadata completeness**: Ensure Information file contains all relevant data
4. **Backup originals**: Keep raw Witec project files as backup
5. **Documentation**: Add notes in ELN for measurement conditions (power, time, averaging)

## Next Steps

- [Reference Guide](../reference/raman_schema.md) - Complete field descriptions
- [Background Information](../explanation/raman_setup.md) - Instrument details
- [Example Walkthrough](../tutorial/raman_example.md) - Learn from example data
