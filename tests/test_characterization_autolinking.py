"""
Test suite for automatic characterization-to-sample linking via filename inference.

Tests cover:
1. Sample name extraction from various characterization file naming conventions
2. Fuzzy matching of extracted names against INLThinFilmStack entries
3. Auto-linking integration in INLCharacterization.normalize()
4. Edge cases and error handling
"""

from unittest.mock import Mock, patch

import pytest

from nomad_inl_base.parsers.parser import (
    _extract_sample_name,
    _find_matching_thin_film_stacks,
)
from nomad_inl_base.schema_packages.characterization import INLCharacterization
from nomad_inl_base.schema_packages.entities import (
    INLSampleReference,
    INLThinFilmStack,
)

# ============================================================================
# Phase 1: Test _extract_sample_name() - Multiple characterization types
# ============================================================================


class TestExtractSampleName:
    """Test sample name extraction from characterization filenames."""

    # --- PC03/PC04 Battery Chambers ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param(
                'PC04_All Signals_LNbO_004 2026.07.16-09.32.33.csv',
                'LNbO_004',
                id='pc04_standard',
            ),
            pytest.param(
                'PC03_All Signals_Sample_A 2026.03.15-14.22.11.CSV',
                'Sample_A',
                id='pc03_uppercase_ext',
            ),
            pytest.param(
                'PC04_All Signals_Complex-Name_v2 2026.01.01-00.00.00.csv',
                'Complex-Name_v2',
                id='pc04_complex_name',
            ),
        ],
        ids=lambda x: x.split('_')[0] if isinstance(x, str) else 'result',
    )
    def test_pc03_pc04_format(self, filename, expected):
        """Test extraction from PC03/PC04 battery chamber naming convention."""
        assert _extract_sample_name(filename) == expected

    # --- 4-Point Probe (4pp) ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('sample_name 4pp.xlsx', 'sample_name', id='4pp_xlsx'),
            pytest.param('LNbO_004 4pp.xls', 'LNbO_004', id='4pp_xls'),
            pytest.param('My Sample 4pp.XLSX', 'My Sample', id='4pp_caps'),
        ],
    )
    def test_4pp_format(self, filename, expected):
        """Test extraction from 4-point probe file naming."""
        assert _extract_sample_name(filename) == expected

    # --- Cyclic Voltammetry (mVs) ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('sample mVs.xlsx', 'sample', id='mvs_xlsx'),
            pytest.param('LNbO_004 mVs.xls', 'LNbO_004', id='mvs_xls'),
        ],
    )
    def test_mvs_format(self, filename, expected):
        """Test extraction from cyclic voltammetry file naming."""
        assert _extract_sample_name(filename) == expected

    # --- Electrodeposition (ED) ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('sample_a ED.xlsx', 'sample_a', id='ed_xlsx'),
            pytest.param('SAMPLE_B ED.xls', 'SAMPLE_B', id='ed_xls'),
        ],
    )
    def test_ed_format(self, filename, expected):
        """Test extraction from electrodeposition file naming."""
        assert _extract_sample_name(filename) == expected

    # --- KLA-Tencor Profiler ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('sample profile.pdf', 'sample', id='profile_pdf'),
            pytest.param('LNbO_004 profile.PDF', 'LNbO_004', id='profile_caps'),
        ],
    )
    def test_profiler_format(self, filename, expected):
        """Test extraction from KLA-Tencor profiler file naming."""
        assert _extract_sample_name(filename) == expected

    # --- EQE (Electroluminescence/EQE) ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('sample eqe.txt', 'sample', id='eqe_txt'),
            pytest.param('LNbO_004 eqe.xlsx', 'LNbO_004', id='eqe_xlsx'),
        ],
    )
    def test_eqe_format(self, filename, expected):
        """Test extraction from EQE file naming."""
        assert _extract_sample_name(filename) == expected

    # --- GDOES (Glow Discharge Optical Emission Spectroscopy) ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('sample gdoes.txt', 'sample', id='gdoes_txt'),
            pytest.param('LNbO_004 GDOES.txt', 'LNbO_004', id='gdoes_caps'),
        ],
    )
    def test_gdoes_format(self, filename, expected):
        """Test extraction from GDOES file naming."""
        assert _extract_sample_name(filename) == expected

    # --- SEM TIFF (YYMMDD - Sample Name.tif) ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('250416 - sample_name.tif', 'sample_name', id='sem_tiff_yymmdd'),
            pytest.param('261215 - LNbO_004.TIF', 'LNbO_004', id='sem_tiff_caps'),
        ],
    )
    def test_sem_tiff_format(self, filename, expected):
        """Test extraction from SEM TIFF naming (YYMMDD - Sample.tif)."""
        assert _extract_sample_name(filename) == expected

    # --- Solar Cell IV/EQE Results ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('Sample Results Table.txt', 'Sample', id='solar_results_table'),
            pytest.param('LNbO_004 IV Graph.txt', 'LNbO_004', id='solar_iv_graph'),
            pytest.param('COMPLEX-NAME Results Table.xlsx', 'COMPLEX-NAME', id='solar_complex'),
        ],
    )
    def test_solar_cell_format(self, filename, expected):
        """Test extraction from solar cell IV/EQE naming."""
        assert _extract_sample_name(filename) == expected

    # --- Eclab (MPR) Electrochemistry ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('sample.mpr', 'sample', id='eclab_mpr'),
            pytest.param('LNbO_004 EIS.mpr', 'LNbO_004 EIS', id='eclab_eis_mpr'),
        ],
    )
    def test_eclab_format(self, filename, expected):
        """Test extraction from Eclab MPR file naming."""
        assert _extract_sample_name(filename) == expected

    # --- EDX/EDS Spectra ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('sample.msa', 'sample', id='edx_msa'),
            pytest.param('LNbO_004.emsa', 'LNbO_004', id='edx_emsa'),
            pytest.param('spectrum.ems', 'spectrum', id='edx_ems'),
        ],
    )
    def test_edx_format(self, filename, expected):
        """Test extraction from EDX/EDS file naming."""
        assert _extract_sample_name(filename) == expected

    # --- Bruker AFM ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('sample.001', 'sample', id='bruker_afm_001'),
            pytest.param('LNbO_004.002', 'LNbO_004', id='bruker_afm_002'),
        ],
    )
    def test_bruker_afm_format(self, filename, expected):
        """Test extraction from Bruker AFM file naming."""
        assert _extract_sample_name(filename) == expected

    # --- Witec Optical Spectroscopy ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('sample_Spec.Data', 'sample', id='witec_spectrum'),
            pytest.param('LNbO_004_Spec.Data', 'LNbO_004', id='witec_spectrum_ln'),
        ],
    )
    def test_witec_format(self, filename, expected):
        """Test extraction from Witec optical spectrum file naming."""
        assert _extract_sample_name(filename) == expected

    # --- Edge Cases ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('sample_name', None, id='no_extension'),
            pytest.param('sample.unknown', 'sample', id='unknown_ext_fallback'),
            pytest.param('', None, id='empty_string'),
            pytest.param('   ', None, id='whitespace_only'),
            pytest.param('.txt', None, id='extension_only'),
        ],
    )
    def test_edge_cases(self, filename, expected):
        """Test edge cases and error handling."""
        result = _extract_sample_name(filename)
        assert result == expected

    # --- Archive Extensions (.pl.archive, .raman.archive, etc.) ---
    @pytest.mark.parametrize(
        'filename, expected',
        [
            pytest.param('260901B1_BCS_001.pl.archive', '260901B1_BCS_001', id='pl_archive'),
            pytest.param('MyNano_002.raman.archive', 'MyNano_002', id='raman_archive'),
            pytest.param('Sample_003.xrd.archive', 'Sample_003', id='xrd_archive'),
            pytest.param('UV_004.uv.archive', 'UV_004', id='uv_archive'),
        ],
    )
    def test_archive_extension_format(self, filename, expected):
        """Test extraction from archive-type files (.pl.archive, .raman.archive, etc.)."""
        assert _extract_sample_name(filename) == expected

    # --- Nested Path ---
    def test_nested_path(self):
        """Test extraction from nested file paths."""
        filename = '/path/to/upload/PC04_All Signals_LNbO_004 2026.07.16-09.32.33.csv'
        assert _extract_sample_name(filename) == 'LNbO_004'


