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
    data = np.array([
        [280, 8.20E-02], [290, 5.71E-01], [300, 5.98E-01], [310, 5.14E-01],
        [320, 1.07E+00], [330, 6.35E-01], [340, 1.34E+00], [350, 1.04E+00],
        [360, 1.26E+00], [370, 1.23E+00], [380, 1.21E+00], [390, 1.14E+00],
        [400, 1.51E+00], [410, 1.67E+00], [420, 1.62E+00], [430, 1.61E+00],
        [440, 1.78E+00], [450, 1.75E+00], [460, 1.75E+00], [470, 1.72E+00],
        [480, 1.68E+00], [490, 1.70E+00], [500, 1.67E+00], [510, 1.63E+00],
        [520, 1.64E+00], [530, 1.58E+00], [540, 1.55E+00], [550, 1.53E+00],
        [560, 1.50E+00], [570, 1.46E+00], [580, 1.43E+00], [590, 1.38E+00],
        [600, 1.40E+00], [610, 1.36E+00], [620, 1.37E+00], [630, 1.34E+00],
        [640, 1.31E+00], [650, 1.28E+00], [660, 1.26E+00], [670, 1.24E+00],
        [680, 1.19E+00], [690, 1.18E+00], [700, 1.17E+00], [710, 1.13E+00],
        [720, 1.07E+00], [730, 1.07E+00], [740, 9.51E-01], [750, 1.04E+00],
        [760, 1.03E+00], [770, 9.11E-01], [780, 9.85E-01], [790, 9.28E-01],
        [800, 9.31E-01], [810, 9.15E-01], [820, 9.07E-01], [830, 8.82E-01],
        [840, 8.60E-01], [850, 8.68E-01], [860, 8.50E-01], [870, 7.50E-01],
        [880, 7.53E-01], [890, 7.79E-01], [900, 6.24E-01], [910, 6.52E-01],
        [920, 4.83E-01], [930, 7.09E-01], [940, 6.01E-01], [950, 4.97E-01],
        [960, 4.58E-01], [970, 5.83E-01], [980, 5.18E-01], [990, 5.08E-01],
        [1000, 4.69E-01], [1010, 4.57E-01], [1020, 4.24E-01], [1030, 4.74E-01],
        [1040, 4.32E-01], [1050, 3.73E-01], [1060, 3.53E-01], [1070, 3.79E-01],
        [1080, 2.95E-01], [1090, 2.29E-01], [1100, 2.68E-01], [1110, 3.40E-01],
        [1120, 3.04E-01], [1130, 2.64E-01], [1140, 2.51E-01], [1150, 2.83E-01],
        [1160, 2.61E-01], [1170, 2.07E-01], [1180, 1.26E-01], [1190, 7.47E-02],
        [1200, 1.70E-01],
    ])
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
    h = 6.62607015e-34   # J·s
    c = 2.99792458e8      # m/s

    photon_flux = am_irr * (am_wl * 1e-9) / (h * c)  # photons/m²/s/nm
    jsc_integrand = eqe_interp * photon_flux * q       # A/m²/nm

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
            sigmoid, wl_fit, qe_fit,
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
        entry = entry_input.resolve_input()
        if entry is None:
            continue

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

        results_list.append({
            'Name': name,
            'Jsc (mA/cm²)': round(jsc, 2),
            'Eg sigmoid (eV)': round(Eg_sigmoid, 3) if Eg_sigmoid else None,
            'Eg Keller (eV)': round(Eg_keller, 3) if Eg_keller else None,
        })

        # Plot EQE
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(wl, qe * 100, 'b-', linewidth=1.5)
        ax.set_xlabel('Wavelength (nm)')
        ax.set_ylabel('EQE (%)')
        ax.set_title(f'EQE — {name}')
        ax.grid(True, alpha=0.3)

        # Add secondary x-axis (energy in eV)
        ax2 = ax.secondary_xaxis('top', functions=(
            lambda x: 1239.84193 / np.where(x > 0, x, 1),
            lambda x: 1239.84193 / np.where(x > 0, x, 1),
        ))
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
        entry = entry_input.resolve_input()
        if entry is None:
            continue

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
                all_results.append({
                    'Entry': name,
                    'Measurement': r.measurement_name or '',
                    'Voc (V)': round(float(r.voc), 3) if r.voc is not None else None,
                    'Jsc (mA/cm²)': round(float(r.jsc), 2) if r.jsc is not None else None,
                    'FF': round(float(r.fill_factor), 3) if r.fill_factor is not None else None,
                    'Eff': round(float(r.efficiency), 4) if r.efficiency is not None else None,
                })

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
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
    ]

    for entry_input in inputs:
        entry = entry_input.resolve_input()
        if entry is None:
            continue

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
                    'y1': None, 'y2': None,
                    'X1': None, 'X2': None,
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
