"""
Analysis functions for INL characterization measurements.

Each function is decorated with @category so that nomad-analysis
can extract its source and inject it into generated Jupyter notebooks.
All imports **must** be inside the function body so they are captured
when the source is serialized into notebook cells.
"""

from nomad_analysis.utils import category

# ============================================================================
# EQE analysis functions
# ============================================================================


@category('EQE')
def eqe_am15g_spectrum():
    """Return the AM1.5G solar spectrum as a pandas DataFrame (wavelength in nm, irradiance in W/m²/nm)."""
    import numpy as np
    import pandas as pd

    # AM1.5G reference spectrum (ASTM G-173-03)
    # Subset covering 280-1200 nm relevant for EQE calculations
    data = np.array(
        [
            [280, 8.20e-02],
            [290, 5.71e-01],
            [300, 5.98e-01],
            [310, 5.14e-01],
            [320, 1.07e00],
            [330, 6.35e-01],
            [340, 1.34e00],
            [350, 1.04e00],
            [360, 1.26e00],
            [370, 1.23e00],
            [380, 1.21e00],
            [390, 1.14e00],
            [400, 1.51e00],
            [410, 1.67e00],
            [420, 1.62e00],
            [430, 1.61e00],
            [440, 1.78e00],
            [450, 1.75e00],
            [460, 1.75e00],
            [470, 1.72e00],
            [480, 1.68e00],
            [490, 1.70e00],
            [500, 1.67e00],
            [510, 1.63e00],
            [520, 1.64e00],
            [530, 1.58e00],
            [540, 1.55e00],
            [550, 1.53e00],
            [560, 1.50e00],
            [570, 1.46e00],
            [580, 1.43e00],
            [590, 1.38e00],
            [600, 1.40e00],
            [610, 1.36e00],
            [620, 1.37e00],
            [630, 1.34e00],
            [640, 1.31e00],
            [650, 1.28e00],
            [660, 1.26e00],
            [670, 1.24e00],
            [680, 1.19e00],
            [690, 1.18e00],
            [700, 1.17e00],
            [710, 1.13e00],
            [720, 1.07e00],
            [730, 1.07e00],
            [740, 9.51e-01],
            [750, 1.04e00],
            [760, 1.03e00],
            [770, 9.11e-01],
            [780, 9.85e-01],
            [790, 9.28e-01],
            [800, 9.31e-01],
            [810, 9.15e-01],
            [820, 9.07e-01],
            [830, 8.82e-01],
            [840, 8.60e-01],
            [850, 8.68e-01],
            [860, 8.50e-01],
            [870, 7.50e-01],
            [880, 7.53e-01],
            [890, 7.79e-01],
            [900, 6.24e-01],
            [910, 6.52e-01],
            [920, 4.83e-01],
            [930, 7.09e-01],
            [940, 6.01e-01],
            [950, 4.97e-01],
            [960, 4.58e-01],
            [970, 5.83e-01],
            [980, 5.18e-01],
            [990, 5.08e-01],
            [1000, 4.69e-01],
            [1010, 4.57e-01],
            [1020, 4.24e-01],
            [1030, 4.74e-01],
            [1040, 4.32e-01],
            [1050, 3.73e-01],
            [1060, 3.53e-01],
            [1070, 3.79e-01],
            [1080, 2.95e-01],
            [1090, 2.29e-01],
            [1100, 2.68e-01],
            [1110, 3.40e-01],
            [1120, 3.04e-01],
            [1130, 2.64e-01],
            [1140, 2.51e-01],
            [1150, 2.83e-01],
            [1160, 2.61e-01],
            [1170, 2.07e-01],
            [1180, 1.26e-01],
            [1190, 7.47e-02],
            [1200, 1.70e-01],
        ]
    )
    df = pd.DataFrame(data, columns=['wavelength', 'irradiance'])
    df = df.set_index('wavelength')
    return df


@category('EQE')
def eqe_calculate_jsc(wavelength_nm, qe_fraction, am_spectrum=None):
    """
    Calculate short-circuit current density (Jsc) from EQE data.

    Parameters
    ----------
    wavelength_nm : array-like
        Wavelength values in nm.
    qe_fraction : array-like
        Quantum efficiency values as fractions (0–1).
    am_spectrum : DataFrame, optional
        AM1.5G spectrum. If None, uses eqe_am15g_spectrum().

    Returns
    -------
    float
        Jsc in mA/cm².
    """
    import numpy as np
    from scipy import integrate, interpolate

    if am_spectrum is None:
        am_spectrum = eqe_am15g_spectrum()

    wl = np.array(wavelength_nm)
    qe = np.array(qe_fraction)

    # Interpolate EQE onto the AM1.5G wavelength grid
    f_eqe = interpolate.interp1d(wl, qe, bounds_error=False, fill_value=0.0)
    am_wl = am_spectrum.index.values
    am_irr = am_spectrum['irradiance'].values
    eqe_interp = f_eqe(am_wl)

    # Jsc = integral(EQE * AM1.5G / (hc/lambda)) dlambda
    # Simplified: multiply EQE by AM1.5G spectral irradiance / photon energy
    # then integrate using Simpson's rule
    # Using: EQE * AM * lambda / (hc) with proper unit conversion
    q = 1.602176634e-19  # C
    h = 6.62607015e-34  # J·s
    c = 2.99792458e8  # m/s

    photon_flux = am_irr * (am_wl * 1e-9) / (h * c)  # photons/m²/s/nm
    jsc_integrand = eqe_interp * photon_flux * q  # A/m²/nm

    jsc = integrate.simpson(jsc_integrand, x=am_wl) / 10  # mA/cm²
    return jsc


@category('EQE')
def eqe_sigmoid_fit(wavelength_nm, qe_fraction, low_limit=850, high_limit=1100):
    """
    Fit a sigmoid function to EQE data to estimate the bandgap.

    Parameters
    ----------
    wavelength_nm : array-like
        Wavelength in nm.
    qe_fraction : array-like
        EQE values (fraction 0–1).
    low_limit : float
        Lower wavelength bound for fitting (nm).
    high_limit : float
        Upper wavelength bound for fitting (nm).

    Returns
    -------
    dict
        Keys: 'Eg_eV' (bandgap), 'lambda_g' (inflection wavelength),
        'amplitude', 'width', 'popt' (raw fit parameters).
    """
    import numpy as np
    from scipy.optimize import curve_fit

    def sigmoid(x, A, xg, b):
        k = np.log(7 + 4 * np.sqrt(3))
        return A / (1 + np.exp(k * (x - xg) / b))

    wl = np.array(wavelength_nm)
    qe = np.array(qe_fraction)

    mask = (wl >= low_limit) & (wl <= high_limit)
    wl_fit = wl[mask]
    qe_fit = qe[mask]

    if len(wl_fit) < 4:
        return None

    try:
        popt, _ = curve_fit(
            sigmoid,
            wl_fit,
            qe_fit,
            p0=[qe_fit.max(), (low_limit + high_limit) / 2, 50],
            maxfev=10000,
        )
    except RuntimeError:
        return None

    A, xg, b = popt
    Eg = 1239.84193 / xg  # eV

    return {
        'Eg_eV': Eg,
        'lambda_g': xg,
        'amplitude': A,
        'width': b,
        'popt': popt,
    }