# ============================================================================
# Phase 2: Test _find_matching_thin_film_stacks() - Fuzzy Matching
# ============================================================================


class TestFuzzyMatching:
    """Test fuzzy matching of sample names against INLThinFilmStack entries."""

    def _create_mock_stack(self, name, stack_id='stack_1'):
        """Helper to create a mock INLThinFilmStack entry."""
        stack = Mock(spec=INLThinFilmStack)
        stack.name = name
        stack.lab_id = None
        return stack

    def _create_mock_archive(self, stacks):
        """Helper to create a mock EntryArchive with stacks in data."""
        archive = Mock()
        archive.data = {f'stack_{i}': stack for i, stack in enumerate(stacks)}
        archive.m_context = None
        return archive

    def test_exact_match(self):
        """Test that exact sample name matches with high confidence."""
        stacks = [self._create_mock_stack('LNbO_004')]
        archive = self._create_mock_archive(stacks)

        matches = _find_matching_thin_film_stacks('LNbO_004', archive)

        assert len(matches) == 1
        confidence, matched_stack = matches[0]
        assert confidence == 1.0  # Perfect match
        assert matched_stack.name == 'LNbO_004'

    def test_case_insensitive_match(self):
        """Test that matching is case-insensitive."""
        stacks = [self._create_mock_stack('LNbO_004')]
        archive = self._create_mock_archive(stacks)

        # Try various case combinations
        for variant in ['lnbo_004', 'LNBO_004', 'LnBo_004']:
            matches = _find_matching_thin_film_stacks(variant, archive)
            assert len(matches) == 1
            confidence, _ = matches[0]
            assert confidence == 1.0

    def test_typo_tolerance(self):
        """Test fuzzy matching tolerance for minor typos (confidence >= 0.85)."""
        stacks = [self._create_mock_stack('LNbO_004')]
        archive = self._create_mock_archive(stacks)

        # Minor typo: missing one character
        matches = _find_matching_thin_film_stacks('LNbO_04', archive, threshold=0.85)
        assert len(matches) >= 1  # Should match with high confidence

    def test_no_match_below_threshold(self):
        """Test that dissimilar names don't match below confidence threshold."""
        stacks = [self._create_mock_stack('LNbO_004')]
        archive = self._create_mock_archive(stacks)

        matches = _find_matching_thin_film_stacks('CompletelyDifferent', archive, threshold=0.85)
        assert len(matches) == 0

    def test_multiple_candidates_sorted_by_confidence(self):
        """Test sorting when multiple stacks match."""
        stacks = [
            self._create_mock_stack('LNbO'),
            self._create_mock_stack('LNbO_004'),
            self._create_mock_stack('LNbO_004_backup'),
        ]
        archive = self._create_mock_archive(stacks)

        matches = _find_matching_thin_film_stacks('LNbO_004', archive, threshold=0.80)

        # Should have multiple matches, sorted by confidence (descending)
        assert len(matches) >= 1
        confidences = [conf for conf, _ in matches]
        assert confidences == sorted(confidences, reverse=True)

    def test_none_sample_name_returns_empty(self):
        """Test that None sample name returns empty list."""
        stacks = [self._create_mock_stack('LNbO_004')]
        archive = self._create_mock_archive(stacks)

        matches = _find_matching_thin_film_stacks(None, archive)
        assert len(matches) == 0

    def test_no_stacks_in_archive(self):
        """Test handling of archive with no INLThinFilmStack entries."""
        archive = Mock()
        archive.data = {}
        archive.m_context = None

        matches = _find_matching_thin_film_stacks('LNbO_004', archive)
        assert len(matches) == 0

    def test_threshold_parameter(self):
        """Test that confidence_threshold parameter is respected."""
        stacks = [self._create_mock_stack('LNbO')]
        archive = self._create_mock_archive(stacks)

        # With high threshold, should not match
        matches_high = _find_matching_thin_film_stacks('LNbO_004', archive, threshold=0.99)
        assert len(matches_high) == 0

        # With low threshold, should match
        matches_low = _find_matching_thin_film_stacks('LNbO_004', archive, threshold=0.50)
        assert len(matches_low) == 1


# ============================================================================
# Phase 3: Test INLCharacterization.normalize() - Auto-linking Integration
# ============================================================================


class TestCharacterizationAutoLinking:
    """Test automatic linking in INLCharacterization.normalize()."""

    def _create_mock_characterization(self, mainfile):
        """Helper to create a mock characterization entry."""
        char = INLCharacterization()

        # Mock archive with metadata
        archive = Mock()
        archive.metadata = Mock()
        archive.metadata.mainfile = mainfile
        archive.data = {}
        archive.m_context = None

        # Mock logger
        logger = Mock()

        return char, archive, logger

    @patch('nomad_inl_base.schema_packages.characterization._extract_sample_name')
    @patch('nomad_inl_base.schema_packages.characterization._find_matching_thin_film_stacks')
    def test_auto_link_with_matching_stack(self, mock_find, mock_extract):
        """Test that characterization auto-links when matching stack is found."""
        # Setup mocks
        mock_extract.return_value = 'LNbO_004'
        mock_stack = Mock(spec=INLThinFilmStack)
        mock_stack.name = 'LNbO_004'
        mock_find.return_value = [(1.0, mock_stack)]  # Perfect match

        char, archive, logger = self._create_mock_characterization(
            'PC04_All Signals_LNbO_004 2026.07.16-09.32.33.csv'
        )

        # Call normalize
        char.normalize(archive, logger)

        # Verify auto-linking occurred
        assert len(char.samples) == 1
        assert char.samples[0].reference == mock_stack

    @patch('nomad_inl_base.schema_packages.characterization._extract_sample_name')
    @patch('nomad_inl_base.schema_packages.characterization._find_matching_thin_film_stacks')
    def test_no_auto_link_with_manual_linking(self, mock_find, mock_extract):
        """Test that auto-linking is skipped when manual linking already exists."""
        # Setup with manual linking already present
        char, archive, logger = self._create_mock_characterization(
            'sample 4pp.xlsx'
        )
        char.samples = [Mock(spec=INLSampleReference)]  # Already manually linked

        # Call normalize
        char.normalize(archive, logger)

        # Verify extraction was NOT called (because manual linking exists)
        mock_extract.assert_not_called()
        mock_find.assert_not_called()

    @patch('nomad_inl_base.schema_packages.characterization._extract_sample_name')
    @patch('nomad_inl_base.schema_packages.characterization._find_matching_thin_film_stacks')
    def test_no_auto_link_when_no_match_found(self, mock_find, mock_extract):
        """Test that no linking occurs when no matching stack is found."""
        # Setup mocks
        mock_extract.return_value = 'UnknownSample'
        mock_find.return_value = []  # No matches

        char, archive, logger = self._create_mock_characterization(
            'UnknownSample 4pp.xlsx'
        )

        # Call normalize
        char.normalize(archive, logger)

        # Verify no samples were added
        assert len(char.samples or []) == 0

    @patch('nomad_inl_base.schema_packages.characterization._extract_sample_name')
    @patch('nomad_inl_base.schema_packages.characterization._find_matching_thin_film_stacks')
    def test_auto_link_uses_best_match(self, mock_find, mock_extract):
        """Test that auto-linking uses the best (most confident) match."""
        # Setup mocks
        mock_extract.return_value = 'LNbO_004'
        mock_stack_best = Mock(spec=INLThinFilmStack)
        mock_stack_best.name = 'LNbO_004'
        mock_stack_ok = Mock(spec=INLThinFilmStack)
        mock_stack_ok.name = 'LNbO'
        # Return multiple matches, sorted by confidence
        mock_find.return_value = [
            (1.0, mock_stack_best),
            (0.90, mock_stack_ok),
        ]

        char, archive, logger = self._create_mock_characterization(
            'sample 4pp.xlsx'
        )

        # Call normalize
        char.normalize(archive, logger)

        # Verify best match was linked
        assert len(char.samples) == 1
        assert char.samples[0].reference == mock_stack_best

    @patch('nomad_inl_base.schema_packages.characterization._extract_sample_name')
    def test_no_auto_link_when_extraction_fails(self, mock_extract):
        """Test graceful handling when sample name extraction fails."""
        # Setup mock to return None (extraction failed)
        mock_extract.return_value = None

        char, archive, logger = self._create_mock_characterization(
            'unknown_file.xyz'
        )

        # Call normalize - should not raise
        char.normalize(archive, logger)

        # Verify no samples were added
        assert len(char.samples or []) == 0

    @patch('nomad_inl_base.schema_packages.characterization._extract_sample_name')
    @patch('nomad_inl_base.schema_packages.characterization._find_matching_thin_film_stacks')
    def test_auto_link_error_handling(self, mock_find, mock_extract):
        """Test that errors during auto-linking are caught and logged."""
        # Setup mock to raise an exception
        mock_extract.side_effect = RuntimeError('Extraction error')

        char, archive, logger = self._create_mock_characterization(
            'sample 4pp.xlsx'
        )

        # Call normalize - should not raise
        char.normalize(archive, logger)

        # Verify warning was logged
        logger.warning.assert_called()

    @patch('nomad_inl_base.schema_packages.characterization._extract_sample_name')
    @patch('nomad_inl_base.schema_packages.characterization._find_matching_thin_film_stacks')
    def test_logging_on_successful_link(self, mock_find, mock_extract):
        """Test that successful auto-linking is logged with confidence."""
        # Setup mocks
        mock_extract.return_value = 'LNbO_004'
        mock_stack = Mock(spec=INLThinFilmStack)
        mock_stack.name = 'LNbO_004'
        mock_find.return_value = [(0.95, mock_stack)]

        char, archive, logger = self._create_mock_characterization(
            'sample 4pp.xlsx'
        )

        # Call normalize
        char.normalize(archive, logger)

        # Verify info log was called with confidence info
        logger.info.assert_called()
        call_args = logger.info.call_args[0][0]
        assert '95' in call_args  # Should mention the confidence percentage

    @patch('nomad_inl_base.schema_packages.characterization._extract_sample_name')
    @patch('nomad_inl_base.schema_packages.characterization._find_matching_thin_film_stacks')
    def test_auto_link_with_fallback_archive_extension(self, mock_find, mock_extract):
        """Test auto-linking with fallback cleanup of archive extensions."""
        # Setup: Extract returns name with .pl.archive suffix
        mock_extract.return_value = '260901B1_BCS_001.pl.archive'
        mock_stack = Mock(spec=INLThinFilmStack)
        mock_stack.name = '260901B1_BCS'

        # Mock find to be called twice: first with full name (no match), then with cleaned name (match)
        mock_find.side_effect = [
            [],  # First call with '260901B1_BCS_001.pl.archive' - no match
            [(0.95, mock_stack)]  # Second call with '260901B1_BCS_001' - match found
        ]

        char, archive, logger = self._create_mock_characterization(
            'some_file.pl.archive'
        )

        # Call normalize
        char.normalize(archive, logger)

        # Verify auto-linking succeeded with the cleaned name
        assert len(char.samples) == 1
        assert char.samples[0].reference == mock_stack
        # Verify log mentions the matched name
        logger.info.assert_called()
        call_args = logger.info.call_args[0][0]
        assert '260901B1_BCS' in call_args  # Should mention the matched name after cleanup

    @patch('nomad_inl_base.schema_packages.characterization._extract_sample_name')
    @patch('nomad_inl_base.schema_packages.characterization._find_matching_thin_film_stacks')
    def test_auto_link_with_fallback_sequential_number(self, mock_find, mock_extract):
        """Test auto-linking with fallback cleanup of trailing sequential numbers."""
        # Setup: Extract returns name with trailing sequential number
        mock_extract.return_value = 'Sample_A_002'
        mock_stack = Mock(spec=INLThinFilmStack)
        mock_stack.name = 'Sample_A'

        # Mock find to be called twice: first with full name (no match), then with cleaned name (match)
        mock_find.side_effect = [
            [],  # First call with 'Sample_A_002' - no match
            [(0.95, mock_stack)]  # Second call with 'Sample_A' - match found
        ]

        char, archive, logger = self._create_mock_characterization(
            'some_file.txt'
        )

        # Call normalize
        char.normalize(archive, logger)

        # Verify auto-linking succeeded with the cleaned name
        assert len(char.samples) == 1
        assert char.samples[0].reference == mock_stack
        # Verify log mentions the matched name
        logger.info.assert_called()
        call_args = logger.info.call_args[0][0]
        assert 'Sample_A' in call_args  # Should mention the matched name after cleanup


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """End-to-end integration tests with realistic scenarios."""

    def test_end_to_end_battery_chamber_to_stack(self):
        """Test complete flow: battery chamber file → stack link."""
        # Given: A characterization file with battery chamber naming
        filename = 'PC04_All Signals_LNbO_004 2026.07.16-09.32.33.csv'

        # When: We extract the sample name
        sample_name = _extract_sample_name(filename)

        # Then: We get the correct sample name
        assert sample_name == 'LNbO_004'

    def test_end_to_end_4pp_to_stack(self):
        """Test complete flow: 4pp file → stack link."""
        # Given: A characterization file with 4pp naming
        filename = 'my_sample 4pp.xlsx'

        # When: We extract the sample name
        sample_name = _extract_sample_name(filename)

        # Then: We get the correct sample name
        assert sample_name == 'my_sample'

    def test_various_filenames_consistency(self):
        """Test that different file types with same sample name extract identically."""
        sample_base = 'LNbO_004'

        filenames_variants = [
            f'{sample_base} 4pp.xlsx',
            f'{sample_base} mVs.xlsx',
            f'{sample_base} ED.xlsx',
            f'{sample_base} profile.pdf',
        ]

        extracted_names = [_extract_sample_name(f) for f in filenames_variants]

        # All should extract to the same name
        assert all(name == sample_base for name in extracted_names)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