@category('EQE')
def eqe_keller_bandgap(wavelength_nm, qe_fraction):
    """
    Estimate the bandgap using the Keller (linear extrapolation) method.

    Transforms EQE data to (ln(1-EQE)*E)^2 vs E, then finds the inflection
    point and extrapolates linearly to the x-axis.

    Parameters
    ----------
    wavelength_nm : array-like
        Wavelength in nm.
    qe_fraction : array-like
        EQE values (fraction 0–1).

    Returns
    -------
    dict or None
        Keys: 'Eg_eV' (bandgap from linear extrapolation),
        'inflection_energy_eV', 'slope', 'intercept'.
    """
    import numpy as np
    from scipy.signal import savgol_filter

    wl = np.array(wavelength_nm, dtype=float)
    qe = np.array(qe_fraction, dtype=float)

    # Convert to energy
    E = 1239.84193 / wl  # eV

    # Remove points where EQE >= 1 or EQE <= 0
    valid = (qe > 0) & (qe < 1)
    E = E[valid]
    qe = qe[valid]

    # Sort by energy
    sort_idx = np.argsort(E)
    E = E[sort_idx]
    qe = qe[sort_idx]

    if len(E) < 15:
        return None

    # Keller transform: y = (ln(1 - EQE) * E)^2
    y = (np.log(1 - qe) * E) ** 2

    # Smooth with Savitzky-Golay filter
    window = min(11, len(y) - 1 if len(y) % 2 == 0 else len(y))
    if window < 5:
        return None
    if window % 2 == 0:
        window -= 1
    y_smooth = savgol_filter(y, window, 3)

    # First derivative
    dy = np.gradient(y_smooth, E)
    # Second derivative
    d2y = np.gradient(dy, E)

    # Find inflection point (where |d2y| is maximized)
    inflection_idx = np.argmax(np.abs(d2y))
    E_inflection = E[inflection_idx]

    # Linear fit around the inflection point
    half_window = max(3, len(E) // 10)
    lo = max(0, inflection_idx - half_window)
    hi = min(len(E), inflection_idx + half_window)

    E_fit = E[lo:hi]
    y_fit = y_smooth[lo:hi]

    if len(E_fit) < 3:
        return None

    coeffs = np.polyfit(E_fit, y_fit, 1)
    slope, intercept = coeffs

    if slope == 0:
        return None

    # x-intercept = -intercept / slope
    Eg = -intercept / slope

    return {
        'Eg_eV': Eg,
        'inflection_energy_eV': E_inflection,
        'slope': slope,
        'intercept': intercept,
    }


@category('EQE')
def eqe_analysis(inputs):
    """
    Run full EQE analysis on NOMAD archive inputs.

    Reads EQE data from each input entry, calculates Jsc, fits sigmoid and
    Keller methods for bandgap estimation, and displays results.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    am_spectrum = eqe_am15g_spectrum()

    results_list = []

    for entry_input in inputs:
        entry = entry_input.reference
        if entry is None:
            continue

        # accessing an attribute forces resolution of the lazy reference proxy
        name = getattr(entry, 'name', 'Unknown')
        wl = np.array(entry.wavelength)
        qe = np.array(entry.quantum_efficiency)

        # Calculate Jsc
        jsc = eqe_calculate_jsc(wl, qe, am_spectrum=am_spectrum)

        # Sigmoid fit for Eg
        sigmoid_result = eqe_sigmoid_fit(wl, qe)
        Eg_sigmoid = sigmoid_result['Eg_eV'] if sigmoid_result else None

        # Keller method for Eg
        keller_result = eqe_keller_bandgap(wl, qe)
        Eg_keller = keller_result['Eg_eV'] if keller_result else None

        results_list.append(
            {
                'Name': name,
                'Jsc (mA/cm²)': round(jsc, 2),
                'Eg sigmoid (eV)': round(Eg_sigmoid, 3) if Eg_sigmoid else None,
                'Eg Keller (eV)': round(Eg_keller, 3) if Eg_keller else None,
            }
        )

        # Plot EQE
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(wl, qe * 100, 'b-', linewidth=1.5)
        ax.set_xlabel('Wavelength (nm)')
        ax.set_ylabel('EQE (%)')
        ax.set_title(f'EQE — {name}')
        ax.grid(True, alpha=0.3)

        # Add secondary x-axis (energy in eV)
        ax2 = ax.secondary_xaxis(
            'top',
            functions=(
                lambda x: 1239.84193 / np.where(x > 0, x, 1),
                lambda x: 1239.84193 / np.where(x > 0, x, 1),
            ),
        )
        ax2.set_xlabel('Energy (eV)')

        plt.tight_layout()
        plt.show()

        print(f'{name}: Jsc = {jsc:.2f} mA/cm²', end='')
        if Eg_sigmoid:
            print(f', Eg(sigmoid) = {Eg_sigmoid:.3f} eV', end='')
        if Eg_keller:
            print(f', Eg(Keller) = {Eg_keller:.3f} eV', end='')
        print()

    if results_list:
        df = pd.DataFrame(results_list)
        print('\nSummary:')
        print(df.to_string(index=False))


# ============================================================================
# Solar Cell IV analysis functions
# ============================================================================


@category('SolarCell')
def solar_cell_iv_analysis(inputs):
    """
    Run Solar Cell IV analysis on NOMAD archive inputs.

    Reads IV curve data and extracted parameters, plots JV curves,
    and displays summary statistics.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    all_results = []

    for entry_input in inputs:
        entry = entry_input.reference
        if entry is None:
            continue

        # accessing an attribute forces resolution of the lazy reference proxy
        name = getattr(entry, 'name', 'Unknown')

        # Plot all IV curves for this entry
        if hasattr(entry, 'iv_curves') and entry.iv_curves:
            fig, ax = plt.subplots(figsize=(8, 5))
            for curve in entry.iv_curves:
                if curve.voltage is not None and curve.current is not None:
                    v = np.array(curve.voltage)
                    i_ma = np.array(curve.current) * 1000
                    label = curve.measurement_name or 'Curve'
                    ax.plot(v, i_ma, linewidth=1.2, label=label)
            ax.set_xlabel('Voltage (V)')
            ax.set_ylabel('Current (mA)')
            ax.set_title(f'JV Curves — {name}')
            ax.axhline(0, color='gray', linewidth=0.5)
            ax.axvline(0, color='gray', linewidth=0.5)
            ax.legend(fontsize=8, loc='best')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()

        # Collect results
        if hasattr(entry, 'results') and entry.results:
            for r in entry.results:
                all_results.append(
                    {
                        'Entry': name,
                        'Measurement': r.measurement_name or '',
                        'Voc (V)': round(float(r.voc), 3)
                        if r.voc is not None
                        else None,
                        'Jsc (mA/cm²)': round(float(r.jsc), 2)
                        if r.jsc is not None
                        else None,
                        'FF': round(float(r.fill_factor), 3)
                        if r.fill_factor is not None
                        else None,
                        'Eff': round(float(r.efficiency), 4)
                        if r.efficiency is not None
                        else None,
                    }
                )

    if all_results:
        df = pd.DataFrame(all_results)
        print('\nSolar Cell IV Summary:')
        print(df.to_string(index=False))

        # Box plots of key parameters
        fig, axes = plt.subplots(1, 4, figsize=(14, 4))
        for ax, col in zip(axes, ['Voc (V)', 'Jsc (mA/cm²)', 'FF', 'Eff']):
            vals = df[col].dropna().values
            if len(vals) > 0:
                ax.boxplot(vals, widths=0.5)
                ax.set_title(col)
                ax.grid(True, alpha=0.3)
        plt.suptitle('Parameter Distribution')
        plt.tight_layout()
        plt.show()


# ============================================================================
# GDOES analysis functions
# ============================================================================


@category('GDOES')
def gdoes_find_half_max_crossings(depth, concentration, depth_unit='µm'):
    """
    Compute the FWHM boundaries for an element concentration profile.

    Parameters
    ----------
    depth : array-like
        Depth values.
    concentration : array-like
        Concentration values (mol %).
    depth_unit : str
        Unit label for depth.

    Returns
    -------
    dict or None
        FWHM results with Max, 50%, boundary positions, and thickness.
    """
    import numpy as np

    y = np.array(concentration, dtype=float)
    x = np.array(depth, dtype=float)

    y_max = np.nanmax(y)
    if not np.isfinite(y_max) or y_max == 0:
        return None

    half_max = y_max / 2.0

    # Find crossings of the half-max level
    above = y >= half_max
    crossings = np.where(np.diff(above.astype(int)))[0]

    if len(crossings) < 2:
        return None

    # Interpolate crossing positions
    def interp_crossing(idx):
        x0, x1 = x[idx], x[idx + 1]
        y0, y1 = y[idx], y[idx + 1]
        if y1 == y0:
            return x0
        return x0 + (half_max - y0) * (x1 - x0) / (y1 - y0)

    x1 = interp_crossing(crossings[0])
    x2 = interp_crossing(crossings[-1])
    y1 = y[crossings[0]]
    y2 = y[crossings[-1]]

    return {
        'Max': round(y_max, 4),
        '50%': round(half_max, 4),
        'y1': round(float(y1), 4),
        'y2': round(float(y2), 4),
        'X1': round(float(x1), 4),
        'X2': round(float(x2), 4),
        f'thickness [{depth_unit}]': round(abs(x2 - x1), 4),
    }


@category('GDOES')
def gdoes_analysis(inputs):
    """
    Run GDOES depth-profile analysis on NOMAD archive inputs.

    Reads depth and element concentration data, plots depth profiles,
    and computes FWHM-based layer thicknesses.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    COLORS = [
        '#1f77b4',
        '#ff7f0e',
        '#2ca02c',
        '#d62728',
        '#9467bd',
        '#8c564b',
        '#e377c2',
        '#7f7f7f',
        '#bcbd22',
        '#17becf',
        '#aec7e8',
        '#ffbb78',
        '#98df8a',
        '#ff9896',
        '#c5b0d5',
    ]

    for entry_input in inputs:
        entry = entry_input.reference
        if entry is None:
            continue

        # accessing an attribute forces resolution of the lazy reference proxy
        name = getattr(entry, 'name', 'Unknown')
        depth = np.array(entry.depth) if entry.depth is not None else None

        if depth is None or not entry.element_profiles:
            print(f'Skipping {name}: no data')
            continue

        sort_idx = np.argsort(depth)
        depth = depth[sort_idx]

        # Plot depth profile
        fig, ax = plt.subplots(figsize=(12, 6))
        results = {}

        for i, profile in enumerate(entry.element_profiles):
            col = profile.element_name or f'Element {i}'
            conc = np.array(profile.concentration)[sort_idx]
            color = COLORS[i % len(COLORS)]
            ax.plot(depth, conc, label=col, color=color, linewidth=1.3)

            # FWHM calculation
            res = gdoes_find_half_max_crossings(depth, conc)
            if res is not None:
                results[col] = res
            else:
                y_max = np.nanmax(conc)
                results[col] = {
                    'Max': round(y_max, 4) if np.isfinite(y_max) else y_max,
                    '50%': round(y_max / 2, 4) if np.isfinite(y_max) else y_max,
                    'y1': None,
                    'y2': None,
                    'X1': None,
                    'X2': None,
                    'thickness [µm]': None,
                }

        ax.set_xlabel('Depth (µm)')
        ax.set_ylabel('Mol Conc. (%)')
        ax.set_title(name)
        ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=9, frameon=True)
        ax.set_xlim(depth.min() - 0.05, depth.max() + 0.05)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

        # Display FWHM results
        if results:
            df_results = pd.DataFrame(results).T
            df_results.index.name = 'Element'
            print(f'\nFWHM Results — {name}:')
            print(df_results.to_string())
            print()


# ============================================================================
# XRD analysis functions
# ============================================================================


@category('XRD')
def xrd_plot_intensity_two_theta(entry, peak_indices=None) -> None:
    """
    Generates a 2D plot of intensity vs 2θ with linear x and y axis.

    Args:
        entry (EntryData): A NOMAD entry data.
        peak_indices (np.array): Indices of peaks found in the intensity data.
    """
    import plotly.express as px

    intensity = entry.results[0].intensity.magnitude
    two_theta = entry.results[0].two_theta.magnitude

    line_linear = px.line(
        x=two_theta,
        y=intensity,
        labels={
            'x': '2θ (°)',
            'y': 'Intensity',
        },
        height=600,
        width=800,
        title='Intensity vs 2θ (linear scale)',
    )
    if peak_indices is not None and len(peak_indices) > 0:
        line_linear.add_scatter(
            x=two_theta[peak_indices],
            y=intensity[peak_indices],
            mode='markers',
            marker=dict(size=8, color='red', symbol='cross'),
            name='Peaks',
        )
    line_linear.show()


@category('XRD')
def xrd_plot_logy_intensity_two_theta(entry, peak_indices=None) -> None:
    """
    Generates a 2D plot of intensity vs 2θ with linear x and log y axis.

    Args:
        entry (EntryData): A NOMAD entry data.
        peak_indices (np.array): Indices of peaks found in the intensity data.
    """
    import plotly.express as px

    intensity = entry.results[0].intensity.magnitude
    two_theta = entry.results[0].two_theta.magnitude

    line_log = px.line(
        x=two_theta,
        y=intensity,
        log_y=True,
        labels={
            'x': '2θ (°)',
            'y': 'Intensity',
        },
        height=600,
        width=800,
        title='Intensity vs 2θ (log scale)',
    )
    if peak_indices is not None and len(peak_indices) > 0:
        line_log.add_scatter(
            x=two_theta[peak_indices],
            y=intensity[peak_indices],
            mode='markers',
            marker=dict(size=8, color='red', symbol='cross'),
            name='Peaks',
        )
    line_log.show()


@category('XRD')
def xrd_find_peaks(entry, options: dict = None) -> dict:
    """
    Finds the peaks in the intensity vs 2θ plot.

    Args:
        entry (EntryData): A NOMAD entry data.
        options (dict): Options for the peak finding algorithm
            `scipy.signal.find_peaks`.

    Returns:
        dict: Peaks found in the intensity vs 2θ plot.
    """
    from scipy.signal import find_peaks

    intensity = entry.results[0].intensity.magnitude
    two_theta = entry.results[0].two_theta.magnitude

    if options:
        peak_indices, _ = find_peaks(intensity, **options)
    else:
        peak_indices, _ = find_peaks(intensity)

    peaks_intensity = intensity[peak_indices]
    peaks_two_theta = two_theta[peak_indices]

    peaks = {
        'peaks': {
            'intensity': peaks_intensity.tolist(),
            'two_theta': peaks_two_theta.tolist(),
        }
    }

    return peaks, peak_indices


@category('XRD')
def xrd_save_analysis_results(
    results: dict, file_name: str = 'tmp_analysis_results.json'
):
    """
    Saves the analysis results as a json file.

    Args:
        results (dict): Analysis results.
        file_name (str): Name of the file to save the results.
    """
    import json

    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(results, f)


@category('XRD')
def xrd_conduct_analysis(
    entry,
    options: dict = None,
    plot: bool = True,
) -> None:
    """
    Conducts XRD analysis on the given archive data. Also saves the analysis results as
    a json file which can be used to fill `analysis_results` section.

    Args:
        entry (EntryData): A NOMAD entry data.
        plot (bool): If True, plots the intensity vs 2θ plot.
    """
    if options is None:
        options = {
            'height': 20,
            'threshold': 30,
            'distance': 1,
        }
    peaks, peak_indices = xrd_find_peaks(entry, options=options)
    if plot:
        xrd_plot_intensity_two_theta(entry, peak_indices)
        xrd_plot_logy_intensity_two_theta(entry, peak_indices)

    results = peaks

    xrd_save_analysis_results(results)


@category('XRD')
def xrd_voila_analysis(input_data) -> None:  # noqa: PLR0915
    """
    Use ipywidgets to create an interactive XRD analysis. These widgets can be rendered
    using Voila.
    """
    ## Voila specific code

    import collections

    import ipywidgets as widgets
    import pandas as pd
    from IPython.display import clear_output, display

    def get_input_entry_names(input_data: list) -> list:
        """
        Gets the names of the input entries.

        Args:
            input_data (list): List of input data.

        Returns:
            list: Names of the input entries.
        """
        from nomad_measurements.xrd.schema import ELNXRayDiffraction

        names = []
        for idx in range(len(input_data)):
            # accessing `.reference.name` first forces resolution of the lazy
            # reference proxy returned by the API search; without this, the
            # `isinstance` check below can spuriously fail on the unresolved proxy
            entry_reference = input_data[idx].reference
            entry_name = input_data[idx].reference.name  # noqa: F841
            if isinstance(entry_reference, ELNXRayDiffraction):
                names.append(entry_reference.name)
        return names

    available_entries = get_input_entry_names(input_data)
    dropdown = widgets.Dropdown(options=available_entries)
    find_peak_parameters = [
        widgets.FloatText(
            description='Height:',
            value=10,
            readout_format='.1f',
            tooltip='Required height of peaks.',
        ),
        widgets.FloatText(
            description='Threshold:',
            value=10,
            readout_format='.1f',
            tooltip='Required threshold of peaks, the vertical distance'
            'to its neighboring samples.',
        ),
        widgets.FloatText(
            description='Distance:',
            value=1,
            readout_format='.1f',
            tooltip='Required minimal horizontal distance (>= 1) in samples'
            'between neighboring peaks.',
        ),
    ]
    find_peak_button = widgets.Button(
        description='Find peaks',
        button_style='primary',
    )
    export_results_button = widgets.Button(
        description='Export results',
        button_style='primary',
    )
    export_csv_button = widgets.Button(
        description='Export CSV',
        button_style='primary',
    )

    no_input_alert = widgets.HTML(
        '<p style="color:red;">No input entry of class`ELNXRayDiffraction` found.</p>'
    )
    no_input_alert.layout.visibility = 'hidden'
    no_peak_alert = widgets.HTML(
        '<p style="color:red;">No peaks found.'
        'Change the parameters for peak finding algorithm</p>'
    )
    no_peak_alert.layout.visibility = 'hidden'
    out = widgets.Output()

    display_panel = widgets.VBox(
        [
            widgets.HTML('<h1>XRD Analysis</h1>'),
            widgets.Label(value='Select input entry:'),
            dropdown,
            widgets.VBox(
                [
                    widgets.HTML(
                        '<h2>Locate the intensity peaks</h2>\
                        Select the parameters for peak finding algorithm:'
                    ),
                    widgets.HBox(find_peak_parameters),
                    widgets.HTML('<br>'),
                    widgets.HBox(
                        [
                            find_peak_button,
                            export_results_button,
                        ]
                    ),
                ]
            ),
            no_peak_alert,
            no_input_alert,
            export_csv_button,
            out,
        ]
    )

    results = collections.defaultdict(None)
    entry_name = dropdown.value
    entry_index = get_input_entry_names(input_data).index(entry_name)
    input_data_entry = input_data[entry_index].reference
    with out:
        xrd_plot_logy_intensity_two_theta(input_data_entry, None)
        clear_output(wait=True)

    def on_change_dropdown(change):
        """
        Event handler for the dropdown change.
        """
        entry_name = dropdown.value
        entry_index = get_input_entry_names(input_data).index(entry_name)
        input_data_entry = input_data[entry_index].reference
        with out:
            xrd_plot_logy_intensity_two_theta(input_data_entry, None)
            clear_output(wait=True)

    def on_click_find_peaks(button):
        """
        Event handler for the find peaks button click.
        """
        entry_name = dropdown.value
        entry_index = get_input_entry_names(input_data).index(entry_name)
        input_data_entry = input_data[entry_index].reference
        find_peak_parameters[2].value = max(find_peak_parameters[2].value, 1)
        options = {
            'height': find_peak_parameters[0].value,
            'threshold': find_peak_parameters[1].value,
            'distance': find_peak_parameters[2].value,
        }
        peaks, peak_indices = xrd_find_peaks(
            entry=input_data_entry,
            options=options,
        )
        peaks_table = pd.DataFrame(
            {
                '2θ (°)': peaks['peaks']['two_theta'],
                'Intensity': peaks['peaks']['intensity'],
            }
        )
        peaks_table.set_index('2θ (°)', inplace=True)
        if not peaks_table.empty:
            results[entry_name] = peaks

        with out:
            print(f'{len(peaks_table)} peak(s) found.')
            xrd_plot_logy_intensity_two_theta(input_data_entry, peak_indices)
            if not peaks_table.empty:
                display(peaks_table)
                export_results_button.disabled = False
            clear_output(wait=True)

    def on_click_export_results(button):
        """
        Event handler for the export results button click.
        """
        xrd_save_analysis_results(results)
        button.disabled = True

    def on_click_download_csv(button):
        """
        Event handler for the download as CSV button click.
        """
        entry_name = dropdown.value
        entry_index = get_input_entry_names(input_data).index(entry_name)
        input_data_entry = input_data[entry_index].reference
        intensity = input_data_entry.results[0].intensity.magnitude
        two_theta = input_data_entry.results[0].two_theta.magnitude
        if input_data_entry:
            peaks_table = pd.DataFrame(
                {
                    '2θ (°)': two_theta,
                    'Intensity': intensity,
                }
            )
            peaks_table.set_index('2θ (°)', inplace=True)
            peaks_table.to_csv(
                f'tmp_{entry_name.replace(" ", "_")}_intensity_2theta.csv'
            )

    if not available_entries:
        no_input_alert.layout.visibility = 'visible'
        dropdown.disabled = True
        find_peak_button.disabled = True
        export_csv_button.disabled = True

    export_results_button.disabled = True

    dropdown.observe(on_change_dropdown, names='value')
    find_peak_button.on_click(on_click_find_peaks)
    export_csv_button.on_click(on_click_download_csv)
    export_results_button.on_click(on_click_export_results)

    display(display_panel)


# ============================================================================
# Advanced XRD analysis functions (notebook-based pipeline)
# ============================================================================


@category('XRD')
def xrd_background_correction(x, y, bg_regions=None, poly_degree=3):
    """
    Subtract polynomial background from XRD data and normalize to [0, 1].

    Parameters
    ----------
    x : array-like
        2θ values in degrees.
    y : array-like
        Raw intensity values.
    bg_regions : list of (float, float), optional
        List of (min_2theta, max_2theta) regions to use for background
        estimation.  If None, the first and last 5 % of the angular range
        are used.
    poly_degree : int
        Degree of the polynomial fit (default 3).

    Returns
    -------
    tuple (x_arr, y_corrected, y_background)
        x_arr          — original 2θ array
        y_corrected    — background-subtracted, normalised intensity [0, 1]
        y_background   — evaluated background polynomial
    """
    import numpy as np

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    if bg_regions is None:
        span = x[-1] - x[0]
        bg_regions = [
            (x[0], x[0] + 0.05 * span),
            (x[-1] - 0.05 * span, x[-1]),
        ]

    bg_mask = np.zeros(len(x), dtype=bool)
    for lo, hi in bg_regions:
        bg_mask |= (x >= lo) & (x <= hi)

    if bg_mask.sum() < poly_degree + 1:
        bg_mask = np.ones(len(x), dtype=bool)

    coeffs = np.polyfit(x[bg_mask], y[bg_mask], poly_degree)
    y_background = np.polyval(coeffs, x)
    y_corrected = np.clip(y - y_background, 0, None)

    y_max = y_corrected.max()
    if y_max > 0:
        y_corrected = y_corrected / y_max

    return x, y_corrected, y_background


@category('XRD')
def xrd_find_and_fit_peaks(x, y, min_rel_height=0.05, peak_prominence=0.05):
    """
    Detect and fit XRD peaks using PseudoVoigt profiles via lmfit.

    The function smooths the pattern with a Savitzky-Golay filter, detects
    candidate peaks with ``scipy.signal.find_peaks``, then fits each peak
    individually in a ±1.5° window with a PseudoVoigt + Constant model.

    Parameters
    ----------
    x : array-like
        2θ values in degrees (background-corrected, normalised).
    y : array-like
        Intensity values.
    min_rel_height : float
        Minimum peak height as a fraction of the maximum intensity.
    peak_prominence : float
        Minimum prominence as a fraction of the maximum intensity.

    Returns
    -------
    pandas.DataFrame
        One row per fitted peak with columns:
        ``center``, ``fwhm``, ``height``, ``amplitude``, ``eta``, ``sigma``.
    """
    import numpy as np
    import pandas as pd
    from lmfit.models import ConstantModel, PseudoVoigtModel
    from scipy.signal import find_peaks, savgol_filter

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    win = max(5, min(11, (len(y) // 10) * 2 + 1))
    if win % 2 == 0:
        win += 1
    y_smooth = savgol_filter(y, window_length=win, polyorder=3)

    y_max = y_smooth.max() if y_smooth.max() > 0 else 1.0
    peak_indices, _ = find_peaks(
        y_smooth,
        height=min_rel_height * y_max,
        prominence=peak_prominence * y_max,
    )

    dx = (x[-1] - x[0]) / max(len(x) - 1, 1)
    results = []
    for idx in peak_indices:
        center_guess = x[idx]
        mask = (x >= center_guess - 1.5) & (x <= center_guess + 1.5)
        if mask.sum() < 5:
            continue
        x_win = x[mask]
        y_win = y[mask]

        try:
            model = PseudoVoigtModel() + ConstantModel()
            params = model.make_params(
                amplitude=dict(value=float(y_win.max()), min=0),
                center=dict(
                    value=center_guess,
                    min=center_guess - 1.0,
                    max=center_guess + 1.0,
                ),
                sigma=dict(value=0.1, min=0.01, max=2.0),
                fraction=dict(value=0.5, min=0.0, max=1.0),
                c=dict(value=float(y_win.min()), min=0),
            )
            fit = model.fit(y_win, params, x=x_win)
            fwhm = float(fit.params['fwhm'].value)
            if not (0.01 <= fwhm <= 2.0):
                continue
            results.append(
                {
                    'center': round(float(fit.params['center'].value), 4),
                    'fwhm': round(fwhm, 4),
                    'height': round(float(fit.params['height'].value), 4),
                    'amplitude': round(float(fit.params['amplitude'].value), 4),
                    'eta': round(float(fit.params['fraction'].value), 4),
                    'sigma': round(float(fit.params['sigma'].value), 4),
                }
            )
        except Exception:
            results.append(
                {
                    'center': round(float(center_guess), 4),
                    'fwhm': round(dx * 3, 4),
                    'height': round(float(y[idx]), 4),
                    'amplitude': round(float(y[idx]), 4),
                    'eta': 0.5,
                    'sigma': round(dx * 1.5, 4),
                }
            )

    return pd.DataFrame(results)


@category('XRD')
def xrd_calculate_scherrer(fwhm_deg, theta_deg, K=0.9, wavelength=1.5406):
    """
    Calculate crystallite size using the Scherrer equation.

    .. math::
        D = \\frac{K \\lambda}{\\beta \\cos\\theta}

    Parameters
    ----------
    fwhm_deg : float
        Full width at half maximum in degrees (β).
    theta_deg : float
        Peak position as 2θ in degrees (will be halved to obtain θ).
    K : float
        Scherrer constant (default 0.9).
    wavelength : float
        X-ray wavelength in Å (default 1.5406 Å for Cu Kα).

    Returns
    -------
    float
        Crystallite size in nm, or NaN if inputs are unphysical.
    """
    import math

    fwhm_rad = math.radians(fwhm_deg)
    theta_rad = math.radians(theta_deg / 2.0)
    cos_theta = math.cos(theta_rad)
    if fwhm_rad <= 0 or cos_theta <= 0:
        return float('nan')
    size_angstrom = (K * wavelength) / (fwhm_rad * cos_theta)
    return size_angstrom / 10.0  # Å → nm


@category('XRD')
def xrd_parse_reference_rtf(content_str):
    """
    Parse an ICDD PDF reference card from RTF file content.

    Extracts the "Peak list" table into a DataFrame with columns:
    ``No.``, ``h``, ``k``, ``l``, ``d [A]``, ``2Theta[deg]``, ``I [%]``,
    and a derived ``hkl`` column (e.g. ``'(101)'``).

    Parameters
    ----------
    content_str : bytes or str
        Raw RTF file content.

    Returns
    -------
    pandas.DataFrame or None
        Reference peaks, or None if parsing fails.
    """
    import re

    import pandas as pd
    from striprtf.striprtf import rtf_to_text

    if isinstance(content_str, (bytes, memoryview)):
        content_str = bytes(content_str).decode('utf-8', errors='replace')

    plain = rtf_to_text(content_str)

    header_re = re.compile(r'No\.?\s+h\s+k\s+l', re.IGNORECASE)
    data_re = re.compile(
        r'^\s*(\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)'
    )

    rows = []
    in_table = False
    for line in plain.splitlines():
        if header_re.search(line):
            in_table = True
            continue
        if in_table:
            m = data_re.match(line)
            if m:
                rows.append(
                    {
                        'No.': int(m.group(1)),
                        'h': int(m.group(2)),
                        'k': int(m.group(3)),
                        'l': int(m.group(4)),
                        'd [A]': float(m.group(5)),
                        '2Theta[deg]': float(m.group(6)),
                        'I [%]': float(m.group(7)),
                    }
                )
            elif rows:
                break

    if not rows:
        return None

    df = pd.DataFrame(rows)
    df['hkl'] = df.apply(
        lambda r: f"({int(r['h'])}{int(r['k'])}{int(r['l'])})", axis=1
    )
    return df


@category('XRD')
def xrd_match_and_analyze(samples_dict, references_dict, tolerance=0.3, scherrer_k=0.9):
    """
    Match experimental peaks to reference phases and compute crystallographic metrics.

    For each sample the function:

    1. Matches fitted peaks to every reference phase using ``pd.merge_asof``
       (nearest 2θ within *tolerance* degrees).
    2. Calculates **crystallite size** via :func:`xrd_calculate_scherrer` using
       the per-sample wavelength stored in *samples_dict* (read from
       ``entry.xrd_settings.source.kalpha_one``) and *scherrer_k*.
    3. Calculates **Texture Coefficient** TC = Rᵢ / mean(Rᵢ), where
       Rᵢ = I_exp / I_ref.

    Parameters
    ----------
    samples_dict : dict
        ``{sample_name: {'two_theta': array, 'intensity': array,
                         'peaks': DataFrame, 'wavelength': float}}``
    references_dict : dict
        ``{phase_name: DataFrame}`` — as returned by
        :func:`xrd_parse_reference_rtf`.
    tolerance : float
        Maximum 2θ separation (°) for a match.
    scherrer_k : float
        Scherrer constant K (default 0.9).

    Returns
    -------
    dict
        ``{sample_name: {'matches': DataFrame, 'summary': dict}}``
        Summary keys: ``Avg_Crystallite_Size_nm``, ``Max_TC``,
        ``Preferred_hkl``.
    """
    import numpy as np
    import pandas as pd

    analysis_results = {}

    for sample_name, sample_data in samples_dict.items():
        peak_df = sample_data.get('peaks')
        if peak_df is None or peak_df.empty:
            continue

        wavelength = sample_data.get('wavelength', 1.5406)
        exp_sorted = peak_df.sort_values('center').reset_index(drop=True)
        phase_matches = []

        for phase_name, ref_df in references_dict.items():
            ref_sorted = (
                ref_df.sort_values('2Theta[deg]')
                .reset_index(drop=True)
            )
            merged = pd.merge_asof(
                exp_sorted.rename(columns={'center': '2Theta_exp'}),
                ref_sorted[['2Theta[deg]', 'I [%]', 'hkl']].rename(
                    columns={'2Theta[deg]': '2Theta_ref', 'I [%]': 'I_ref'}
                ),
                left_on='2Theta_exp',
                right_on='2Theta_ref',
                tolerance=tolerance,
                direction='nearest',
            )
            merged = merged.dropna(subset=['2Theta_ref']).copy()
            merged['phase'] = phase_name

            merged['crystallite_size_nm'] = merged.apply(
                lambda r: xrd_calculate_scherrer(
                    r['fwhm'], r['2Theta_exp'], K=scherrer_k, wavelength=wavelength
                ),
                axis=1,
            )
            merged['Ri'] = np.where(
                merged['I_ref'] > 0,
                merged['height'] / merged['I_ref'],
                np.nan,
            )
            phase_matches.append(merged)

        if not phase_matches:
            continue

        matches_df = pd.concat(phase_matches, ignore_index=True)

        tc_frames = []
        for _, group in matches_df.groupby('phase'):
            mean_ri = group['Ri'].mean()
            tc = (group['Ri'] / mean_ri) if (mean_ri and mean_ri > 0) else np.nan
            tc_frames.append(group.assign(TC=tc))
        matches_df = pd.concat(tc_frames, ignore_index=True) if tc_frames else matches_df

        avg_size = float(matches_df['crystallite_size_nm'].dropna().mean())
        if 'TC' in matches_df.columns and not matches_df['TC'].isna().all():
            max_idx = matches_df['TC'].idxmax()
            max_tc = float(matches_df.loc[max_idx, 'TC'])
            preferred_hkl = matches_df.loc[max_idx, 'hkl']
        else:
            max_tc = float('nan')
            preferred_hkl = 'N/A'

        analysis_results[sample_name] = {
            'matches': matches_df,
            'summary': {
                'Avg_Crystallite_Size_nm': round(avg_size, 2),
                'Max_TC': round(max_tc, 3) if not np.isnan(max_tc) else None,
                'Preferred_hkl': preferred_hkl,
            },
        }

    return analysis_results


@category('XRD')
def xrd_plot_stacked(samples_dict, references_dict=None, reference_peak_scale=0.15):
    """
    Create an interactive stacked XRD patterns plot using Plotly.

    Each sample pattern is offset vertically by a constant step.
    Reference peak positions (if provided) are shown as vertical sticks
    beneath the bottom pattern.

    Parameters
    ----------
    samples_dict : dict
        ``{sample_name: {'two_theta': array, 'intensity': array}}``
    references_dict : dict, optional
        ``{phase_name: DataFrame}`` — from :func:`xrd_parse_reference_rtf`.
    reference_peak_scale : float
        Height of reference peak sticks relative to the stacking step.
    """
    import plotly.graph_objects as go

    fig = go.Figure()
    n = len(samples_dict)
    offset_step = 1.2

    for i, (name, data) in enumerate(samples_dict.items()):
        hue = int(i * 360 / max(n, 1))
        color = f'hsl({hue},70%,50%)'
        fig.add_trace(
            go.Scatter(
                x=data['two_theta'],
                y=data['intensity'] + i * offset_step,
                mode='lines',
                name=name,
                line=dict(color=color, width=1.5),
            )
        )

    if references_dict:
        stub_colors = [
            'rgba(0,0,0,0.55)',
            'rgba(200,0,0,0.55)',
            'rgba(0,0,200,0.55)',
            'rgba(0,150,0,0.55)',
        ]
        for j, (phase_name, ref_df) in enumerate(references_dict.items()):
            color = stub_colors[j % len(stub_colors)]
            stick_top = -0.05
            for _, row in ref_df.iterrows():
                stick_h = row['I [%]'] / 100.0 * reference_peak_scale
                fig.add_shape(
                    type='line',
                    x0=row['2Theta[deg]'],
                    x1=row['2Theta[deg]'],
                    y0=stick_top - stick_h,
                    y1=stick_top,
                    line=dict(color=color, width=1),
                )
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode='lines',
                    name=phase_name,
                    line=dict(color=color, dash='dot'),
                )
            )

    fig.update_layout(
        title='Stacked XRD Patterns',
        xaxis_title='2θ (°)',
        yaxis_title='Normalised intensity (offset)',
        height=600,
        showlegend=True,
    )
    fig.show()


@category('XRD')
def xrd_plot_single_pattern(samples_dict, sample_name, references_dict=None, peak_df=None):
    """
    Plot a single XRD pattern with fitted peak markers and reference lines.

    Parameters
    ----------
    samples_dict : dict
        Full samples dictionary.
    sample_name : str
        Key in *samples_dict* to plot.
    references_dict : dict, optional
        Reference phases dictionary.
    peak_df : pandas.DataFrame, optional
        Fitted peaks (from :func:`xrd_find_and_fit_peaks`).  If None, uses
        ``samples_dict[sample_name]['peaks']``.
    """
    import plotly.graph_objects as go

    data = samples_dict.get(sample_name)
    if data is None:
        print(f'Sample "{sample_name}" not found.')
        return

    if peak_df is None:
        peak_df = data.get('peaks')

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data['two_theta'],
            y=data['intensity'],
            mode='lines',
            name=sample_name,
            line=dict(color='steelblue', width=1.5),
        )
    )

    if peak_df is not None and not peak_df.empty:
        for _, row in peak_df.iterrows():
            fig.add_vline(
                x=row['center'],
                line=dict(color='red', dash='dash', width=1),
                annotation_text=f"{row['center']:.2f}°",
                annotation_font_size=9,
            )

    if references_dict:
        ref_colors = [
            'rgba(0,150,0,0.75)',
            'rgba(150,0,150,0.75)',
            'rgba(200,100,0,0.75)',
        ]
        for j, (phase_name, ref_df) in enumerate(references_dict.items()):
            color = ref_colors[j % len(ref_colors)]
            for _, row in ref_df.iterrows():
                fig.add_vline(
                    x=row['2Theta[deg]'],
                    line=dict(color=color, dash='dot', width=0.8),
                )
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode='lines',
                    name=phase_name,
                    line=dict(color=color, dash='dot'),
                )
            )

    fig.update_layout(
        title=f'XRD Pattern — {sample_name}',
        xaxis_title='2θ (°)',
        yaxis_title='Normalised intensity',
        height=500,
    )
    fig.show()


@category('XRD')
def xrd_plot_tc(analysis_results):
    """
    Interactive grouped bar chart of Texture Coefficient (TC) per (hkl) per sample.

    A dashed horizontal line at TC = 1 marks the random-texture reference.

    Parameters
    ----------
    analysis_results : dict
        Output of :func:`xrd_match_and_analyze`.
    """
    import plotly.graph_objects as go

    fig = go.Figure()
    for sample_name, result in analysis_results.items():
        matches = result.get('matches')
        if matches is None or 'TC' not in matches.columns:
            continue
        tc_data = matches.dropna(subset=['TC', 'hkl'])
        if tc_data.empty:
            continue
        fig.add_trace(
            go.Bar(
                name=sample_name,
                x=tc_data['hkl'],
                y=tc_data['TC'],
                text=[f'{v:.2f}' for v in tc_data['TC']],
                textposition='outside',
            )
        )

    fig.add_hline(
        y=1.0,
        line=dict(color='black', dash='dash', width=1),
        annotation_text='TC = 1 (random texture)',
    )
    fig.update_layout(
        title='Texture Coefficient by (hkl)',
        xaxis_title='(hkl)',
        yaxis_title='Texture Coefficient',
        barmode='group',
        height=500,
    )
    fig.show()


@category('XRD')
def xrd_plot_crystallite_size(analysis_results):
    """
    Interactive grouped bar chart of Scherrer crystallite size (nm) per (hkl) per sample.

    Parameters
    ----------
    analysis_results : dict
        Output of :func:`xrd_match_and_analyze`.
    """
    import plotly.graph_objects as go

    fig = go.Figure()
    for sample_name, result in analysis_results.items():
        matches = result.get('matches')
        if matches is None or 'crystallite_size_nm' not in matches.columns:
            continue
        size_data = matches.dropna(subset=['crystallite_size_nm', 'hkl'])
        if size_data.empty:
            continue
        fig.add_trace(
            go.Bar(
                name=sample_name,
                x=size_data['hkl'],
                y=size_data['crystallite_size_nm'],
                text=[f'{v:.1f}' for v in size_data['crystallite_size_nm']],
                textposition='outside',
            )
        )

    fig.update_layout(
        title='Crystallite Size by (hkl)',
        xaxis_title='(hkl)',
        yaxis_title='Crystallite size (nm)',
        barmode='group',
        height=500,
    )
    fig.show()


@category('XRD')
def xrd_full_analysis(inputs, reference_contents=None, scherrer_k=0.9, tolerance=0.3):
    """
    Run the full advanced XRD analysis pipeline on NOMAD archive inputs.

    Steps:

    1. Load 2θ / intensity data from each ``ELNXRayDiffraction`` input entry.
       The X-ray wavelength is read from
       ``entry.xrd_settings.source.kalpha_one`` (Cu Kα default: 1.5406 Å).
    2. Apply polynomial background correction and normalise.
    3. Detect and fit peaks with PseudoVoigt profiles.
    4. If *reference_contents* is provided, parse each RTF reference card,
       match experimental peaks, and compute crystallite size (Scherrer) and
       Texture Coefficient.
    5. Display stacked pattern plot, per-sample pattern plots, and (when
       references are available) TC and crystallite-size bar charts.

    Parameters
    ----------
    inputs : list
        ``analysis.inputs`` — list of ``SectionReference`` objects from the
        NOMAD JupyterAnalysis entry.
    reference_contents : dict, optional
        ``{phase_name: str}`` mapping phase names to raw RTF file content.
        Populated by the reference upload widget cell above this one.
    scherrer_k : float
        Scherrer constant K (default 0.9). Set via
        ``analysis.scherrer_k_factor`` on the analysis entry.
    tolerance : float
        Maximum 2θ separation (°) for peak-to-reference matching (default 0.3).
        Set via ``analysis.peak_matching_tolerance`` on the analysis entry.
    """
    import numpy as np
    import pandas as pd
    from nomad_measurements.xrd.schema import ELNXRayDiffraction

    samples_dict = {}
    for entry_input in inputs:
        entry = entry_input.reference
        if entry is None:
            continue
        # Force proxy resolution before isinstance check
        name = entry.name
        if not isinstance(entry, ELNXRayDiffraction):
            print(f'Skipping "{name}" — not an ELNXRayDiffraction entry.')
            continue
        try:
            two_theta = np.array(entry.results[0].two_theta.magnitude)
            intensity = np.array(entry.results[0].intensity.magnitude)
        except Exception as exc:
            print(f'Could not read data from "{name}": {exc}')
            continue

        # Read wavelength from instrument settings; fall back to Cu Kα
        wavelength = 1.5406
        try:
            if (
                entry.xrd_settings is not None
                and entry.xrd_settings.source is not None
                and entry.xrd_settings.source.kalpha_one is not None
            ):
                wavelength = float(entry.xrd_settings.source.kalpha_one.magnitude)
        except Exception:
            print(f'  Could not read wavelength for "{name}", using Cu K\u03b1 default (1.5406 \u00c5).')

        x_corr, y_corr, _ = xrd_background_correction(two_theta, intensity)
        peak_df = xrd_find_and_fit_peaks(x_corr, y_corr)
        samples_dict[name] = {
            'two_theta': x_corr,
            'intensity': y_corr,
            'peaks': peak_df,
            'wavelength': wavelength,
        }
        print(f'Loaded "{name}": {len(peak_df)} peak(s) fitted (\u03bb = {wavelength:.4f} \u00c5).')

    if not samples_dict:
        print('No valid ELNXRayDiffraction entries found in inputs.')
        return

    references_dict = {}
    if reference_contents:
        for phase_name, content in reference_contents.items():
            ref_df = xrd_parse_reference_rtf(content)
            if ref_df is not None:
                references_dict[phase_name] = ref_df
                print(f'Loaded reference "{phase_name}": {len(ref_df)} peaks.')
            else:
                print(f'Warning: could not parse reference "{phase_name}".')

    # Stacked overview
    xrd_plot_stacked(samples_dict, references_dict or None)

    # Per-sample detailed plot
    for sample_name in samples_dict:
        xrd_plot_single_pattern(samples_dict, sample_name, references_dict or None)

    # Crystallographic analysis (requires reference phases)
    if references_dict:
        analysis_results = xrd_match_and_analyze(
            samples_dict, references_dict, tolerance=tolerance, scherrer_k=scherrer_k
        )

        summary_rows = []
        for sample_name, result in analysis_results.items():
            row = {'Sample': sample_name}
            row.update(result['summary'])
            summary_rows.append(row)
        if summary_rows:
            print('\nCrystallographic summary:')
            print(pd.DataFrame(summary_rows).to_string(index=False))

        xrd_plot_tc(analysis_results)
        xrd_plot_crystallite_size(analysis_results)
    else:
        print(
            '\nNo reference phases provided — TC and crystallite-size analysis skipped.'
            '\nUpload ICDD .rtf reference cards with the widget above to enable full analysis.'
        )
